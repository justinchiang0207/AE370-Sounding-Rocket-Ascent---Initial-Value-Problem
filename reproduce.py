"""Run all checks and experiments; optionally compile the report.

Usage: python reproduce.py [--skip-latex]
Outputs are written relative to this file, regardless of the working directory.
"""
from pathlib import Path
import argparse
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-latex', action='store_true')
    args = parser.parse_args()
    (ROOT / 'data').mkdir(exist_ok=True)
    environment = {'python': sys.version, 'platform': platform.platform(),
                   'packages': {x: importlib.metadata.version(x)
                                for x in ['numpy', 'matplotlib']}}
    (ROOT / 'data/environment.json').write_text(json.dumps(environment, indent=2)+'\n')
    with (ROOT / 'data/execution_log.txt').open('w') as log:
        def run(*command):
            print('Running:', ' '.join(command), flush=True)
            completed = subprocess.run(command, cwd=ROOT, text=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log.write('$ ' + ' '.join(command) + '\n' + completed.stdout + '\n')
            log.flush()
            print(completed.stdout, end='', flush=True)
            completed.check_returncode()
        run(sys.executable, '-m', 'unittest', '-v', 'test_solver')
        for script in ['plot_trajectory.py', 'convergence_study.py', 'validation.py',
                       'parameter_evaluation.py', 'engineering_results.py']:
            run(sys.executable, script)
        if not args.skip_latex:
            if shutil.which('latexmk'):
                run('latexmk', '-pdf', '-interaction=nonstopmode', '-halt-on-error', 'main.tex')
            elif shutil.which('pdflatex'):
                for _ in range(2):
                    run('pdflatex', '-interaction=nonstopmode', '-halt-on-error', 'main.tex')
            else:
                print('LaTeX unavailable: figures/data regenerated; compile main.tex in Overleaf.')


if __name__ == '__main__':
    main()
