"""Run the documented verification and reproduction sequence from any directory."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    commands = [
        [sys.executable, '-m', 'eval.model_assertions'],
        [sys.executable, '-m', 'unittest', 'eval.test_regressions', '-v'],
        [sys.executable, '-m', 'eval.test_qrisk3_source'],
        ['node', 'metatool/test_models.js'],
        ['node', 'metatool/test_ui.js'],
        [sys.executable, '-m', 'eval.run_eval'],
        [sys.executable, '-m', 'eval.supplement'],
        ['node', 'metatool/parity_check.js'],
        [sys.executable, '-m', 'eval.extended_parity'],
        [sys.executable, '-m', 'eval.robustness'],
        [sys.executable, '-m', 'eval.build_submission_figures'],
    ]
    for command in commands:
        print('Running:', ' '.join(command), flush=True)
        subprocess.run(command, cwd=ROOT, check=True)
    print('All verification and reproduction steps passed.')

if __name__ == '__main__':
    main()
