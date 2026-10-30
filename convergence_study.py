"""Measure apogee convergence before the floating-point error floor."""
from pathlib import Path
import csv
import numpy as np
from plot_style import setup, save, plt
from rocket_solver import RocketParameters, simulate

ROOT = Path(__file__).resolve().parent

def main():
    setup()
    p = RocketParameters()
    _, ref_states = simulate(p, dt=0.0005)
    ref_apogee = ref_states[-1][0]
    _, finer_states = simulate(p, dt=0.00025)
    ref_change = abs(ref_apogee - finer_states[-1][0])
    dt_list = [1.0, 0.5, 0.25, 0.125]
    errors = []
    for dt in dt_list:
        _, states = simulate(p, dt=dt)
        errors.append(abs(states[-1][0] - ref_apogee))
    orders = np.log2(np.array(errors[:-1]) / errors[1:])
    slope, _ = np.polyfit(np.log(dt_list), np.log(errors), 1)
    print('Reference apogee:', ref_apogee, 'm; reference change:', ref_change)
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'figures').mkdir(exist_ok=True)
    with (ROOT / 'data/convergence.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['dt_s', 'apogee_error_m', 'observed_order'])
        for i, (dt, err) in enumerate(zip(dt_list, errors)):
            order = '' if i == 0 else orders[i-1]
            w.writerow([dt, err, order])
            print(dt, err, order)
    print('Fitted slope:', slope)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.loglog(dt_list, errors, 'o-', label=f'Apogee error (fit: {slope:.2f})')
    ax.loglog(dt_list, [errors[-1]*(dt/dt_list[-1])**4 for dt in dt_list],
              'k--', label='Fourth-order reference')
    ax.set(xlabel='Time step (s)', ylabel='Absolute apogee error (m)',
           title='RK4 convergence: Table 1 sounding rocket')
    ax.grid(True, which='both', alpha=0.3)
    ax.legend()
    fig.tight_layout()
    save(fig, 'convergence')

if __name__ == '__main__':
    main()
