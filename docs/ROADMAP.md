# AtariSandbox Roadmap

## M0 — Foundation

Status: implemented repository-side.

- establish AtariSandbox identity as Hatari Malware Analysis Edition
- preserve Hatari GPL provenance and upstream lineage
- define defensive-analysis scope and trust boundary
- select ST/STE as initial machine family
- select EmuTOS as the initial free CI boot path
- define minimum `session.json` / `events.jsonl` evidence contract
- define deny-by-default networking and host-write policy
- document ASW Core integration boundary

Exit gate: repository contains project/safety/analysis contracts and upstream provenance without altering emulator semantics.

## M1 — Analysis mode foundation

- add explicit AtariSandbox analysis-mode switch
- create analysis output directory contract
- emit versioned `session.json`
- emit append-only `events.jsonl`
- record emulator revision/build and deterministic config fingerprint
- record selected machine profile and ROM/OS identity/hash
- force/verify networking-disabled and host-share-disabled analysis defaults
- clean start/stop events

Exit gate: harmless EmuTOS boot produces valid deterministic evidence artifacts.

## M1.1 — GitHub runtime qualification

- Ubuntu GitHub Actions build
- free EmuTOS runtime only
- visible/Xvfb-compatible emulator execution as practical
- verify `session.start` and `session.stop`
- upload evidence artifact
- no proprietary TOS images

Exit gate: green GitHub Actions runtime qualification with retained evidence.

## M2 — CPU and exception instrumentation

- periodic 68000 register snapshots
- PC/SR + D0-D7 + A0-A7
- selected instruction trace mode with bounded output
- exception/vector observations
- watchdog and output-size limits

## M3 — Atari OS/API observations

- GEMDOS calls
- BIOS/XBIOS calls
- process/program load/termination observations where practical
- file/path operations where observable without broad host sharing

## M4 — Media and persistence evidence

- floppy/HDD read/write observations
- boot-sector write detection
- pre/post media SHA-256
- disposable media overlays/images
- screenshot capture and selected memory snapshots

## M5 — ASW adapter

- AtariSandbox machine-profile mapping
- ASW-owned runner/evidence ingestion adapter
- hash-bound runtime manifest
- artifact size/type/path validation
- cross-platform namespace enforcement

## M6 — Cross-repo harmless E2E

- ASW checkout
- AtariSandbox checkout/build
- EmuTOS harmless runtime
- evidence generation
- ASW ingestion and hash verification
- evidence artifact upload

## M7 — Physical workstation qualification

- visible ST/STE qualification on the dedicated workstation
- exact local TOS/EmuTOS provenance and hashes
- networking off
- no writable host shares
- disposable runtime state
- cleanup/destruction verification

Only after this gate should controlled real-malware runtime work begin.

## Later scope

Possible later machine profiles include TT and Falcon. They must not be added to the qualified matrix until machine-specific evidence and runtime behavior have their own qualification evidence.
