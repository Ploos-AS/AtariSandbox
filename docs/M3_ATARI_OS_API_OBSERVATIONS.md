# M3 — Atari OS/API observations

M3 converts Hatari's existing operating-system trace output into the versioned AtariSandbox evidence stream without making the upstream diagnostic text itself part of the stable API.

## Scope

Initial event classes:

- `os.gemdos.call`
- `os.bios.call`
- `os.xbios.call`

Every event uses schema `atarisandbox.event/1`, records `source=hatari-os-trace`, preserves a bounded copy of the original Hatari line in `raw`, and identifies the API family. Where the upstream line exposes them, the adapter also records call number, symbolic call name, path, and an operation class.

GEMDOS process calls such as `Pexec`/`Pterm*` are tagged `operation_class=process`. File and directory calls such as `Fopen`, `Fcreate`, `Fread`, `Fwrite`, `Fdelete`, `Frename`, `Fsfirst`, `Fsnext`, `Dcreate`, `Ddelete`, and path operations are tagged `operation_class=filesystem`.

## Safety and bounds

The adapter is post-processing only. It does not add host filesystem sharing or guest networking. It fails closed when the input trace exceeds the configured byte limit or when the emitted event count exceeds the configured event limit. The retained raw line is truncated to a fixed maximum length.

Default limits are:

- trace input: 16 MiB
- structured OS events: 4096
- retained raw line: 4096 characters

These limits are intentionally conservative and may be tightened by the ASW adapter.

## Qualification model

M3 repository qualification verifies that the Hatari source exposes the `gemdos`, `bios`, and `xbios` trace classes, tests deterministic parsing/classification, and exercises the bounded command-line converter. Synthetic trace lines are used for parser qualification; this does not by itself claim a real EmuTOS OS-call runtime capture.

A later M3.1 runtime gate must boot the real Hatari + EmuTOS CI profile, enable the relevant Hatari OS trace classes, produce non-empty structured evidence from the emulator runtime, and preserve the M1/M2 deny-by-default lifecycle and evidence constraints.
