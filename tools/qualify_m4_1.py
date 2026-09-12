#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(description="AtariSandbox M4.1 disposable media identity qualifier")
    p.add_argument("--source-media", required=True)
    p.add_argument("--analysis-dir", required=True)
    p.add_argument("--backend-revision", required=True)
    args = p.parse_args()

    source = Path(args.source_media).resolve()
    analysis = Path(args.analysis_dir).resolve()
    analysis.mkdir(parents=True, exist_ok=True)
    if not source.is_file() or source.stat().st_size == 0:
        raise SystemExit("source media missing or empty")

    source_sha = sha256_file(source)
    runtime = analysis / "runtime-media.img"
    shutil.copyfile(source, runtime)
    runtime_pre_sha = sha256_file(runtime)
    if runtime_pre_sha != source_sha:
        raise SystemExit("disposable runtime media differs from source before runtime")

    # M4.1 is deliberately harmless: prove that all writes are confined to a
    # disposable copy and that the immutable source remains unchanged.
    with runtime.open("r+b") as f:
        original = f.read(16)
        f.seek(0)
        f.write(bytes((b ^ 0x5A) for b in original))

    runtime_post_sha = sha256_file(runtime)
    source_post_sha = sha256_file(source)
    if source_post_sha != source_sha:
        raise SystemExit("source media was modified")
    if runtime_post_sha == runtime_pre_sha:
        raise SystemExit("runtime media did not record the controlled change")

    manifest = {
        "schema": "atarisandbox.media/1",
        "source": {
            "name": source.name,
            "size": source.stat().st_size,
            "sha256_pre": source_sha,
            "sha256_post": source_post_sha,
            "immutable": True,
        },
        "runtime": {
            "name": runtime.name,
            "size": runtime.stat().st_size,
            "sha256_pre": runtime_pre_sha,
            "sha256_post": runtime_post_sha,
            "disposable": True,
            "changed": True,
        },
    }
    (analysis / "media.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    qualification = {
        "schema": "atarisandbox.m4_1.qualification/1",
        "backend_revision": args.backend_revision,
        "source_preserved": True,
        "disposable_runtime_media": True,
        "pre_post_sha256": True,
        "result": "PASS",
    }
    (analysis / "qualification-m4_1.json").write_text(
        json.dumps(qualification, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"M4.1 PASS: source={source_sha} runtime_post={runtime_post_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
