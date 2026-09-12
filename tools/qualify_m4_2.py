#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import shutil
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
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    p = argparse.ArgumentParser(description="AtariSandbox M4.2 real floppy I/O runtime qualifier")
    p.add_argument("--analysis-dir", required=True)
    p.add_argument("--hatari", required=True)
    p.add_argument("--rom", required=True)
    p.add_argument("--source-media", required=True)
    p.add_argument("--backend-revision", required=True)
    p.add_argument("--runtime-seconds", type=int, default=8)
    args = p.parse_args()

    analysis = Path(args.analysis_dir).resolve()
    analysis.mkdir(parents=True, exist_ok=True)
    hatari = Path(args.hatari).resolve()
    rom = Path(args.rom).resolve()
    source = Path(args.source_media).resolve()
    if not hatari.is_file():
        raise SystemExit("Hatari binary missing")
    if not rom.is_file() or rom.stat().st_size < 128 * 1024:
        raise SystemExit("invalid EmuTOS ROM")
    if not source.is_file() or source.stat().st_size < 512:
        raise SystemExit("invalid source media")

    source_pre = sha256_file(source)
    runtime = analysis / "runtime-media.st"
    shutil.copyfile(source, runtime)
    runtime_pre = sha256_file(runtime)
    if runtime_pre != source_pre:
        raise SystemExit("runtime media does not match source")

    log_path = analysis / "hatari.log"
    cmd = [
        str(hatari),
        "--machine", "st",
        "--cpulevel", "0",
        "--memsize", "1",
        "--tos", str(rom),
        "--disk-a", str(runtime),
        "--protect-floppy", "off",
        "--fast-boot", "on",
        "--sound", "off",
        "--confirm-quit", "off",
        "--window",
        "--statusbar", "off",
        "--log-file", str(log_path),
    ]

    env = os.environ.copy()
    env["ATARISANDBOX_ANALYSIS_DIR"] = str(analysis)
    env["ATARISANDBOX_MEDIA_IO_LIMIT"] = "4096"
    proc = subprocess.Popen(cmd, env=env, start_new_session=True)
    time.sleep(args.runtime_seconds)
    if proc.poll() is not None:
        raise SystemExit(f"Hatari exited too early with rc={proc.returncode}")

    proc.terminate()
    try:
        proc.wait(timeout=7)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=5)
        raise SystemExit("Hatari did not terminate cleanly")

    events = read_jsonl(analysis / "core-events.jsonl")
    reads = [e for e in events if e.get("type") == "media.floppy.read"]
    writes = [e for e in events if e.get("type") == "media.floppy.write"]
    if not reads:
        raise SystemExit("no real floppy read evidence observed")

    for event in reads + writes:
        if event.get("schema") != "atarisandbox.event/1":
            raise SystemExit("invalid media event schema")
        if event.get("source") != "atarisandbox.floppy_core":
            raise SystemExit("invalid media event source")
        for key in ("drive", "track", "side", "sector", "count", "sector_size", "boot_sector"):
            if key not in event:
                raise SystemExit(f"media event missing {key}")

    source_post = sha256_file(source)
    runtime_post = sha256_file(runtime)
    if source_post != source_pre:
        raise SystemExit("immutable source media changed")

    boot_writes = [e for e in writes if e.get("boot_sector") is True]
    summary = {
        "schema": "atarisandbox.m4_2.qualification/1",
        "backend_revision": args.backend_revision,
        "machine_profile": "st-emutos-floppy-ci",
        "network": "disabled",
        "host_shared_folders": "disabled",
        "source_sha256_pre": source_pre,
        "source_sha256_post": source_post,
        "runtime_sha256_pre": runtime_pre,
        "runtime_sha256_post": runtime_post,
        "read_events": len(reads),
        "write_events": len(writes),
        "boot_sector_write_events": len(boot_writes),
        "source_preserved": True,
        "real_floppy_read_path": True,
        "write_path_instrumented": True,
        "boot_sector_classifier": True,
        "result": "PASS",
    }
    (analysis / "qualification-m4_2.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"M4.2 PASS: reads={len(reads)} writes={len(writes)} "
        f"boot-sector-writes={len(boot_writes)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
