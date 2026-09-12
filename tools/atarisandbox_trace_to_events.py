#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

EVENT_SCHEMA = "atarisandbox.event/1"
EXCEPTION_RE = re.compile(
    r"cpu exception (?P<nr>\d+)"
    r"(?: vector (?P<vector>[0-9a-fA-F]+))?"
    r" currpc (?P<currpc>[0-9a-fA-F]+)"
    r" buspc (?P<buspc>[0-9a-fA-F]+)"
    r" newpc (?P<newpc>[0-9a-fA-F]+)"
    r" fault_e3 (?P<fault>[0-9a-fA-F]+)"
    r" op_e3 (?P<op>[0-9a-fA-F]+)"
    r" addr_e3 (?P<addr>[0-9a-fA-F]+)"
    r" SR (?P<sr>[0-9a-fA-F]+)",
    re.IGNORECASE,
)


def parse_exception(line: str) -> dict | None:
    match = EXCEPTION_RE.search(line)
    if not match:
        return None
    g = match.groupdict()
    event = {
        "schema": EVENT_SCHEMA,
        "type": "cpu.exception",
        "exception_nr": int(g["nr"], 10),
        "pc": int(g["currpc"], 16),
        "instruction_pc": int(g["buspc"], 16),
        "vector_target": int(g["newpc"], 16),
        "fault_address": int(g["fault"], 16),
        "fault_opcode": int(g["op"], 16),
        "fault_instruction_address": int(g["addr"], 16),
        "sr": int(g["sr"], 16),
        "source": "hatari.cpu_exception_trace",
    }
    if g["vector"] is not None:
        event["vector_offset"] = int(g["vector"], 16)
    return event


def convert(trace_path: Path, output_path: Path) -> int:
    count = 0
    with trace_path.open("r", encoding="utf-8", errors="replace") as src, output_path.open(
        "a", encoding="utf-8"
    ) as dst:
        for line in src:
            event = parse_exception(line)
            if event is None:
                continue
            dst.write(json.dumps(event, sort_keys=True) + "\n")
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Hatari CPU exception trace to AtariSandbox JSONL events")
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--require-events", action="store_true")
    args = parser.parse_args()

    if not args.trace.is_file():
        raise SystemExit(f"trace file not found: {args.trace}")
    count = convert(args.trace, args.events)
    if args.require_events and count == 0:
        raise SystemExit("no Hatari CPU exception events found")
    print(f"converted {count} cpu.exception events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
