# AtariSandbox safety and trust boundary

AtariSandbox is a defensive malware-analysis emulator fork. It processes potentially hostile Atari software and must be operated as part of a layered containment design.

## Trust boundary

The emulator process is **not** a sufficient standalone sandbox. A malformed or malicious guest sample could exploit emulator bugs or unsafe integration features. Production analysis therefore requires host-level isolation in addition to AtariSandbox's own analysis defaults.

## Required defaults

- external guest networking disabled
- no broad writable host filesystem exposure
- disposable writable disk/media state
- explicit verified sample ingress
- explicit artifact egress
- no secrets, signing keys or publication credentials in the runtime environment
- exact emulator/ROM/OS identity captured in evidence
- bounded runtime, evidence and trace sizes

## Sample custody

AtariSandbox does not fetch samples from public services. ASW Core owns verified import, SHA-256 identity, immutable originals, analyst queue state, evidence custody and release approval.

Samples should enter AtariSandbox only as disposable, hash-bound analysis copies. The original must remain unchanged.

## CI policy

GitHub Actions qualification must use harmless fixtures and freely distributable boot/runtime assets such as EmuTOS. Real malware and proprietary TOS images must not be stored in the repository or CI artifacts.

## Evidence semantics

Generated events and forensic observations are evidence, not malware verdicts. Detection signatures or public releases require separate analyst review and qualification.
