# M4.3 — Controlled media writes

M4.3 closes the write-side gap left deliberately open by M4.2. It exercises Hatari's real `Floppy_WriteSectors` path against a disposable, harmless ST image and requires structured evidence for a boot-sector write.

## Safety model

The probe is disabled by default and only enabled when `ATARISANDBOX_M4_3_CONTROLLED_WRITE=1` is supplied by the qualification harness. CI uses deterministic synthetic media, EmuTOS, no networking, and no writable host shared folders. The original source image is never mounted in Hatari; only a disposable copy is used at runtime.

## Evidence

The existing `atarisandbox.event/1` media events gain a `controlled_test` boolean. M4.3 requires a successful `media.floppy.write` event with `controlled_test=true`, a write beginning at track 0 / side 0 / sector 1 with `boot_sector=true`, unchanged source-media SHA-256, and changed runtime-media SHA-256.

The qualification verdict uses `atarisandbox.m4_3.qualification/1` and records pre/post hashes plus read, write, controlled-write and controlled boot-sector-write counts.

## Exit gate

GitHub Actions must prove that the harmless runtime reaches the real Hatari floppy-write implementation, classifies the controlled boot-sector write, persists a hash-visible change only to disposable runtime media, and leaves the immutable source image unchanged.

This milestone is a deterministic CI qualification probe, not a malware sample and not a general-purpose mechanism for modifying user media. The environment gate remains off in normal AtariSandbox runs.
