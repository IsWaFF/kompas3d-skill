#!/usr/bin/env python3
"""Run a Python script against the running KOMPAS-3D.

    python3 run.py script.py [args...]     Linux
    py run.py script.py [args...]          Windows (64-bit Python)

The script can `import ksapi`, `from constants import constants as c` and `import ks`.
Linux: the script runs inside the distrobox that holds KOMPAS; KOMPAS_BOX=none runs it on
the host instead (KOMPAS installed natively). Windows: it runs with the Python that started run.py.
Env: T (timeout in seconds, default 120), KOMPAS_DIR (install dir), KOMPAS_BOX (Linux, default kompas-box).
"""
import os
import subprocess
import sys
import threading

WINDOWS = os.name == 'nt'
DEFAULT_DIR = r'C:\Program Files\ASCON\KOMPAS-3D v25' if WINDOWS else '/opt/ascon/kompas3d-v25'
SCRIPTS = os.path.dirname(os.path.abspath(__file__))


def run(cmd, cwd=None, env=None, timeout=None):
    """Run cmd, stream its output without the box's apport noise, and exit with its exit code."""
    p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding='utf-8', errors='replace')
    timed_out = threading.Event()

    def kill():
        timed_out.set()
        p.kill()

    timer = threading.Timer(timeout, kill) if timeout else None
    if timer:
        timer.start()
    for line in p.stdout:
        if 'apport' in line.lower():
            continue
        try:
            sys.stdout.write(line)
            sys.stdout.flush()
        except BrokenPipeError:
            # e.g. `run.py ... | head`: keep draining, or the script dies mid-way (before it saves)
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
    code = p.wait()
    if timer:
        timer.cancel()
    if timed_out.is_set() or code == 124:       # 124: `timeout` inside the box
        sys.exit('run.py: timed out (raise the limit with T=seconds); a modal dialog in KOMPAS may be waiting')
    sys.exit(code)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.stdout.reconfigure(errors='replace')    # Cyrillic output on a non-UTF-8 Windows console
    script, args = os.path.abspath(sys.argv[1]), sys.argv[2:]
    bin_dir = os.path.abspath(os.path.join(os.environ.get('KOMPAS_DIR', DEFAULT_DIR), 'Bin'))
    timeout = os.environ.get('T', '120')
    pythonpath = os.pathsep.join([bin_dir, SCRIPTS])
    box = 'none' if WINDOWS else os.environ.get('KOMPAS_BOX', 'kompas-box')
    if box != 'none':
        # The timeout runs inside the box: killing `distrobox enter` would leave the script running.
        run(['distrobox', 'enter', box, '--', 'env', f'PYTHONPATH={pythonpath}', 'PYTHONIOENCODING=utf-8',
             'bash', '-c', 'cd "$1" && shift && exec timeout "$0" python3 "$@"', timeout, bin_dir, script, *args])
    else:
        env = dict(os.environ, PYTHONPATH=pythonpath, PYTHONIOENCODING='utf-8')
        run([sys.executable, script, *args], cwd=bin_dir, env=env, timeout=float(timeout))


if __name__ == '__main__':
    main()
