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
    p = argparse.ArgumentParser(description="AtariSandbox M1.1 real Hatari/EmuTOS runtime qualifier")
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

    cmd = [
        str(hatari),
        "--machine", "st",
        "--cpu-level", "0",
        "--memsize", "1",
        "--tos", str(rom),
        "--fast-boot", "on",
        "--sound", "off",
        "--confirm-quit", "off",
        "--grab", "off",
        "--statusbar", "off",
        "--log-file", str(log_path),
        "--trace-file", str(analysis / "hatari-trace.log"),
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

    os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=5)

    session = json.loads((analysis / "session.json").read_text(encoding="utf-8"))
    if session.get("schema") != "atarisandbox.session/1":
        raise SystemExit("unexpected session schema")
    if session.get("machine_profile") != "st-emutos-ci":
        raise SystemExit("unexpected machine profile")
    events = [json.loads(line) for line in (analysis / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if [e.get("type") for e in events[:1]] != ["session.start"]:
        raise SystemExit("missing session.start")
    if not any(e.get("type") == "session.stop" for e in events):
        raise SystemExit("missing session.stop")

    summary = {
        "schema": "atarisandbox.m1_1.qualification/1",
        "backend_revision": args.backend_revision,
        "machine_profile": "st-emutos-ci",
        "rom_sha256": rom_sha,
        "runtime_seconds": args.runtime_seconds,
        "network": "disabled",
        "host_shared_folders": "disabled",
        "result": "PASS",
    }
    (analysis / "qualification.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("M1.1 PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
