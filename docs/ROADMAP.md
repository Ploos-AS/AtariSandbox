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

Status: implemented and runtime-qualified.

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

Status: PASS on GitHub Actions with Hatari + EmuTOS 1.4.

- Ubuntu GitHub Actions build
- free EmuTOS runtime only
- visible/Xvfb-compatible emulator execution as practical
- verify `session.start` and `session.stop`
- upload evidence artifact
- no proprietary TOS images

Exit gate: green GitHub Actions runtime qualification with retained evidence.

## M2 — CPU and exception instrumentation

Status: implemented and runtime-qualified through M2.2.

- periodic 68000 register snapshots
- PC/SR + D0-D7 + A0-A7
- selected instruction trace mode with bounded output
- exception/vector observations
- watchdog and output-size limits
- versioned `cpu.snapshot` / CPU exception evidence
- bounded Hatari trace adapter with fail-closed trace/event limits

Repository-side gate: PASS.

## M2.1 — Real CPU evidence runtime qualification

Status: PASS on GitHub Actions with real Hatari + EmuTOS runtime.

- preserve M1.1 lifecycle evidence
- require native CPU-core register evidence
- require D0-D7 + A0-A7, PC/instruction PC, SR and cycle fields
- retain structured exception/vector evidence
- merge bounded CPU evidence into the versioned evidence stream
- keep networking and host shared folders disabled

Exit gate: harmless EmuTOS boot produces real CPU-core register evidence and structured exception evidence.

## M2.2 — Bounded memory-write evidence

Status: PASS on GitHub Actions with bounded real runtime evidence.

- emit versioned `memory.write` events from the emulator memory core
- retain write address, value, size, PC/instruction PC and cycle context
- cap retained memory-write evidence to a configured limit
- require at least one real runtime memory-write event
- preserve M2.1 CPU/exception and M1 lifecycle evidence
- keep networking and host shared folders disabled

Exit gate: harmless EmuTOS boot produces real memory-write evidence, with the CI qualification enforcing a 256-event upper bound.

## M3 — Atari OS/API observations

Status: implemented and runtime-qualified through M3.1.

- GEMDOS calls
- BIOS/XBIOS calls
- process/program load/termination observations where practical
- file/path operations where observable without broad host sharing
- versioned `os.gemdos.call`, `os.bios.call`, and `os.xbios.call` evidence
- process/filesystem classification where exposed by Hatari trace text
- bounded trace input, bounded event count, bounded retained raw lines

Repository-side gate: PASS.

## M3.1 — Real OS/API runtime qualification

Status: PASS on GitHub Actions with real Hatari + EmuTOS runtime.

- enable bounded Hatari `gemdos`, `bios`, and `xbios` traces
- run the existing harmless EmuTOS CI profile
- convert actual Hatari trace output into structured events
- require real GEMDOS, BIOS and XBIOS evidence
- retain raw trace for provenance
- preserve lifecycle evidence and deny-by-default settings
- retain ROM SHA-256 and backend revision in qualification evidence

Exit gate: a harmless real Hatari + EmuTOS run produces at least one structured event for each required OS API class and uploads the complete evidence bundle. PASS.

## M4 — Media and persistence evidence

Status: M4.1 implemented; GitHub Actions qualification pending.

- floppy/HDD read/write observations
- boot-sector write detection
- pre/post media SHA-256
- disposable media overlays/images
- screenshot capture and selected memory snapshots

## M4.1 — Media identity and disposable runtime state

Status: implemented; GitHub Actions qualification pending.

- deterministic harmless CI media image
- immutable source-media identity with SHA-256
- disposable runtime media copy
- pre/post SHA-256 for runtime media
- verify controlled changes cannot alter source media
- versioned `atarisandbox.media/1` evidence
- versioned `atarisandbox.m4_1.qualification/1` verdict

Exit gate: CI proves source preservation, disposable runtime state, and hash-visible controlled runtime-media change.

## M4.2 — Real media I/O observations

Status: planned.

- connect Hatari floppy/HDD read/write activity to structured evidence
- classify writes touching boot-sector regions
- bind I/O events to M4.1 media identity
- retain bounded evidence and deny-by-default host access

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
