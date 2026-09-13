#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

ALLOWED_KINDS = {"screenshot", "memory_snapshot"}
MAX_OBJECTS = 16
MAX_OBJECT_BYTES = 16 * 1024 * 1024


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(msg: str) -> None:
    raise SystemExit(f"M5 ASW adapter FAIL: {msg}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate AtariSandbox evidence and emit an ASW ingestion manifest")
    ap.add_argument("--analysis-dir", required=True)
    ap.add_argument("--output", default="asw-manifest.json")
    args = ap.parse_args()

    root = Path(args.analysis_dir).resolve()
    evidence_path = root / "evidence-m4_4.json"
    qualification_path = root / "qualification-m4_4.json"
    if not evidence_path.is_file() or not qualification_path.is_file():
        fail("missing M4.4 evidence or qualification manifest")

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    qualification = json.loads(qualification_path.read_text(encoding="utf-8"))
    if evidence.get("schema") != "atarisandbox.m4_4.evidence/1":
        fail("unsupported evidence schema")
    if qualification.get("schema") != "atarisandbox.m4_4.qualification/1" or qualification.get("result") != "PASS":
        fail("M4.4 qualification is not PASS")

    # M4.4's qualified contract expresses deny-by-default policy as strings.
    # The ASW ingestion contract normalizes those states to boolean capability
    # flags after requiring both evidence and qualification to agree.
    if evidence.get("network") != "disabled" or evidence.get("host_shared_folders") != "disabled":
        fail("unsafe runtime policy in evidence")
    if qualification.get("network") != "disabled" or qualification.get("host_shared_folders") != "disabled":
        fail("unsafe runtime policy in qualification")

    objects = evidence.get("objects")
    if not isinstance(objects, list) or not (1 <= len(objects) <= MAX_OBJECTS):
        fail("invalid object count")
    if evidence.get("object_count") != len(objects):
        fail("evidence object_count mismatch")

    out_objects = []
    seen = set()
    for obj in objects:
        kind = obj.get("kind")
        rel = obj.get("path")
        if kind not in ALLOWED_KINDS or not isinstance(rel, str) or not rel:
            fail("unsupported object kind/path")
        p = (root / rel).resolve()
        if root not in p.parents:
            fail("object escapes analysis directory")
        if not p.is_file():
            fail(f"missing object: {rel}")
        size = p.stat().st_size
        if not (0 < size <= MAX_OBJECT_BYTES):
            fail(f"object size out of bounds: {rel}")
        digest = sha256_file(p)
        if size != obj.get("bytes") or digest != obj.get("sha256"):
            fail(f"object identity mismatch: {rel}")
        if rel in seen:
            fail(f"duplicate object path: {rel}")
        seen.add(rel)
        out_objects.append({"kind": kind, "path": rel, "bytes": size, "sha256": digest})

    source_manifest_sha256 = sha256_file(evidence_path)
    manifest = {
        "schema": "atarisandbox.asw-ingest/1",
        "producer": "AtariSandbox",
        "machine_profile": evidence.get("machine_profile"),
        "backend_revision": evidence.get("backend_revision"),
        "rom_sha256": evidence.get("rom_sha256"),
        "source_evidence": "evidence-m4_4.json",
        "source_evidence_sha256": source_manifest_sha256,
        "network_enabled": False,
        "host_shared_folders_enabled": False,
        "object_count": len(out_objects),
        "objects": out_objects,
    }
    output = (root / args.output).resolve()
    if root not in output.parents:
        fail("output escapes analysis directory")
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"M5 ASW adapter PASS: {output}")


if __name__ == "__main__":
    main()
