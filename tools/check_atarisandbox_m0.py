#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

required = [
    ROOT / "README.md",
    ROOT / "gpl.txt",
    ROOT / "docs" / "ROADMAP.md",
    ROOT / "docs" / "SAFETY.md",
    ROOT / "src",
    ROOT / "CMakeLists.txt",
]

for path in required:
    if not path.exists():
        raise SystemExit(f"missing required M0 path: {path.relative_to(ROOT)}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
roadmap = (ROOT / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
safety = (ROOT / "docs" / "SAFETY.md").read_text(encoding="utf-8")

checks = {
    "Hatari Malware Analysis Edition": readme,
    "11964da62914bf232ca84eacf0cedf1d25223e08": readme,
    "session.json": readme + roadmap,
    "events.jsonl": readme + roadmap,
    "EmuTOS": readme + roadmap,
    "networking disabled": readme + safety,
    "no broad writable host filesystem": readme + safety,
    "ASW Core": readme + safety,
}

for needle, haystack in checks.items():
    if needle not in haystack:
        raise SystemExit(f"M0 contract missing required text: {needle}")

for forbidden in ("samples", "malware", "quarantine"):
    candidate = ROOT / forbidden
    if candidate.exists():
        raise SystemExit(f"forbidden repository sample path exists: {forbidden}")

print("AtariSandbox M0 checks: PASS")
