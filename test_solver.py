"""Run with python -m unittest -v. No external ODE solver is used."""
import unittest
from dataclasses import replace
from math import exp
from unittest.mock import patch
import rocket_solver as rs
from validation import powered_exact
from engineering_results import vacuum_apogee

class SolverTests(unittest.TestCase):
    def test_ballistic_solution(self):
        p = rs.RocketParameters(initial_mass=50, dry_mass=50,
                               thrust=0, burn_time=0, drag_coefficient=0)
        times, states = rs.simulate(p, dt=.1, initial_velocity=150)
        for t, (h, v, m) in zip(times, states):
            self.assertAlmostEqual(h, 150*t-.5*p.gravity*t*t, delta=1e-8)
            self.assertAlmostEqual(v, 150-p.gravity*t, delta=1e-9)
            self.assertEqual(m, 50)
        self.assertAlmostEqual(times[-1], 150/p.gravity, delta=1e-9)

    def test_powered_exact_and_order(self):
        p = rs.RocketParameters(drag_coefficient=0)
        exact = powered_exact(p, p.burn_time)
        errors = []
        for dt in [.5, .25, .125]:
            _, states = rs.simulate(p, dt=dt, end_time=p.burn_time,
                                    stop_at_apogee=False)
            errors.append(abs(states[-1][0]-exact[0]))
        for a, b in zip(errors, errors[1:]):
            self.assertTrue(15 < a/b < 17)

    def test_non_aligned_burnout(self):
        p = rs.RocketParameters()
        t, s = rs.simulate(p, dt=.3)
        ib = t.index(p.burn_time)
        self.assertTrue(all(x[2] == p.dry_mass for x in s[ib:]))
        for ti, si in zip(t[:ib], s[:ib]):
            self.assertAlmostEqual(si[2], p.initial_mass-p.mass_flow_rate*ti,
                                   delta=1e-10)
        _, fine = rs.simulate(p, dt=.15)
        self.assertLess(abs(s[-1][0]-fine[-1][0]), .001)

    def test_drag_direction_and_density(self):
        p = rs.RocketParameters(thrust=0, initial_mass=20, dry_mass=20)
        a_up = rs.derivatives((0, 100, 20), p, False)[1]
        a_down = rs.derivatives((0, -100, 20), p, False)[1]
        self.assertAlmostEqual(a_up, -14.1373125)
        self.assertLess(a_up, -p.gravity)
        self.assertGreater(a_down, -p.gravity)
        a_high = rs.derivatives((p.scale_height, 100, 20), p, False)[1]
        self.assertAlmostEqual((a_high+p.gravity)/(a_up+p.gravity), exp(-1))

    def test_failure_is_not_reported_as_apogee(self):
        with self.assertRaises(RuntimeError):
            rs.simulate(rs.RocketParameters(), end_time=1)
        with self.assertRaises(ValueError):
            rs.simulate(rs.RocketParameters(thrust=100))

    def test_powered_then_coast_vacuum_apogee(self):
        for phi, tb in [(.4, 15.), (.6, 10.), (.8, 5.)]:
            p = rs.RocketParameters(initial_mass=20/(1-phi), burn_time=tb,
                                    drag_coefficient=0.)
            eh, et = vacuum_apogee(p)
            t, s = rs.simulate(p, dt=.125, end_time=2*et)
            self.assertAlmostEqual(s[-1][0], eh, delta=.001)
            self.assertAlmostEqual(t[-1], et, delta=1e-5)
            self.assertAlmostEqual(s[-1][1], 0, delta=1e-9)

    def test_cost_count(self):
        original = rs.derivatives
        with patch.object(rs, 'derivatives', wraps=original) as counted:
            t, _ = rs.simulate(rs.RocketParameters(), dt=1)
        self.assertEqual(counted.call_count, 4*(len(t)-1)+184)
        self.assertEqual(counted.call_count, 316)

if __name__ == '__main__':
    unittest.main()
