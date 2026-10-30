"""Generate the three nominal trajectory figures using Table 1."""
from pathlib import Path
import csv
from plot_style import setup, save, plt
from rocket_solver import RocketParameters, simulate

ROOT = Path(__file__).resolve().parent

def main():
    setup()
    p = RocketParameters()
    times, states = simulate(p, dt=0.1)
    (ROOT / 'figures').mkdir(exist_ok=True)
    (ROOT / 'data').mkdir(exist_ok=True)
    with (ROOT / 'data/trajectory.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['time_s', 'altitude_m', 'velocity_m_s', 'mass_kg'])
        w.writerows((t, *s) for t, s in zip(times, states))
    for i, name, ylabel in [(0, 'altitude', 'Altitude (m)'),
                            (1, 'velocity', 'Vertical velocity (m/s)'),
                            (2, 'mass', 'Rocket mass (kg)')]:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(times, [s[i] for s in states], linewidth=2)
        ax.axvline(p.burn_time, linestyle='--', linewidth=1,
                   label='Engine burnout')
        ax.set(xlabel='Time (s)', ylabel=ylabel,
               title=f'Rocket {name} versus time')
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        save(fig, name)
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.2))
    for i, (ax, ylabel) in enumerate(zip(axes,
            ['Altitude (km)', 'Vertical velocity (m/s)', 'Rocket mass (kg)'])):
        ax.plot(times, [s[i]/(1000 if i == 0 else 1) for s in states], linewidth=2)
        ax.axvline(p.burn_time, color='0.4', linestyle='--', linewidth=1)
        ax.set(xlabel='Time (s)', ylabel=ylabel)
    fig.tight_layout()
    save(fig, 'nominal_trajectory')
    print(f'Nominal apogee: {states[-1][0]:.9f} m at {times[-1]:.9f} s')

if __name__ == '__main__':
    main()
