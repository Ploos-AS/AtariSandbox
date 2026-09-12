#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

EVENT_SCHEMA = "atarisandbox.event/1"
DEFAULT_MAX_TRACE_BYTES = 16 * 1024 * 1024
DEFAULT_MAX_EVENTS = 4096
MAX_RAW_CHARS = 4096

CLASS_RE = re.compile(r"\b(?P<class>GEMDOS|BIOS|XBIOS)\b", re.IGNORECASE)
CALL_HEX_RE = re.compile(r"(?:call|opcode|function|fn|#)\s*[=:]?\s*(?:0x|\$)(?P<num>[0-9a-fA-F]{1,4})", re.IGNORECASE)
CALL_DEC_RE = re.compile(r"(?:call|opcode|function|fn|#)\s*[=:]?\s*(?P<num>\d{1,5})", re.IGNORECASE)
NAME_RE = re.compile(r"\b(?P<name>[A-Za-z][A-Za-z0-9_]{1,31})\s*\(")
PATH_RE = re.compile(r"(?P<quote>['\"])(?P<path>[^'\"\r\n]{1,1024})(?P=quote)")

PROCESS_NAMES = {"pexec", "pterm", "pterm0", "ptermres"}
FILE_NAMES = {
    "fcreate", "fopen", "fclose", "fread", "fwrite", "fdelete", "frename",
    "fattrib", "fsfirst", "fsnext", "dcreate", "ddelete", "dsetpath", "dgetpath",
}


def classify(line: str) -> dict | None:
    raw = line.rstrip("\n")
    match = CLASS_RE.search(raw)
    if not match:
        return None

    api = match.group("class").lower()
    event: dict = {
        "schema": EVENT_SCHEMA,
        "type": f"os.{api}.call",
        "source": "hatari-os-trace",
        "api": api,
        "raw": raw[:MAX_RAW_CHARS],
    }

    number = CALL_HEX_RE.search(raw)
    if number:
        event["call_number"] = int(number.group("num"), 16)
    else:
        number = CALL_DEC_RE.search(raw)
        if number:
            event["call_number"] = int(number.group("num"), 10)

    name = NAME_RE.search(raw)
    if name:
        call_name = name.group("name")
        event["call_name"] = call_name
        lname = call_name.lower()
        if api == "gemdos" and lname in PROCESS_NAMES:
            event["operation_class"] = "process"
        elif api == "gemdos" and lname in FILE_NAMES:
            event["operation_class"] = "filesystem"

    path = PATH_RE.search(raw)
    if path:
        event["path"] = path.group("path")

    return event


def convert(trace_path: Path, events_path: Path, max_trace_bytes: int, max_events: int) -> dict[str, int]:
    size = trace_path.stat().st_size
    if size > max_trace_bytes:
        raise SystemExit(f"trace exceeds limit: {size} > {max_trace_bytes}")

    counts = {"gemdos": 0, "bios": 0, "xbios": 0, "events": 0}
    with trace_path.open("r", encoding="utf-8", errors="replace") as src, events_path.open("a", encoding="utf-8") as dst:
        for line in src:
            event = classify(line)
            if event is None:
                continue
            if counts["events"] >= max_events:
                raise SystemExit(f"event limit exceeded: {max_events}")
            dst.write(json.dumps(event, sort_keys=True) + "\n")
            counts[event["api"]] += 1
            counts["events"] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Hatari GEMDOS/BIOS/XBIOS trace lines to AtariSandbox events")
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--max-trace-bytes", type=int, default=DEFAULT_MAX_TRACE_BYTES)
    parser.add_argument("--max-events", type=int, default=DEFAULT_MAX_EVENTS)
    parser.add_argument("--require-gemdos", action="store_true")
    args = parser.parse_args()

    if not args.trace.is_file():
        raise SystemExit(f"trace file not found: {args.trace}")
    if args.max_trace_bytes < 1 or args.max_events < 1:
        raise SystemExit("limits must be positive")

    counts = convert(args.trace, args.events, args.max_trace_bytes, args.max_events)
    if args.require_gemdos and counts["gemdos"] < 1:
        raise SystemExit("no GEMDOS events found")
    print(json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
