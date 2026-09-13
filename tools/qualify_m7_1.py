#!/usr/bin/env python3
"""AtariSandbox M7.1 physical-workstation qualification collector.

This collector is intentionally host-side and harmless.  It records provenance and
verifies an already-completed disposable AtariSandbox qualification run.  It does
not launch samples or enable networking.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "atarisandbox.m7_1.qualification/1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(repo: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, default=Path.cwd())
    p.add_argument("--rom", type=Path, required=True)
    p.add_argument("--source-media", type=Path, required=True)
    p.add_argument("--runtime-media", type=Path, required=True)
    p.add_argument("--evidence-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--machine-profile", default="st")
    p.add_argument("--rom-label", required=True, help="e.g. EmuTOS-1.4 or locally-owned TOS label")
    p.add_argument("--operator-confirm-visible", action="store_true")
    p.add_argument("--operator-confirm-network-off", action="store_true")
    p.add_argument("--operator-confirm-no-writable-host-shares", action="store_true")
    p.add_argument("--operator-confirm-runtime-destroyed", action="store_true")
    args = p.parse_args()

    required = [args.rom, args.source_media, args.evidence_dir]
    missing = [str(x) for x in required if not x.exists()]
    if missing:
        raise SystemExit("missing required input: " + ", ".join(missing))

    source_hash = sha256(args.source_media)
    runtime_exists = args.runtime_media.exists()
    runtime_hash = sha256(args.runtime_media) if runtime_exists else None

    confirmations = {
        "visible_runtime_observed": args.operator_confirm_visible,
        "network_off": args.operator_confirm_network_off,
        "no_writable_host_shares": args.operator_confirm_no_writable_host_shares,
        "runtime_destroyed": args.operator_confirm_runtime_destroyed,
    }

    # Destruction is fail-closed: confirmation alone is insufficient if the
    # disposable runtime image is still present.
    cleanup_verified = args.operator_confirm_runtime_destroyed and not runtime_exists
    policy_pass = all([
        args.operator_confirm_visible,
        args.operator_confirm_network_off,
        args.operator_confirm_no_writable_host_shares,
        cleanup_verified,
    ])

    evidence_objects = []
    for name in ("session.json", "events.jsonl", "asw-manifest.json"):
        path = args.evidence_dir / name
        if path.is_file():
            evidence_objects.append({
                "path": name,
                "size": path.stat().st_size,
                "sha256": sha256(path),
            })

    evidence_pass = len(evidence_objects) >= 2
    result = "PASS" if policy_pass and evidence_pass else "FAIL"

    doc = {
        "schema": SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": result,
        "repository_revision": git_head(args.repo),
        "workstation": {
            "hostname": socket.gethostname(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "runtime": {
            "machine_profile": args.machine_profile,
            "rom_label": args.rom_label,
            "rom_sha256": sha256(args.rom),
            "source_media_sha256": source_hash,
            "runtime_media_present_after_cleanup": runtime_exists,
            "runtime_media_sha256_if_present": runtime_hash,
        },
        "operator_confirmations": confirmations,
        "cleanup_verified": cleanup_verified,
        "evidence": evidence_objects,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"M7.1 physical workstation qualification: {result}")
    print(args.output)
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
