# M4.1 — Media identity and disposable runtime state

M4.1 establishes the first AtariSandbox media/persistence evidence contract without introducing malware or writable host media into CI.

The qualification uses deterministic harmless test media. The original image is treated as immutable evidence. AtariSandbox creates a disposable runtime copy, records SHA-256 before and after execution, and verifies that any controlled change is confined to that disposable copy.

## Evidence

`media.json` uses schema `atarisandbox.media/1` and records source/runtime names, sizes, pre/post SHA-256 values, source immutability, runtime disposability, and whether runtime media changed.

`qualification-m4_1.json` uses schema `atarisandbox.m4_1.qualification/1` and records the backend revision plus the qualification verdict.

## Safety boundary

M4.1 uses only generated harmless media. It does not execute malware, does not require networking, and does not expose writable host shares. The source image must remain byte-identical after qualification.

## Exit gate

CI passes only when the immutable source hash is unchanged, the disposable runtime copy begins identical to the source, the controlled runtime-copy change is observable through a different post-run SHA-256, and the evidence schemas validate.

M4.2 can build on this contract by connecting real Hatari floppy/HDD read/write observations and boot-sector write classification to the hash-bound disposable media.
