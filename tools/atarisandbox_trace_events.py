#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

EVENT_SCHEMA = "atarisandbox.event/1"

# Hatari trace output is intentionally treated as an upstream diagnostic format.
# Keep the parser permissive and preserve the original line in every emitted event.
EXCEPTION_RE = re.compile(r"(?:exception|vector)\D*(?P<vector>\d+)", re.IGNORECASE)
PC_RE = re.compile(r"\bPC\s*[=:]\s*(?:0x|\$)?(?P<pc>[0-9a-fA-F]+)")
SR_RE = re.compile(r"\bSR\s*[=:]\s*(?:0x|\$)?(?P<sr>[0-9a-fA-F]+)")
REG_RE = re.compile(r"\b(?P<name>[dDaA][0-7])\s*[=:]\s*(?:0x|\$)?(?P<value>[0-9a-fA-F]{1,8})")


def _hex(value: str | None) -> int | None:
    return int(value, 16) if value else None


def parse_line(line: str) -> dict | None:
    raw = line.rstrip("\n")
    if not raw:
        return None

    regs = {m.group("name").lower(): _hex(m.group("value")) for m in REG_RE.finditer(raw)}
    pc_match = PC_RE.search(raw)
    sr_match = SR_RE.search(raw)
    exc_match = EXCEPTION_RE.search(raw)

    if exc_match:
        event = {
            "schema": EVENT_SCHEMA,
            "type": "cpu.exception",
            "source": "hatari-core-trace",
            "unix_ns": time.time_ns(),
            "vector": int(exc_match.group("vector")),
            "raw": raw,
        }
        if pc_match:
            event["pc"] = _hex(pc_match.group("pc"))
        if sr_match:
            event["sr"] = _hex(sr_match.group("sr"))
        if regs:
            event["registers"] = regs
        return event

    if pc_match or sr_match or regs:
        event = {
            "schema": EVENT_SCHEMA,
            "type": "cpu.snapshot",
            "source": "hatari-core-trace",
            "unix_ns": time.time_ns(),
            "raw": raw,
        }
        if pc_match:
            event["pc"] = _hex(pc_match.group("pc"))
        if sr_match:
            event["sr"] = _hex(sr_match.group("sr"))
        if regs:
            event["registers"] = regs
        return event

    return None


def convert(trace_path: Path, output_path: Path) -> tuple[int, int]:
    snapshots = 0
    exceptions = 0
    with trace_path.open("r", encoding="utf-8", errors="replace") as source, output_path.open("a", encoding="utf-8") as out:
        for line in source:
            event = parse_line(line)
            if not event:
                continue
            if event["type"] == "cpu.snapshot":
                snapshots += 1
            elif event["type"] == "cpu.exception":
                exceptions += 1
            out.write(json.dumps(event, sort_keys=True) + "\n")
    return snapshots, exceptions


def main() -> int:
    p = argparse.ArgumentParser(description="Convert Hatari CPU/exception trace into AtariSandbox JSONL events")
    p.add_argument("--trace", required=True)
    p.add_argument("--events", required=True)
    p.add_argument("--require-snapshot", action="store_true")
    args = p.parse_args()

    trace = Path(args.trace).resolve()
    events = Path(args.events).resolve()
    if not trace.is_file():
        raise SystemExit("Hatari trace file missing")
    if not events.is_file():
        raise SystemExit("AtariSandbox events file missing")

    snapshots, exceptions = convert(trace, events)
    if args.require_snapshot and snapshots < 1:
        raise SystemExit("no CPU snapshot found in Hatari trace")
    print(json.dumps({"cpu_snapshots": snapshots, "cpu_exceptions": exceptions}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
