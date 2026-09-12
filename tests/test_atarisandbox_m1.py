import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "atarisandbox_run.py"


class M1AnalysisRunnerTests(unittest.TestCase):
    def test_successful_command_emits_session_and_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            cmd = [
                sys.executable, str(RUNNER),
                "--analysis-dir", tmp,
                "--machine-profile", "st-emutos-ci",
                "--config-fingerprint", "test-fingerprint",
                "--backend-revision", "test-revision",
                "--", sys.executable, "-c", "print('harmless runtime')",
            ]
            cp = subprocess.run(cmd, check=False)
            self.assertEqual(cp.returncode, 0)
            session = json.loads((Path(tmp) / "session.json").read_text())
            self.assertEqual(session["schema"], "atarisandbox.session/1")
            self.assertEqual(session["backend"], "atarisandbox")
            self.assertEqual(session["machine_profile"], "st-emutos-ci")
            self.assertEqual(session["network"], "disabled")
            self.assertEqual(session["host_shared_folders"], "disabled")
            self.assertTrue(session["completed"])
            self.assertEqual(session["exit_code"], 0)
            events = [json.loads(line) for line in (Path(tmp) / "events.jsonl").read_text().splitlines()]
            self.assertEqual([e["type"] for e in events], ["session.start", "session.stop"])

    def test_refuses_to_overwrite_existing_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "session.json").write_text("{}\n")
            cmd = [sys.executable, str(RUNNER), "--analysis-dir", tmp, "--", sys.executable, "-c", "pass"]
            cp = subprocess.run(cmd, check=False)
            self.assertNotEqual(cp.returncode, 0)


if __name__ == "__main__":
    unittest.main()
