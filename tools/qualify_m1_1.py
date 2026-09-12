#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(description="AtariSandbox M1.1/M2 real Hatari/EmuTOS runtime qualifier")
    p.add_argument("--analysis-dir", required=True)
    p.add_argument("--hatari", required=True)
    p.add_argument("--rom", required=True)
    p.add_argument("--backend-revision", required=True)
    p.add_argument("--runtime-seconds", type=int, default=8)
    args = p.parse_args()

    analysis = Path(args.analysis_dir).resolve()
    analysis.mkdir(parents=True, exist_ok=True)
    rom = Path(args.rom).resolve()
    hatari = Path(args.hatari).resolve()
    if not rom.is_file() or rom.stat().st_size < 128 * 1024:
        raise SystemExit("invalid EmuTOS ROM")
    if not hatari.is_file():
        raise SystemExit("Hatari binary missing")

    rom_sha = sha256_file(rom)
    (analysis / "emutos.sha256").write_text(f"{rom_sha}  {rom.name}\n", encoding="utf-8")
    log_path = analysis / "hatari.log"
    trace_path = analysis / "hatari-trace.log"

    cmd = [
        str(hatari),
        "--machine", "st",
        "--cpulevel", "0",
        "--memsize", "1",
        "--tos", str(rom),
        "--fast-boot", "on",
        "--sound", "off",
        "--confirm-quit", "off",
        "--window",
        "--statusbar", "off",
        "--log-file", str(log_path),
        "--trace-file", str(trace_path),
        "--trace", "cpu_exception",
    ]

    runner = Path(__file__).with_name("atarisandbox_run.py")
    lifecycle_cmd = [
        os.environ.get("PYTHON", "python3"), str(runner),
        "--analysis-dir", str(analysis),
        "--machine-profile", "st-emutos-ci",
        "--config-fingerprint", f"emutos-sha256:{rom_sha}",
        "--backend-revision", args.backend_revision,
        "--",
    ] + cmd

    env = os.environ.copy()
    proc = subprocess.Popen(lifecycle_cmd, env=env, start_new_session=True)
    time.sleep(args.runtime_seconds)
    if proc.poll() is not None:
        raise SystemExit(f"Hatari exited too early with rc={proc.returncode}")

    # Stop only the runner. Its SIGTERM handler owns child shutdown and must be
    # allowed to write session.stop and the completed session record.
    proc.terminate()
    try:
        proc.wait(timeout=7)
    except subprocess.TimeoutExpired:
        # Last resort for a wedged lifecycle. At this point evidence should not
        # be considered qualified because the orderly stop contract failed.
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=5)
        raise SystemExit("AtariSandbox runner did not terminate cleanly")

    session = json.loads((analysis / "session.json").read_text(encoding="utf-8"))
    if session.get("schema") != "atarisandbox.session/1":
        raise SystemExit("unexpected session schema")
    if session.get("machine_profile") != "st-emutos-ci":
        raise SystemExit("unexpected machine profile")
    if session.get("completed") is not True:
        raise SystemExit("session did not complete cleanly")

    converter = Path(__file__).with_name("atarisandbox_trace_to_events.py")
    subprocess.run(
        [
            os.environ.get("PYTHON", "python3"),
            str(converter),
            "--trace", str(trace_path),
            "--events", str(analysis / "events.jsonl"),
            "--require-events",
        ],
        check=True,
    )

    events = [
        json.loads(line)
        for line in (analysis / "events.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if [e.get("type") for e in events[:1]] != ["session.start"]:
        raise SystemExit("missing session.start")
    if not any(e.get("type") == "session.stop" for e in events):
        raise SystemExit("missing session.stop")

    cpu_events = [e for e in events if e.get("type") == "cpu.exception"]
    if not cpu_events:
        raise SystemExit("missing structured cpu.exception evidence")
    for event in cpu_events:
        for key in ("exception_nr", "pc", "instruction_pc", "vector_target", "sr"):
            if not isinstance(event.get(key), int):
                raise SystemExit(f"invalid cpu.exception field: {key}")

    summary = {
        "schema": "atarisandbox.m2.qualification/1",
        "backend_revision": args.backend_revision,
        "machine_profile": "st-emutos-ci",
        "rom_sha256": rom_sha,
        "runtime_seconds": args.runtime_seconds,
        "network": "disabled",
        "host_shared_folders": "disabled",
        "cpu_exception_events": len(cpu_events),
        "result": "PASS",
    }
    (analysis / "qualification.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"M2 PASS: {len(cpu_events)} structured cpu.exception events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
