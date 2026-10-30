"""Controlled 357-case sensitivity study with refinement and exact vacuum checks.

Fixed: thrust, dry mass, area, drag coefficient, atmosphere and gravity.
Varied: burn time 5:0.5:15 s and propellant fraction 0.4:0.025:0.8.
This is NOT a fixed-specific-impulse motor family.
"""
from dataclasses import replace
from pathlib import Path
import csv
import json
import numpy as np
from rocket_solver import RocketParameters, simulate
from validation import powered_exact
from plot_style import setup, save, plt, COLORS

ROOT = Path(__file__).resolve().parent
BURN_TIMES = np.linspace(5.0, 15.0, 21)
FRACTIONS = np.linspace(.4, .8, 17)
STEPS = (.5, .25, .125)
HEIGHT_TOL = .1  # m; consecutive refinement differences, not exact error bounds
TIME_TOL = .001 # s


def vacuum_apogee(p):
    """Independent exact solution for positive q, g and immediate lift-off."""
    if p.mass_flow_rate <= 0 or p.gravity <= 0 or p.thrust <= p.initial_mass*p.gravity:
        raise ValueError('Exact benchmark requires q>0, g>0, immediate lift-off')
    hb, vb, _ = powered_exact(p, p.burn_time)
    return float(hb + vb*vb/(2*p.gravity)), float(p.burn_time + vb/p.gravity)


def main():
    setup()
    (ROOT / 'data').mkdir(exist_ok=True)
    rows = []
    for phi in FRACTIONS:
        for tb in BURN_TIMES:
            p = RocketParameters(initial_mass=20/(1-float(phi)), burn_time=float(tb))
            h_exact, t_exact = vacuum_apogee(p)
            # Drag can alter burnout velocity; use a generous bound and raise on failure.
            horizon = max(120., 2*t_exact)
            results = [simulate(p, dt=dt, end_time=horizon) for dt in STEPS]
            heights = np.array([s[-1][0] for t, s in results])
            times = np.array([t[-1] for t, s in results])
            dh, dt_change = abs(np.diff(heights)), abs(np.diff(times))
            if max(dh) > HEIGHT_TOL or max(dt_change) > TIME_TOL:
                raise AssertionError(f'Refinement failed for phi={phi}, burn={tb}')
            vt, vs = simulate(replace(p, drag_coefficient=0), dt=STEPS[-1], end_time=horizon)
            if abs(vs[-1][0]-h_exact) > HEIGHT_TOL or abs(vt[-1]-t_exact) > TIME_TOL:
                raise AssertionError('Independent vacuum benchmark failed')
            row = dict(burn_time_s=float(tb), propellant_fraction=float(phi),
                initial_mass_kg=p.initial_mass, impulse_N_s=p.thrust*p.burn_time,
                effective_exhaust_velocity_m_s=p.thrust/p.mass_flow_rate,
                apogee_m=float(heights[-1]), apogee_time_s=float(times[-1]),
                vacuum_exact_apogee_m=h_exact, vacuum_exact_time_s=t_exact,
                drag_penalty_m=float(h_exact-heights[-1]),
                drag_penalty_percent=float(100*(h_exact-heights[-1])/h_exact),
                coarse_height_change_m=float(dh[0]), fine_height_change_m=float(dh[1]),
                coarse_time_change_s=float(dt_change[0]), fine_time_change_s=float(dt_change[1]),
                vacuum_height_error_m=float(abs(vs[-1][0]-h_exact)),
                vacuum_time_error_s=float(abs(vt[-1]-t_exact)))
            rows.append(row)
    with (ROOT / 'data/engineering_results.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    shape = (len(FRACTIONS), len(BURN_TIMES))
    heights = np.array([r['apogee_m'] for r in rows]).reshape(shape)
    penalty = np.array([r['drag_penalty_percent'] for r in rows]).reshape(shape)
    phi_i, tb_i = 8, 10  # phi=.6, burn=10 s, both interior nodes
    nominal = rows[phi_i*len(BURN_TIMES)+tb_i]
    monotone_t = bool(np.all(np.diff(heights, axis=1) > 0))
    monotone_phi = bool(np.all(np.diff(heights, axis=0) < 0))
    stats = dict(grid_cases=len(rows), dt_s=STEPS[-1], nominal=nominal,
        maximum_apogee_case=max(rows, key=lambda r:r['apogee_m']),
        minimum_apogee_case=min(rows, key=lambda r:r['apogee_m']),
        increasing_with_burn_time_at_all_sampled_fractions=monotone_t,
        decreasing_with_fraction_at_all_sampled_burn_times=monotone_phi,
        drag_penalty_increases_with_burn_time=bool(np.all(np.diff(penalty, axis=1)>0)),
        drag_penalty_decreases_with_fraction=bool(np.all(np.diff(penalty, axis=0)<0)),
        minimum_adjacent_burn_height_gain_m=float(np.min(np.diff(heights, axis=1))),
        minimum_adjacent_fraction_height_loss_m=float(np.min(-np.diff(heights, axis=0))),
        max_fine_height_change_m=max(r['fine_height_change_m'] for r in rows),
        max_fine_time_change_s=max(r['fine_time_change_s'] for r in rows),
        max_coarse_height_change_m=max(r['coarse_height_change_m'] for r in rows),
        max_coarse_time_change_s=max(r['coarse_time_change_s'] for r in rows),
        max_vacuum_height_error_m=max(r['vacuum_height_error_m'] for r in rows),
        max_vacuum_time_error_s=max(r['vacuum_time_error_s'] for r in rows),
        minimum_drag_penalty_percent=float(penalty.min()),
        maximum_drag_penalty_percent=float(penalty.max()),
        nominal_dh_dtb_m_s=float((heights[phi_i,tb_i+1]-heights[phi_i,tb_i-1])/1.0),
        nominal_dh_dphi_m=float((heights[phi_i+1,tb_i]-heights[phi_i-1,tb_i])/.05))
    if not (monotone_t and monotone_phi and
            stats['drag_penalty_increases_with_burn_time'] and
            stats['drag_penalty_decreases_with_fraction']):
        raise AssertionError('Observed trends changed; review report interpretation')
    (ROOT / 'data/engineering_summary.json').write_text(json.dumps(stats, indent=2)+'\n')
    with (ROOT / 'data/results_table.tex').open('w') as f:
        f.write('% Generated by engineering_results.py; do not edit values.\n')
        for r in rows:
            if any(np.isclose(r['propellant_fraction'], x) for x in [.4,.6,.8]) and r['burn_time_s'] in [5.,10.,15.]:
                f.write(f"{r['burn_time_s']:.0f} & {r['propellant_fraction']:.2f} & {r['apogee_m']:.2f} & {r['apogee_time_s']:.3f} & {r['vacuum_exact_apogee_m']:.2f} & {r['drag_penalty_percent']:.2f}" + r' \\' + '\n')
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9))
    for i, style in zip([0,8,16], ['-', '--', ':']):
        axes[0].plot(BURN_TIMES, heights[i]/1000, style, linewidth=2,
                     label=f'Propellant fraction {FRACTIONS[i]:.1f}')
    for i, style in zip([0,10,20], ['-', '--', ':']):
        axes[1].plot(FRACTIONS, heights[:,i]/1000, style, linewidth=2,
                     label=f'Burn duration {BURN_TIMES[i]:.0f} s')
    axes[0].set(xlabel='Burn duration (s)', ylabel='Apogee altitude (km)', title='(a) Fixed propellant fraction')
    axes[1].set(xlabel='Propellant mass fraction (-)', ylabel='Apogee altitude (km)', title='(b) Fixed burn duration')
    for ax in axes: ax.legend(loc='best')
    fig.tight_layout()
    save(fig, 'parameter_slices')
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, z, label, cmap in zip(axes, [heights/1000,penalty],
            ['Apogee altitude (km)', 'Apogee reduction from vacuum (%)'], ['viridis','cividis']):
        mesh = ax.pcolormesh(BURN_TIMES, FRACTIONS, z, shading='nearest', cmap=cmap, rasterized=True)
        ax.plot(10,.6,'wo', markeredgecolor='black', markersize=6, label='Nominal case')
        ax.set(xlabel='Burn duration (s)', ylabel='Propellant mass fraction (-)',
               xlim=(5,15), ylim=(.4,.8))
        ax.grid(False)
        fig.colorbar(mesh, ax=ax, label=label)
        ax.legend(loc='lower left')
    fig.tight_layout()
    save(fig, 'parameter_maps')
    fig, axes = plt.subplots(1,2,figsize=(10,3.9))
    exact = np.array([r['vacuum_exact_apogee_m'] for r in rows]).reshape(shape)
    axes[0].plot(BURN_TIMES,exact[8]/1000,'--',label='No drag: exact solution',linewidth=2)
    axes[0].plot(BURN_TIMES,heights[8]/1000,'-',label='Atmosphere: RK4',linewidth=2)
    axes[0].set(xlabel='Burn duration (s)',ylabel='Apogee altitude (km)',title='(a) Nominal fraction = 0.6')
    for i,style in zip([0,8,16],['-','--',':']):
        axes[1].plot(BURN_TIMES,penalty[i],style,linewidth=2,label=f'Propellant fraction {FRACTIONS[i]:.1f}')
    axes[1].set(xlabel='Burn duration (s)',ylabel='Apogee reduction from vacuum (%)',title='(b) Relative drag penalty')
    for ax in axes: ax.legend()
    fig.tight_layout()
    save(fig, 'drag_comparison')
    print(json.dumps(stats,indent=2))

if __name__ == '__main__':
    main()
