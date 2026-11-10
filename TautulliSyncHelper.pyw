"""Windows launcher for the PlexAniSync Tautulli helper.

Tautulli runs a notification script with the ``pythonw`` interpreter it finds
on PATH. That interpreter does not have PlexAniSync's dependencies installed,
so this launcher starts the real helper (``TautulliSyncHelper.py``) inside the
project virtual environment instead.

The output of the helper is forwarded to Tautulli (so it shows up in the
Tautulli log) and mirrored to ``logs/tautulli_sync.log`` so the sync can be
inspected without enabling Tautulli's verbose logging.

Do not rename this file: Tautulli picks the interpreter based on the file
extension and ``.pyw`` is the one that runs without a console window popping up.
"""

import os
import subprocess
import sys
import threading
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(BASE_DIR, ".venv", "Scripts")
HELPER = os.path.join(BASE_DIR, "TautulliSyncHelper.py")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.ini")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "tautulli_sync.log")


def find_interpreter():
    """Return the virtualenv interpreter, preferring the windowless pythonw."""
    pythonw = os.path.join(VENV_DIR, "pythonw.exe")
    python = os.path.join(VENV_DIR, "python.exe")
    if os.path.isfile(pythonw):
        return pythonw
    if os.path.isfile(python):
        return python
    return None


def write_log(log_file, text):
    """Write a line to the log file and to stdout."""
    log_file.write(text)
    log_file.flush()
    if sys.stdout is not None:
        sys.stdout.write(text)
        sys.stdout.flush()


def forward_output(source, sink, log_file, lock):
    """Copy one output stream of the helper to the log file and to Tautulli."""
    for line in iter(source.readline, b""):
        text = line.decode("utf-8", "replace")
        with lock:
            log_file.write(text)
            log_file.flush()
            if sink is not None:
                sink.write(text)
                sink.flush()


def main():
    show_name = " ".join(sys.argv[1:])

    interpreter = find_interpreter()
    if interpreter is None:
        message = (
            "PlexAniSync launcher: no virtualenv interpreter found in {}. "
            "Run 'python -m venv .venv' and install requirements.txt first."
        ).format(VENV_DIR)
        print(message)
        return 1

    # Tautulli exports these and they break the virtualenv interpreter.
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    # Point the helper at the settings file so it does not depend on the
    # working directory it happens to be started in.
    env["SETTINGS_FILE"] = SETTINGS_FILE

    command = [interpreter, HELPER] + sys.argv[1:]

    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        lock = threading.Lock()
        header = "\n=== PlexAniSync run {} | show: {} ===\n".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), show_name
        )
        with lock:
            write_log(log_file, header)

        process = subprocess.Popen(
            command,
            cwd=BASE_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        threads = [
            threading.Thread(
                target=forward_output, args=(process.stdout, sys.stdout, log_file, lock)
            ),
            threading.Thread(
                target=forward_output, args=(process.stderr, sys.stderr, log_file, lock)
            ),
        ]
        for thread in threads:
            thread.start()

        returncode = process.wait()
        for thread in threads:
            thread.join()

        with lock:
            write_log(log_file, "=== PlexAniSync finished with exit code {} ===\n".format(returncode))

    return returncode


if __name__ == "__main__":
    sys.exit(main())
