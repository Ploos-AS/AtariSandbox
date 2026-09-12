# M4.2 — Real floppy media I/O evidence

M4.2 connects AtariSandbox's media evidence stream to Hatari's real sector-level floppy I/O path without modifying upstream `floppy.c` semantics.

## Implementation

On GNU/ELF builds used for qualification, AtariSandbox uses linker wrapping around `Floppy_ReadSectors` and `Floppy_WriteSectors`. Successful operations emit bounded structured events to `core-events.jsonl` when `ATARISANDBOX_MEDIA_IO_LIMIT` is set.

Event schema: `atarisandbox.event/1`

Event types:

- `media.floppy.read`
- `media.floppy.write`

Fields include drive, track, side, sector, count, sector size, and `boot_sector`. A write beginning at track 0, side 0, sector 1 is classified as a boot-sector write.

## Runtime qualification

GitHub Actions builds AtariSandbox with the floppy linker wrappers enabled, downloads the official EmuTOS 1.4 512 KiB ROM, creates a deterministic harmless 720 KiB ST floppy image, copies it to disposable runtime media, and boots real Hatari under Xvfb.

The gate requires:

- at least one real `media.floppy.read` event from Hatari/EmuTOS runtime,
- valid `atarisandbox.event/1` media events,
- bounded evidence collection,
- immutable source-media SHA-256 before and after execution,
- no writable host shared folders,
- networking disabled by the qualification profile.

The write wrapper and boot-sector classifier are present in M4.2. A later controlled guest-write qualification will require an observed real write and an observed harmless boot-sector write on disposable media; M4.2 does not claim those writes occurred merely because the paths are instrumented.

## Safety

The CI image is synthetic and harmless. The original source image is never passed directly to the emulator; Hatari receives only the disposable copy. No malware sample is used.
