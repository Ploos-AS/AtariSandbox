# AtariSandbox

**Hatari Malware Analysis Edition**

AtariSandbox is a defensive malware-analysis fork of Hatari for reproducible, instrumented analysis of Atari ST-family software. It is intended as the Atari runtime backend for the multi-platform ASW Core used by Ploos AS.

## M0 status

M0 establishes project identity, provenance, safety boundaries, initial analysis requirements and the roadmap. Upstream Hatari functionality is intentionally kept intact at this stage; malware-analysis instrumentation is added incrementally in later milestones.

Baseline upstream revision at M0: `11964da62914bf232ca84eacf0cedf1d25223e08`.

## Scope

Initial target family:

- Atari ST
- Atari STE

Later profiles may cover TT and Falcon once the initial evidence contract is stable.

The preferred free CI firmware/OS path is **EmuTOS**. Physical qualification may additionally use lawfully obtained original TOS images, with exact hashes recorded per run.

## Analysis contract

AtariSandbox will evolve toward a dedicated analysis mode that emits at minimum:

- `session.json`
- `events.jsonl`

Planned runtime evidence includes:

- exact AtariSandbox/Hatari revision and build identity
- deterministic machine/configuration fingerprint
- CPU register snapshots and selected instruction tracing
- exception/vector activity
- GEMDOS, BIOS and XBIOS observations where practical
- disk and boot-sector read/write activity
- pre/post media hashes
- screenshots and runtime logs
- optional memory snapshots/watchpoints

The event stream will be explicitly versioned. Downstream tools must tolerate unknown future event classes.

## Security defaults

Real samples are hostile input. AtariSandbox is only one defense layer and is not considered a complete host-security boundary.

Default policy for analysis runs:

- guest networking disabled
- no broad writable host filesystem sharing
- disposable writable media/state
- explicit sample ingress and artifact egress
- no signing or publication credentials in the emulator environment
- local-only control/IPC where possible
- exact ROM/TOS/EmuTOS identity recorded
- visible local qualification for physical runtime claims

No public quarantine service may feed samples directly into AtariSandbox. ASW Core remains responsible for verified import, immutable originals, evidence custody and approval gates.

## Relationship to ASW

Canonical intended flow:

```text
verified ASW sample
  -> disposable Atari analysis copy
  -> AtariSandbox
  -> session.json + events.jsonl + runtime artifacts
  -> ASW hash-bound runtime manifest
  -> Atari-specific forensic interpretation
  -> analyst review
  -> research-only candidate
```

A runtime observation is evidence, not an automatic malware verdict or signature-publication authorization.

## Development roadmap

See `docs/ROADMAP.md`.

## Upstream and license

AtariSandbox is derived from **Hatari**. Original Hatari copyright and licensing remain in force. The imported codebase includes `gpl.txt`; modifications to GPL-covered Hatari code remain GPL-compatible.

Upstream project: `https://hatari.tuxfamily.org/`
GitHub mirror used as source lineage: `https://github.com/hatari/hatari`

## Project

Maintained by Ploos AS for defensive malware research and retro-computing security analysis.
