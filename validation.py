"""Independent vacuum solutions test gravity, thrust, mass, and RK4."""
from dataclasses import replace
from pathlib import Path
import csv
import numpy as np
from plot_style import setup, save, plt
from rocket_solver import RocketParameters, simulate

ROOT = Path(__file__).resolve().parent

def powered_exact(p, t):
    q = p.mass_flow_rate
    m = p.initial_mass - q * t
    L = np.log(p.initial_mass / m)
    v = p.thrust / q * L - p.gravity * t
    h = p.thrust / q**2 * (p.initial_mass - m - m*L) - 0.5*p.gravity*t*t
    return h, v, m

def main():
    setup()
    p = RocketParameters()
    vacuum = replace(p, dry_mass=p.initial_mass, burn_time=0.0,
                     thrust=0.0, drag_coefficient=0.0)
    times, states = simulate(vacuum, dt=0.1, initial_velocity=150.0)
    t, s = np.array(times), np.array(states)
    exact_h = 150*t - 0.5*p.gravity*t*t
    exact_v = 150 - p.gravity*t
    err = abs(s[:, 0] - exact_h)
    print('Ballistic maximum altitude error:', max(err), 'm')
    print('Ballistic maximum velocity error:', max(abs(s[:, 1]-exact_v)), 'm/s')
    (ROOT / 'figures').mkdir(exist_ok=True)
    (ROOT / 'data').mkdir(exist_ok=True)
    with (ROOT / 'data/ballistic_validation.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['time_s', 'numerical_h_m', 'exact_h_m', 'height_error_m',
                    'numerical_v_m_s', 'exact_v_m_s'])
        w.writerows(zip(t, s[:, 0], exact_h, err, s[:, 1], exact_v))
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].plot(t, exact_h, 'k-', linewidth=3, label='Analytical (exact)')
    axes[0].plot(t, s[:, 0], 'r--', linewidth=2, label='Numerical (RK4)')
    axes[0].set(xlabel='Time (s)', ylabel='Altitude (m)',
                title='Validation: altitude versus time')
    axes[0].legend()
    positive = err > 0  # Zero error cannot be displayed on a logarithmic axis.
    axes[1].semilogy(t[positive], err[positive])
    axes[1].set(xlabel='Time (s)', ylabel='Absolute altitude error (m)',
                title='Floating-point residual (zero values omitted)')
    for ax in axes:
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    save(fig, 'verification')
    pv = replace(p, drag_coefficient=0.0)
    exact = powered_exact(pv, pv.burn_time)
    with (ROOT / 'data/powered_validation.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['dt_s', 'burnout_height_error_m', 'burnout_velocity_error_m_s'])
        for dt in [0.5, 0.25, 0.125]:
            _, states = simulate(pv, dt=dt, end_time=pv.burn_time,
                                  stop_at_apogee=False)
            errors = np.abs(np.array(states[-1])-exact)
            w.writerow([dt, *errors[:2]])
            print('Powered vacuum:', dt, errors[:2])

if __name__ == '__main__':
    main()
