#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "atarisandbox_trace_events.py"
spec = importlib.util.spec_from_file_location("atarisandbox_trace_events", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class TraceEventTests(unittest.TestCase):
    def test_snapshot_full_register_set(self):
        line = (
            "PC=$00fc1234 SR=$2700 "
            "D0=$00000001 D1=$00000002 D2=$00000003 D3=$00000004 "
            "D4=$00000005 D5=$00000006 D6=$00000007 D7=$00000008 "
            "A0=$00000100 A1=$00000200 A2=$00000300 A3=$00000400 "
            "A4=$00000500 A5=$00000600 A6=$00000700 A7=$00000800"
        )
        event = mod.parse_line(line)
        self.assertEqual(event["type"], "cpu.snapshot")
        self.assertEqual(event["pc"], 0x00FC1234)
        self.assertEqual(event["sr"], 0x2700)
        self.assertEqual(len(event["registers"]), 16)
        self.assertEqual(event["registers"]["d7"], 8)
        self.assertEqual(event["registers"]["a7"], 0x800)

    def test_exception_event(self):
        event = mod.parse_line("CPU exception vector 4 PC=$123456 SR=$2000 D0=$deadbeef")
        self.assertEqual(event["type"], "cpu.exception")
        self.assertEqual(event["vector"], 4)
        self.assertEqual(event["pc"], 0x123456)
        self.assertEqual(event["registers"]["d0"], 0xDEADBEEF)

    def test_trace_size_limit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            trace = root / "trace.log"
            events = root / "events.jsonl"
            trace.write_text("PC=$1\n" * 32, encoding="utf-8")
            events.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "trace exceeds limit"):
                mod.convert(trace, events, max_trace_bytes=8, max_events=100)

    def test_event_limit_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            trace = root / "trace.log"
            events = root / "events.jsonl"
            trace.write_text("PC=$1\nPC=$2\nPC=$3\n", encoding="utf-8")
            events.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "event limit exceeded"):
                mod.convert(trace, events, max_trace_bytes=1024, max_events=2)
            parsed = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(parsed), 2)

    def test_raw_line_is_bounded(self):
        event = mod.parse_line("PC=$1 " + ("X" * 10000))
        self.assertLessEqual(len(event["raw"]), mod.MAX_RAW_LINE)


if __name__ == "__main__":
    unittest.main()
