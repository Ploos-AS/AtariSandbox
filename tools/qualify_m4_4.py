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


def wait_for_path(path: Path, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return True
        time.sleep(0.05)
    return path.exists()


def fifo_command(path: Path, command: str) -> None:
    with path.open("w", encoding="utf-8") as fifo:
        fifo.write(command.rstrip("\n") + "\n")
        fifo.flush()


def main() -> int:
    p = argparse.ArgumentParser(description="AtariSandbox M4.4 visual/memory evidence qualifier")
    p.add_argument("--analysis-dir", required=True)
    p.add_argument("--hatari", required=True)
    p.add_argument("--rom", required=True)
    p.add_argument("--backend-revision", required=True)
    p.add_argument("--runtime-seconds", type=int, default=8)
    p.add_argument("--max-screenshot-bytes", type=int, default=4 * 1024 * 1024)
    p.add_argument("--max-memory-bytes", type=int, default=4 * 1024 * 1024)
    args = p.parse_args()

    analysis = Path(args.analysis_dir).resolve()
    analysis.mkdir(parents=True, exist_ok=True)
    hatari = Path(args.hatari).resolve()
    rom = Path(args.rom).resolve()
    if not hatari.is_file():
        raise SystemExit("Hatari binary missing")
    if not rom.is_file() or rom.stat().st_size < 128 * 1024:
        raise SystemExit("invalid EmuTOS ROM")

    fifo = analysis / "hatari-control.fifo"
    mem = analysis / "memory-state.sav"
    log = analysis / "hatari.log"
    for stale in (fifo, mem):
        if stale.exists():
            stale.unlink()

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
        "--cmd-fifo", str(fifo),
        "--log-file", str(log),
    ]
    env = os.environ.copy()
    env["ATARISANDBOX_ANALYSIS_DIR"] = str(analysis)
    proc = subprocess.Popen(cmd, env=env, cwd=analysis, start_new_session=True)

    if not wait_for_path(fifo, 5.0):
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=5)
        raise SystemExit("Hatari control FIFO was not created")

    time.sleep(args.runtime_seconds)
    if proc.poll() is not None:
        raise SystemExit(f"Hatari exited too early with rc={proc.returncode}")

    # Use Hatari's native remote shortcuts. Screenshot output is constrained by
    # cwd=analysis; memory-state output is explicitly redirected there.
    fifo_command(fifo, f"hatari-path memsave {mem}")
    fifo_command(fifo, "hatari-shortcut screenshot")
    fifo_command(fifo, "hatari-shortcut savemem")

    screenshot: Path | None = None
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        candidates = sorted(analysis.glob("grab*.*"))
        if candidates and mem.exists() and mem.stat().st_size > 0:
            screenshot = candidates[-1]
            if screenshot.stat().st_size > 0:
                break
        time.sleep(0.1)
    if screenshot is None or not screenshot.exists() or screenshot.stat().st_size == 0:
        raise SystemExit("Hatari screenshot evidence was not created")
    if not mem.exists() or mem.stat().st_size == 0:
        raise SystemExit("Hatari memory snapshot evidence was not created")
    if screenshot.parent != analysis or mem.parent != analysis:
        raise SystemExit("evidence escaped analysis directory")
    if screenshot.stat().st_size > args.max_screenshot_bytes:
        raise SystemExit("screenshot exceeds M4.4 size bound")
    if mem.stat().st_size > args.max_memory_bytes:
        raise SystemExit("memory snapshot exceeds M4.4 size bound")

    objects = [
        {
            "kind": "screenshot",
            "path": screenshot.name,
            "bytes": screenshot.stat().st_size,
            "sha256": sha256_file(screenshot),
        },
        {
            "kind": "memory_snapshot",
            "path": mem.name,
            "bytes": mem.stat().st_size,
            "sha256": sha256_file(mem),
        },
    ]
    manifest = {
        "schema": "atarisandbox.m4_4.evidence/1",
        "backend_revision": args.backend_revision,
        "machine_profile": "st-emutos-visual-memory-ci",
        "rom_sha256": sha256_file(rom),
        "network": "disabled",
        "host_shared_folders": "disabled",
        "object_count": len(objects),
        "objects": objects,
    }
    manifest_path = analysis / "evidence-m4_4.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    fifo_command(fifo, "hatari-shortcut quit")
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=5)
        raise SystemExit("Hatari did not exit cleanly")
    if proc.returncode != 0:
        raise SystemExit(f"Hatari returned rc={proc.returncode}")

    verdict = {
        "schema": "atarisandbox.m4_4.qualification/1",
        "backend_revision": args.backend_revision,
        "machine_profile": "st-emutos-visual-memory-ci",
        "network": "disabled",
        "host_shared_folders": "disabled",
        "screenshot_captured": True,
        "memory_snapshot_captured": True,
        "hash_bound_manifest": True,
        "analysis_directory_only": True,
        "screenshot_bytes": objects[0]["bytes"],
        "memory_snapshot_bytes": objects[1]["bytes"],
        "manifest_sha256": sha256_file(manifest_path),
        "result": "PASS",
    }
    (analysis / "qualification-m4_4.json").write_text(
        json.dumps(verdict, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"M4.4 PASS: screenshot={objects[0]['bytes']} bytes memory={objects[1]['bytes']} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
