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
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, events: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )


def validate_core_snapshot(event: dict) -> None:
    if event.get("schema") != "atarisandbox.event/1":
        raise SystemExit("unexpected core event schema")
    if event.get("type") != "cpu.exception.snapshot":
        raise SystemExit("unexpected core snapshot event type")
    if event.get("source") != "atarisandbox.cpu_core":
        raise SystemExit("unexpected core snapshot source")
    for key in ("exception_nr", "exception_source", "pc", "instruction_pc", "sr", "cycles"):
        if not isinstance(event.get(key), int):
            raise SystemExit(f"invalid core snapshot field: {key}")
    for bank in ("d", "a"):
        values = event.get(bank)
        if not isinstance(values, list) or len(values) != 8:
            raise SystemExit(f"invalid {bank.upper()} register bank")
        if not all(isinstance(value, int) and 0 <= value <= 0xFFFFFFFF for value in values):
            raise SystemExit(f"invalid {bank.upper()} register value")


def validate_memory_write(event: dict) -> None:
    if event.get("schema") != "atarisandbox.event/1":
        raise SystemExit("unexpected memory event schema")
    if event.get("type") != "memory.write":
        raise SystemExit("unexpected memory event type")
    if event.get("source") != "atarisandbox.memory_core":
        raise SystemExit("unexpected memory event source")
    for key in ("address", "size", "value", "pc", "instruction_pc", "cycles"):
        if not isinstance(event.get(key), int):
            raise SystemExit(f"invalid memory.write field: {key}")
    if event["size"] not in (1, 2, 4):
        raise SystemExit("invalid memory.write size")
    if not 0 <= event["address"] <= 0xFFFFFFFF:
        raise SystemExit("invalid memory.write address")
    max_value = (1 << (event["size"] * 8)) - 1
    if not 0 <= event["value"] <= max_value:
        raise SystemExit("memory.write value does not fit write size")


def main() -> int:
    p = argparse.ArgumentParser(description="AtariSandbox M2.2 real Hatari/EmuTOS runtime qualifier")
    p.add_argument("--analysis-dir", required=True)
    p.add_argument("--hatari", required=True)
    p.add_argument("--rom", required=True)
    p.add_argument("--backend-revision", required=True)
    p.add_argument("--runtime-seconds", type=int, default=8)
    p.add_argument("--memory-write-limit", type=int, default=256)
    args = p.parse_args()

    if args.memory_write_limit <= 0:
        raise SystemExit("memory write limit must be positive for M2.2 qualification")

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
    env["ATARISANDBOX_MEMORY_WRITE_LIMIT"] = str(args.memory_write_limit)
    proc = subprocess.Popen(lifecycle_cmd, env=env, start_new_session=True)
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
    if session.get("schema") != "atarisandbox.session/1":
        raise SystemExit("unexpected session schema")
    if session.get("machine_profile") != "st-emutos-ci":
        raise SystemExit("unexpected machine profile")
    if session.get("completed") is not True:
        raise SystemExit("session did not complete cleanly")

    events_path = analysis / "events.jsonl"
    lifecycle_events = read_jsonl(events_path)
    starts = [e for e in lifecycle_events if e.get("type") == "session.start"]
    stops = [e for e in lifecycle_events if e.get("type") == "session.stop"]
    if len(starts) != 1 or len(stops) != 1:
        raise SystemExit("invalid lifecycle evidence")

    converter = Path(__file__).with_name("atarisandbox_trace_to_events.py")
    trace_events_path = analysis / "trace-events.jsonl"
    subprocess.run(
        [
            os.environ.get("PYTHON", "python3"),
            str(converter),
            "--trace", str(trace_path),
            "--events", str(trace_events_path),
            "--require-events",
        ],
        check=True,
    )

    trace_events = read_jsonl(trace_events_path)
    cpu_events = [e for e in trace_events if e.get("type") == "cpu.exception"]
    if not cpu_events:
        raise SystemExit("missing structured cpu.exception evidence")
    for event in cpu_events:
        for key in ("exception_nr", "pc", "instruction_pc", "vector_target", "sr"):
            if not isinstance(event.get(key), int):
                raise SystemExit(f"invalid cpu.exception field: {key}")

    core_path = analysis / "core-events.jsonl"
    if not core_path.is_file():
        raise SystemExit("missing CPU/memory core instrumentation evidence")
    core_events = read_jsonl(core_path)
    if not core_events:
        raise SystemExit("empty CPU/memory core instrumentation evidence")

    snapshot_events = [e for e in core_events if e.get("type") == "cpu.exception.snapshot"]
    memory_events = [e for e in core_events if e.get("type") == "memory.write"]
    unknown_core_events = [
        e for e in core_events
        if e.get("type") not in {"cpu.exception.snapshot", "memory.write"}
    ]
    if unknown_core_events:
        raise SystemExit("unexpected core instrumentation event type")
    if not snapshot_events:
        raise SystemExit("missing CPU exception snapshots")
    if not memory_events:
        raise SystemExit("missing guest memory-write evidence")
    if len(memory_events) > args.memory_write_limit:
        raise SystemExit("memory-write evidence exceeded configured bound")

    for event in snapshot_events:
        validate_core_snapshot(event)
    for event in memory_events:
        validate_memory_write(event)

    unified_events = starts + core_events + trace_events + stops
    write_jsonl(events_path, unified_events)

    summary = {
        "schema": "atarisandbox.m2_2.qualification/1",
        "backend_revision": args.backend_revision,
        "machine_profile": "st-emutos-ci",
        "rom_sha256": rom_sha,
        "runtime_seconds": args.runtime_seconds,
        "network": "disabled",
        "host_shared_folders": "disabled",
        "cpu_exception_events": len(cpu_events),
        "cpu_exception_snapshot_events": len(snapshot_events),
        "memory_write_events": len(memory_events),
        "memory_write_limit": args.memory_write_limit,
        "memory_write_fields": ["address", "size", "value", "pc", "instruction_pc", "cycles"],
        "register_snapshot": {
            "data_registers": 8,
            "address_registers": 8,
            "pc": True,
            "instruction_pc": True,
            "sr": True,
            "cycles": True,
        },
        "result": "PASS",
    }
    (analysis / "qualification.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        "M2.2 PASS: "
        f"{len(cpu_events)} trace exceptions, "
        f"{len(snapshot_events)} CPU snapshots, "
        f"{len(memory_events)} bounded memory writes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
