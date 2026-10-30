from dataclasses import dataclass
from math import exp, isfinite
from typing import Tuple

State = Tuple[float, float, float] 

@dataclass(frozen=True)
class RocketParameters:
    initial_mass: float = 50.0       # kg, including 30 kg propellant
    dry_mass: float = 20.0           # kg, after burnout
    burn_time: float = 10.0          # s
    thrust: float = 2500.0           # N during burn
    drag_coefficient: float = 0.45    # assumed constant
    area: float = 0.0314             # m^2, approximately 20 cm diameter
    sea_level_density: float = 1.225 # kg/m^3
    scale_height: float = 8500.0     # m
    gravity: float = 9.81            # m/s^2

    def __post_init__(self):
        if not all(isfinite(x) for x in vars(self).values()):
            raise ValueError("Parameters must be finite")
        if not (0 < self.dry_mass <=  self.initial_mass):
            raise ValueError("Require 0 < dry_mass <= initial_mass")
        if self.burn_time < 0 or (self.burn_time == 0 and
                                    self.initial_mass != self.dry_mass):
            raise ValueError("Positive propellant mass requires burn_time > 0")
        if (self.thrust < 0 or self.drag_coefficient < 0 or self.area < 0
                or self.sea_level_density < 0 or self.gravity < 0
                or self.scale_height <= 0):
            raise ValueError("Check the physical parameter signs")

    @property
    def mass_flow_rate(self) -> float:
        if self.burn_time == 0:
            return 0.0
        return (self.initial_mass - self.dry_mass) / self.burn_time


def derivatives(state: State, p: RocketParameters, burning: bool) -> State:
    height, velocity, mass = state
    if mass <= 0:
        raise ValueError("Rocket mass must remain positive")

    density = p.sea_level_density * exp(-height / p.scale_height)
    drag = 0.5 * density * p.drag_coefficient * p.area * velocity * abs(velocity)
    thrust = p.thrust if burning else 0.0
    mass_derivative = -p.mass_flow_rate if burning else 0.0

    height_derivative = velocity
    velocity_derivative = (thrust - drag) / mass - p.gravity
    return height_derivative, velocity_derivative, mass_derivative

def add_scaled(state: State, slope: State, factor: float) -> State:
    return tuple(x + factor * k for x, k in zip(state, slope))

def rk4_step(state: State, dt: float, p: RocketParameters,
            burning: bool) -> State:
    k1 = derivatives(state, p, burning)
    k2 = derivatives(add_scaled(state, k1, dt / 2), p, burning)
    k3 = derivatives(add_scaled(state, k2, dt / 2), p, burning)
    k4 = derivatives(add_scaled(state, k3, dt), p, burning)
    return tuple(
        x + dt * (a + 2*b + 2*c + d) / 6
        for x, a, b, c, d in zip(state, k1, k2, k3, k4)
    )

def apogee_within_step(state: State, step: float,
                        p: RocketParameters, burning: bool):
    low, high = 0.0, step
    for _ in range(45):
        middle = 0.5 * (low + high)
        trial = rk4_step(state, middle, p, burning)
        if trial[1] > 0:
            low = middle
        else:
            high = middle
    offset = 0.5 * (low + high)
    return offset, rk4_step(state, offset, p, burning)

def simulate(p: RocketParameters, dt: float = 0.1, end_time: float = 120.0,
            initial_height: float = 0.0, initial_velocity: float = 0.0,
            stop_at_apogee: bool = True, dt_coast: float = None):
    """Stop at the first upward-to-downward crossing; raise if not reached.

    A launch from rest requires positive initial upward acceleration.
    Ground contact, delayed lift-off, and relaunch are outside this model.
    Set stop_at_apogee=False only for fixed-time verification studies.
    """
    if dt_coast is None:
        dt_coast = dt
    if not all(isfinite(x) for x in
               (dt, dt_coast, end_time, initial_height, initial_velocity)):
        raise ValueError("Numerical inputs must be finite")
    if dt_coast <= 0:
        raise ValueError("dt_coast must be positive")
    if dt <= 0 or end_time <= 0:
        raise ValueError("dt and end_time must be positive")

    t = 0.0
    state: State = (initial_height, initial_velocity, p.initial_mass)
    if stop_at_apogee and (initial_velocity < 0 or
            (initial_velocity == 0 and
             (p.thrust if p.burn_time > 0 else 0.0) / p.initial_mass <= p.gravity)):
        raise ValueError("Apogee run requires upward flight or immediate lift-off")
    times = [t]
    states = [state]

    while t < end_time:
        burning = t < p.burn_time
        step = min(dt if burning else dt_coast, end_time - t)

        if burning:
            step = min(step, p.burn_time - t)

        next_t = t + step
        if burning and abs(next_t - p.burn_time) <= 1e-12:
            next_t = p.burn_time
            step = next_t - t
        if step <= 0:
            raise ArithmeticError("Time step cannot advance time")

        next_state = rk4_step(state, step, p, burning)
        if not all(isfinite(x) for x in next_state):
            raise ArithmeticError("Nonfinite state; reduce the time step")
        if burning and next_t == p.burn_time:
            next_state = (next_state[0], next_state[1], p.dry_mass)

        if stop_at_apogee and state[1] > 0 and next_state[1] <= 0:
            offset, peak_state = apogee_within_step(state, step, p, burning)
            times.append(t + offset)
            states.append(peak_state)
            return times, states

        t, state = next_t, next_state
        times.append(t)
        states.append(state)

    if stop_at_apogee:
        raise RuntimeError("Apogee not reached; increase end_time")
    return times, states
