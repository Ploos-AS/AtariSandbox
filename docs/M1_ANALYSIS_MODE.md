# M1 — Analysis mode foundation

M1 establishes the first stable AtariSandbox evidence boundary without changing normal Hatari behavior.

## Scope

`tools/atarisandbox_run.py` launches a caller-supplied Hatari command without shell interpolation and emits a versioned analysis envelope around the runtime.

Required artifacts:

- `session.json`
- `events.jsonl`

The M1 event stream contains `session.start` and `session.stop`. Later milestones add emulator-native CPU, exception, GEMDOS/BIOS/XBIOS, disk and memory instrumentation while preserving the M1 envelope.

## Environment passed to Hatari

- `ATARISANDBOX_ANALYSIS_DIR`
- `ATARISANDBOX_MACHINE_PROFILE`
- `ATARISANDBOX_CONFIG_FINGERPRINT`

These variables are intentionally compatible with future in-process instrumentation hooks.

## Safety defaults

The session declares external networking and writable host shared folders disabled. M1 does not itself configure Hatari networking or host folders; the ASW caller and future native analysis mode must enforce those declarations before hostile samples are permitted.

No malware samples are used in CI. M1 qualification uses a harmless child process to validate lifecycle and evidence semantics only.

## Qualification gate

M1 passes repository-side qualification when:

1. tests validate schema and lifecycle events;
2. existing evidence cannot be overwritten silently;
3. command execution uses an argv vector, not a shell;
4. GitHub Actions completes the M1 test suite successfully.

M1 is not yet a claim of emulator-native telemetry or guest malware execution. Those begin in M1.1/M2.
