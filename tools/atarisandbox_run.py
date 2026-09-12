#!/usr/bin/env python3
import argparse
import json
import os
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

    rc = 127
    try:
        proc = subprocess.run(args.command, env=env, check=False)
        rc = proc.returncode
        return rc
    finally:
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
