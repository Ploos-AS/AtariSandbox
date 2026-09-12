# M1.1 — Hatari + EmuTOS runtime qualification

M1.1 upgrades AtariSandbox from a host-side evidence contract to a real Atari ST runtime qualification using Hatari and the free EmuTOS ROM.

## Scope

The GitHub Actions gate must:

- build Hatari from this repository on Ubuntu 24.04;
- obtain an official EmuTOS 512 KiB ROM image at runtime;
- record the exact EmuTOS SHA-256 used by the run;
- launch Hatari under Xvfb with an ST profile;
- keep networking and host shared folders disabled;
- run long enough to prove a live guest runtime;
- terminate Hatari in a bounded and controlled way;
- produce AtariSandbox `session.json` and `events.jsonl` evidence;
- retain the Hatari log and ROM hash as qualification artifacts.

No proprietary Atari TOS image is required for this gate. EmuTOS is the canonical free CI firmware for M1.1.

## Qualification profile

Initial CI profile:

- machine: Atari ST
- CPU: 68000
- RAM: 1 MiB
- ROM: EmuTOS 512 KiB
- display: SDL/X11 under Xvfb
- networking: disabled
- GEMDOS host drive/shared folder: disabled
- writable guest media: none required for this boot gate

## PASS criteria

M1.1 may be marked PASS only when the GitHub Actions job proves all of the following:

1. the repository builds a runnable Hatari binary;
2. the downloaded ROM is non-empty and its SHA-256 is recorded;
3. Hatari starts with the requested ST/EmuTOS profile;
4. the process remains alive for the observation interval instead of exiting immediately;
5. AtariSandbox emits valid `atarisandbox.session/1` and `atarisandbox.event/1` evidence;
6. the lifecycle closes with `session.stop`;
7. the qualification artifacts are uploaded.

A CI PASS here is a harmless free-firmware runtime qualification. It is not yet hostile-sample qualification.
