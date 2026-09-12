#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "atarisandbox_os_trace_events.py"
spec = importlib.util.spec_from_file_location("atarisandbox_os_trace_events", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class AtariSandboxM3Tests(unittest.TestCase):
    def test_gemdos_process_call(self):
        event = module.classify('GEMDOS call=$4b Pexec("C:\\TEST.PRG")')
        self.assertEqual(event["type"], "os.gemdos.call")
        self.assertEqual(event["call_number"], 0x4B)
        self.assertEqual(event["call_name"], "Pexec")
        self.assertEqual(event["operation_class"], "process")
        self.assertEqual(event["path"], "C:\\TEST.PRG")

    def test_gemdos_filesystem_call(self):
        event = module.classify('GEMDOS function=61 Fopen("A:\\README.TXT")')
        self.assertEqual(event["operation_class"], "filesystem")
        self.assertEqual(event["call_number"], 61)

    def test_bios_and_xbios(self):
        bios = module.classify("BIOS #=0x03 Bconout(2,65)")
        xbios = module.classify("XBIOS call=2 Physbase()")
        self.assertEqual(bios["type"], "os.bios.call")
        self.assertEqual(xbios["type"], "os.xbios.call")

    def test_unrelated_line_ignored(self):
        self.assertIsNone(module.classify("CPU 0001234 NOP"))

    def test_trace_limit_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.log"
            events = Path(tmp) / "events.jsonl"
            trace.write_text("GEMDOS Pexec()\n" * 100, encoding="utf-8")
            with self.assertRaises(SystemExit):
                module.convert(trace, events, 32, 100)

    def test_event_limit_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.log"
            events = Path(tmp) / "events.jsonl"
            trace.write_text("GEMDOS Pexec()\nGEMDOS Pterm()\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                module.convert(trace, events, 1024, 1)

    def test_convert_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.log"
            events = Path(tmp) / "events.jsonl"
            trace.write_text(
                'GEMDOS call=$4b Pexec("C:\\HELLO.PRG")\n'
                'BIOS #=0x03 Bconout(2,65)\n'
                'XBIOS call=2 Physbase()\n',
                encoding="utf-8",
            )
            counts = module.convert(trace, events, 4096, 16)
            parsed = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(counts, {"gemdos": 1, "bios": 1, "xbios": 1, "events": 3})
            self.assertEqual(len(parsed), 3)


if __name__ == "__main__":
    unittest.main()
