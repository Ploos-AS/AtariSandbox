# M6 — Cross-repo harmless E2E

M6 qualifies the first complete harmless AtariSandbox-to-ASW path across the two real repositories.

The GitHub Actions job checks out both `Ploos-AS/AtariSandbox` and `Ploos-AS/AmiGuard-Signature-Workstation`, builds AtariSandbox, boots the official free EmuTOS 1.4 CI ROM under Hatari, generates M4.4 evidence, creates the M5 hash-bound ASW manifest, and then hands that directory to ASW-owned `tools/asw_atarisandbox.py`.

ASW independently validates the AtariSandbox manifest, deny-by-default policy, paths, object kinds, byte counts and SHA-256 identities before copying retained evidence into the ASW-side evidence directory. The final `asw.atarisandbox.ingestion/1` manifest binds the Atari platform namespace, backend revision, machine profile, ROM identity, source manifests and retained evidence hashes.

No hostile sample is used. Networking and writable host shared folders remain disabled. This milestone does not authorize real-malware execution; that remains gated by M7 physical workstation qualification.

## Exit gate

One GitHub Actions run must complete the real cross-repository AtariSandbox + ASW path, verify the retained evidence hashes from ASW-owned code, and upload the combined evidence bundle.

Status: implementation committed; GitHub Actions qualification pending.
