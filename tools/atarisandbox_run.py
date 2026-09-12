#!/usr/bin/env python3
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

SCHEMA = "atarisandbox.session/1"
EVENT_SCHEMA = "atarisandbox.event/1"


def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_event(path: Path, event):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")


def main():
    p = argparse.ArgumentParser(description="AtariSandbox M1 analysis runner")
    p.add_argument("--analysis-dir", required=True)
    p.add_argument("--machine-profile", default="st-emutos-ci")
    p.add_argument("--config-fingerprint", default="unspecified")
    p.add_argument("--backend-revision", default="unknown")
    p.add_argument("command", nargs=argparse.REMAINDER)
    args = p.parse_args()

    if not args.command:
        p.error("missing Hatari command after --")
    if args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        p.error("empty Hatari command")

    out = Path(args.analysis_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    session_path = out / "session.json"
    events_path = out / "events.jsonl"

    if session_path.exists() or events_path.exists():
        raise SystemExit("analysis directory already contains AtariSandbox evidence")

    start = time.time_ns()
    base = {
        "schema": SCHEMA,
        "backend": "atarisandbox",
        "backend_revision": args.backend_revision,
        "machine_profile": args.machine_profile,
        "config_fingerprint": args.config_fingerprint,
        "network": "disabled",
        "host_shared_folders": "disabled",
        "started_unix_ns": start,
        "completed": False,
    }
    write_json(session_path, base)
    append_event(events_path, {
        "schema": EVENT_SCHEMA,
        "type": "session.start",
        "unix_ns": start,
        "machine_profile": args.machine_profile,
    })

    env = os.environ.copy()
    env["ATARISANDBOX_ANALYSIS_DIR"] = str(out)
    env["ATARISANDBOX_MACHINE_PROFILE"] = args.machine_profile
    env["ATARISANDBOX_CONFIG_FINGERPRINT"] = args.config_fingerprint

    child = None
    rc = 127
    shutdown_signal = None

    def request_shutdown(signum, _frame):
        nonlocal shutdown_signal
        shutdown_signal = signum
        if child is not None and child.poll() is None:
            child.terminate()

    old_term = signal.signal(signal.SIGTERM, request_shutdown)
    old_int = signal.signal(signal.SIGINT, request_shutdown)
    try:
        child = subprocess.Popen(args.command, env=env)
        try:
            rc = child.wait()
        except KeyboardInterrupt:
            request_shutdown(signal.SIGINT, None)
            try:
                rc = child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                rc = child.wait(timeout=5)

        if shutdown_signal is not None and rc < 0:
            rc = 128 + shutdown_signal
        return rc
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
        signal.signal(signal.SIGTERM, old_term)
        signal.signal(signal.SIGINT, old_int)

        stop = time.time_ns()
        append_event(events_path, {
            "schema": EVENT_SCHEMA,
            "type": "session.stop",
            "unix_ns": stop,
            "exit_code": rc,
        })
        base.update({
            "completed": True,
            "stopped_unix_ns": stop,
            "exit_code": rc,
        })
        write_json(session_path, base)


if __name__ == "__main__":
    sys.exit(main())
