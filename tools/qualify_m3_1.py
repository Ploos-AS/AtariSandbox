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


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    p = argparse.ArgumentParser(description="AtariSandbox M3.1 real Hatari/EmuTOS OS API runtime qualifier")
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
    trace_path = analysis / "hatari-os-trace.log"

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
        "--trace", "gemdos,bios,xbios",
    ]

    runner = Path(__file__).with_name("atarisandbox_run.py")
    lifecycle_cmd = [
        os.environ.get("PYTHON", "python3"), str(runner),
        "--analysis-dir", str(analysis),
        "--machine-profile", "st-emutos-ci",
        "--config-fingerprint", f"emutos-sha256:{rom_sha};trace=gemdos,bios,xbios",
        "--backend-revision", args.backend_revision,
        "--",
    ] + cmd

    proc = subprocess.Popen(lifecycle_cmd, env=os.environ.copy(), start_new_session=True)
    time.sleep(args.runtime_seconds)
    if proc.poll() is not None:
        raise SystemExit(f"Hatari exited too early with rc={proc.returncode}")

    proc.terminate()
    try:
        proc.wait(timeout=7)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=5)
        raise SystemExit("AtariSandbox runner did not terminate cleanly")

    session = json.loads((analysis / "session.json").read_text(encoding="utf-8"))
    if session.get("schema") != "atarisandbox.session/1" or session.get("completed") is not True:
        raise SystemExit("invalid or incomplete session evidence")

    lifecycle = read_jsonl(analysis / "events.jsonl")
    if len([e for e in lifecycle if e.get("type") == "session.start"]) != 1:
        raise SystemExit("missing session.start")
    if len([e for e in lifecycle if e.get("type") == "session.stop"]) != 1:
        raise SystemExit("missing session.stop")

    converter = Path(__file__).with_name("atarisandbox_os_trace_events.py")
    os_events_path = analysis / "os-events.jsonl"
    os_events_path.write_text("", encoding="utf-8")
    subprocess.run(
        [
            os.environ.get("PYTHON", "python3"), str(converter),
            "--trace", str(trace_path),
            "--events", str(os_events_path),
            "--max-trace-bytes", str(16 * 1024 * 1024),
            "--max-events", "4096",
            "--require-gemdos",
            "--require-bios",
            "--require-xbios",
        ],
        check=True,
    )

    os_events = read_jsonl(os_events_path)
    counts = {api: len([e for e in os_events if e.get("api") == api]) for api in ("gemdos", "bios", "xbios")}
    if not all(counts.values()):
        raise SystemExit(f"missing required OS API evidence: {counts}")

    merged = []
    for event in lifecycle:
        if event.get("type") == "session.stop":
            merged.extend(os_events)
        merged.append(event)
    (analysis / "events.jsonl").write_text(
        "".join(json.dumps(e, sort_keys=True) + "\n" for e in merged), encoding="utf-8"
    )

    summary = {
        "schema": "atarisandbox.m3_1.qualification/1",
        "backend_revision": args.backend_revision,
        "machine_profile": "st-emutos-ci",
        "rom_sha256": rom_sha,
        "runtime_seconds": args.runtime_seconds,
        "network": "disabled",
        "host_shared_folders": "disabled",
        "gemdos_events": counts["gemdos"],
        "bios_events": counts["bios"],
        "xbios_events": counts["xbios"],
        "result": "PASS",
    }
    (analysis / "qualification-m3_1.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"M3.1 PASS: GEMDOS={counts['gemdos']} BIOS={counts['bios']} XBIOS={counts['xbios']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
