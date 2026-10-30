"""Reproduce the 25 step-size comparisons and nominal diagnostics."""
from pathlib import Path
import csv
import json
import numpy as np
from rocket_solver import RocketParameters, simulate

ROOT = Path(__file__).resolve().parent

def main():
    p = RocketParameters()
    t0, s0 = simulate(p, dt=0.0005)
    t1, s1 = simulate(p, dt=0.00025)
    ref_h, ref_t = s0[-1][0], t0[-1]
    rows = []
    for hp in [0.1, 0.25, 0.5, 1.0, 2.0]:
        for hc in [0.1, 0.25, 0.5, 1.0, 2.0]:
            t, s = simulate(p, dt=hp, dt_coast=hc)
            eh, et = abs(s[-1][0]-ref_h), abs(t[-1]-ref_t)
            n = len(t)-1
            rows.append([hp, hc, eh, et, n, 4*n+4*46,
                         eh <= 0.1 and et <= 0.001])
    (ROOT / 'data').mkdir(exist_ok=True)
    with (ROOT / 'data/parameter_evaluation.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['powered_dt_s', 'coast_dt_s', 'height_error_m',
                    'time_error_s', 'main_steps', 'rhs_evaluations', 'passes'])
        w.writerows(rows)
    best = min((r for r in rows if r[-1]), key=lambda r: r[5])
    print('Reference:', ref_h, ref_t, '; best passing row:', best)
    h, v, m = np.array(s0).T
    t = np.array(t0)
    density = p.sea_level_density * np.exp(-h/p.scale_height)
    D = 0.5*density*p.drag_coefficient*p.area*v*abs(v)
    burn = t < p.burn_time
    thrust = np.where(burn, p.thrust, 0.0)
    q = np.where(burn, p.mass_flow_rate, 0.0)
    a = (thrust-D)/m-p.gravity
    jerk = q*(thrust-D)/m**2-density*p.drag_coefficient*p.area/m*v*a+D*v/(m*p.scale_height)
    beta = density*p.drag_coefficient*p.area*abs(v)/m
    alpha = D/(m*p.scale_height)
    lam_minus = (-beta-np.sqrt(beta**2+4*alpha))/2
    ib = np.argmin(abs(t-p.burn_time))
    z = float(min(lam_minus))
    diagnostics = dict(reference_h_m=ref_h, reference_t_s=ref_t,
        reference_h_change_m=abs(s1[-1][0]-ref_h),
        reference_t_change_s=abs(t1[-1]-ref_t),
        max_powered_jerk_m_s3=float(max(abs(jerk[burn]))),
        coast_initial_jerk_m_s3=float(jerk[ib]),
        burnout_acceleration_before_m_s2=float(a[ib]+p.thrust/p.dry_mass),
        burnout_acceleration_after_m_s2=float(a[ib]),
        most_negative_eigenvalue_s_inv=z,
        RK4_amplification_at_dt_1=1+z+z*z/2+z**3/6+z**4/24)
    (ROOT / 'data/diagnostics.json').write_text(json.dumps(diagnostics, indent=2)+'\n')
    print(json.dumps(diagnostics, indent=2))

if __name__ == '__main__':
    main()
