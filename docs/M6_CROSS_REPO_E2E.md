# M6 — Cross-repo harmless E2E

M6 qualifies the first complete harmless AtariSandbox-to-ASW path across the two real repositories.

The GitHub Actions job checks out both `Ploos-AS/AtariSandbox` and `Ploos-AS/AmiGuard-Signature-Workstation`, builds AtariSandbox, boots the official free EmuTOS 1.4 CI ROM under Hatari, generates M4.4 evidence, creates the M5 hash-bound ASW manifest, and then hands that directory to ASW-owned `tools/asw_atarisandbox.py`.

ASW independently validates the AtariSandbox manifest, deny-by-default policy, paths, object kinds, byte counts and SHA-256 identities before copying retained evidence into the ASW-side evidence directory. The final `asw.atarisandbox.ingestion/1` manifest binds the Atari platform namespace, backend revision, machine profile, ROM identity, source manifests and retained evidence hashes.

No hostile sample is used. Networking and writable host shared folders remain disabled. This milestone does not authorize real-malware execution; that remains gated by M7 physical workstation qualification.

## Exit gate

One GitHub Actions run must complete the real cross-repository AtariSandbox + ASW path, verify the retained evidence hashes from ASW-owned code, and upload the combined evidence bundle.

## Qualification

Status: **PASS**.

- GitHub Actions run: `34735588943` (successful rerun attempt)
- AtariSandbox commit: `8d708f133677ab431a773e654a58d2a31a745841`
- ASW ingestion fix used by the successful cross-repo run: `d66fad09030082691d3d1c0aceb67ea3ca610b3b`
- Evidence artifact: `atarisandbox-m6-asw-e2e-evidence`
- Artifact ID: `10314297146`
- Artifact size: `745938` bytes
- Artifact SHA-256: `16dd4c44ab04703f1fad9b7e2bee39847747836e3a56184896471812efbd9bed`

The successful run passed AtariSandbox build, EmuTOS runtime, evidence generation, ASW-owned ingestion, independent cross-repository hash verification and evidence upload.

M6 exit gate: **PASS**.

Next: M7 physical workstation qualification.
