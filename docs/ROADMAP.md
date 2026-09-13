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

Status: runtime-qualified through M4.4.

- floppy/HDD read/write observations
- boot-sector write detection
- pre/post media SHA-256
- disposable media overlays/images
- screenshot capture and selected memory snapshots

## M4.1 — Media identity and disposable runtime state

Status: PASS on GitHub Actions.

- deterministic harmless CI media image
- immutable source-media identity with SHA-256
- disposable runtime media copy
- pre/post SHA-256 for runtime media
- verify controlled changes cannot alter source media
- versioned `atarisandbox.media/1` evidence
- versioned `atarisandbox.m4_1.qualification/1` verdict

Exit gate: CI proves source preservation, disposable runtime state, and hash-visible controlled runtime-media change.

## M4.2 — Real media I/O observations

Status: PASS on GitHub Actions with real Hatari + EmuTOS floppy-read evidence.

- use GNU/ELF linker wrapping to observe Hatari's real `Floppy_ReadSectors` and `Floppy_WriteSectors` paths without changing upstream floppy semantics
- emit bounded `media.floppy.read` / `media.floppy.write` events using `atarisandbox.event/1`
- retain drive, track, side, sector, count and sector-size evidence
- classify writes beginning at track 0 / side 0 / sector 1 as boot-sector writes
- boot real Hatari + EmuTOS with deterministic harmless disposable ST media in CI
- require at least one real runtime floppy-read event
- preserve source-media SHA-256 and deny writable host shared folders

Exit gate: harmless Hatari + EmuTOS runtime produces real sector-level floppy-read evidence and proves source-media preservation. PASS.

## M4.3 — Controlled media writes

Status: PASS on GitHub Actions run 34714784136 at commit `3f4e53775ea467f583011aebe5464fe728b149d0`.

- enable a CI-only deterministic write probe only with `ATARISANDBOX_M4_3_CONTROLLED_WRITE=1`
- operate exclusively on the disposable runtime image after real guest boot-sector access
- require a real `media.floppy.write` event through Hatari's `Floppy_WriteSectors` implementation
- require a controlled boot-sector write and `boot_sector=true` classification
- mark qualification-probe evidence with `controlled_test=true`
- bind pre/post runtime-media SHA-256 to the observed write evidence
- verify the immutable source image remains unchanged
- use a one-shot controlled mutation and graceful Hatari shutdown so the changed image is flushed exactly once
- keep networking and writable host shared folders disabled

Exit gate: CI proves a hash-visible controlled write through Hatari's real floppy-write path, correct boot-sector classification, and immutable source preservation. PASS.

## M4.4 — Runtime visual and memory evidence

Status: PASS on GitHub Actions run `34720995579` at commit `db35a3de30dcac0951d75bfd9be9c697ce695c82`.

- deterministic screenshot capture from the harmless EmuTOS runtime
- bounded selected memory snapshot(s)
- SHA-256 identity for every captured evidence object
- manifest references tying screenshot and memory evidence to the runtime session
- strict size/count limits and analysis-directory-only output
- retain deny-by-default networking and host-share policy

Exit gate: CI captures and validates deterministic visual and bounded memory evidence from a harmless Hatari + EmuTOS runtime and uploads a hash-bound evidence bundle. PASS.

## M5 — ASW adapter

Status: PASS on GitHub Actions run `34730495915` at commit `9e162c39eff8bafb5a1c7b1f682c04b5d51f2758`.

- AtariSandbox machine-profile mapping
- ASW ingestion-boundary manifest
- hash-bound runtime manifest
- artifact size/type/path validation
- deny-by-default policy normalization

Exit gate: harmless M4.4 evidence passes the M5 adapter, independent ASW-manifest/hash validation and artifact upload. PASS.

## M6 — Cross-repo harmless E2E

Status: PASS on GitHub Actions run `34735588943` (successful rerun attempt) at AtariSandbox commit `8d708f133677ab431a773e654a58d2a31a745841`.

- ASW checkout
- AtariSandbox checkout/build
- EmuTOS harmless runtime
- evidence generation
- ASW ingestion and hash verification
- evidence artifact upload

Qualified artifact: `atarisandbox-m6-asw-e2e-evidence`, ID `10314297146`, SHA-256 `16dd4c44ab04703f1fad9b7e2bee39847747836e3a56184896471812efbd9bed`.

Exit gate: one GitHub Actions run crosses the real AtariSandbox and ASW repositories, boots harmless EmuTOS, generates AtariSandbox evidence, validates/ingests it through ASW-owned code and uploads the hash-bound cross-repo evidence bundle. PASS.

## M7 — Physical workstation qualification

Status: active milestone; repository-side qualification tooling and runbook are next. Final PASS requires execution on the dedicated physical workstation and cannot be granted by GitHub Actions alone.

- visible ST/STE qualification on the dedicated workstation
- exact local TOS/EmuTOS provenance and hashes
- networking off
- no writable host shares
- disposable runtime state
- cleanup/destruction verification

Exit gate: a physical-workstation qualification run records machine/runtime provenance, ROM identity, deny-by-default isolation, disposable-state preservation and verified cleanup/destruction in a retained qualification bundle.

Only after this gate should controlled real-malware runtime work begin.

## Later scope

Possible later machine profiles include TT and Falcon. They must not be added to the qualified matrix until machine-specific evidence and runtime behavior have their own qualification evidence.
