# M3.1 — Real Atari OS/API Runtime Qualification

M3.1 turns the repository-side M3 trace contract into a real Hatari + EmuTOS runtime gate.

## Runtime

The GitHub Actions qualification builds AtariSandbox from the repository, downloads the official EmuTOS 1.4 512 KiB ROM package, and launches an ST/68000 profile under Xvfb through the existing AtariSandbox lifecycle runner.

The runtime enables Hatari trace classes:

- `gemdos`
- `bios`
- `xbios`

Networking and host shared folders remain disabled by the AtariSandbox analysis contract. The ROM is external to the repository and its SHA-256 is retained in the evidence directory.

## Evidence

The qualifier retains:

- `session.json`
- `events.jsonl`
- `hatari.log`
- `hatari-os-trace.log`
- `os-events.jsonl`
- `emutos.sha256`
- `qualification-m3_1.json`

The structured event stream uses `atarisandbox.event/1` and requires at least one real runtime event for each of GEMDOS, BIOS and XBIOS before M3.1 can PASS.

Trace conversion remains bounded to 16 MiB and 4096 structured events. The raw Hatari trace is retained beside the normalized event stream so downstream tooling can verify or reinterpret the original diagnostics.

## Qualification boundary

A green repository-side M3 parser test is not sufficient for M3.1. PASS requires a real EmuTOS boot in Hatari and real emulator-generated OS/API traces.

This is still a harmless CI qualification. No malware sample is introduced into the guest.
