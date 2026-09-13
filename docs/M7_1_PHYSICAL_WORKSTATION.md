# M7.1 — Physical workstation qualification

Status: repository-side tooling implemented; physical qualification pending.

M7.1 moves AtariSandbox from CI-only harmless qualification to the dedicated physical analysis workstation. It remains a harmless qualification milestone: **do not use a real malware sample for M7.1**.

## Required workstation state

- AtariSandbox built from a recorded Git commit.
- Visible Hatari ST/STE session; do not qualify headless-only execution.
- A known ROM with local provenance. EmuTOS is suitable; a legally owned TOS ROM may also be recorded locally.
- Networking disabled before the emulator is launched.
- No writable host shared folders exposed to the guest.
- Source media kept immutable.
- Runtime media created as a disposable copy.
- Existing AtariSandbox evidence retained outside the disposable guest state.

## Qualification procedure

1. Record the repository HEAD and workstation identity.
2. Hash the selected ROM and immutable source media before launch.
3. Create a disposable runtime-media copy from the source media.
4. Start AtariSandbox visibly with networking disabled and no writable host shares.
5. Boot the harmless ST/STE qualification environment and generate normal AtariSandbox evidence.
6. Stop AtariSandbox cleanly.
7. Preserve the evidence directory, but destroy the disposable runtime-media copy.
8. Run `tools/qualify_m7_1.py` only after cleanup.

Example:

```sh
python3 tools/qualify_m7_1.py \
  --repo . \
  --rom /path/to/emutos-512k.rom \
  --rom-label EmuTOS-1.4 \
  --source-media /path/to/source.st \
  --runtime-media /tmp/atarisandbox-m7/runtime.st \
  --evidence-dir /path/to/retained/evidence \
  --output /path/to/retained/evidence/m7_1-qualification.json \
  --machine-profile st \
  --operator-confirm-visible \
  --operator-confirm-network-off \
  --operator-confirm-no-writable-host-shares \
  --operator-confirm-runtime-destroyed
```

The collector is deliberately fail-closed. `--operator-confirm-runtime-destroyed` is not enough by itself: the runtime-media path must actually be absent when the collector runs.

## Evidence contract

The output schema is `atarisandbox.m7_1.qualification/1`. It records:

- AtariSandbox repository revision;
- physical workstation OS/machine identity;
- machine profile;
- ROM label and SHA-256;
- immutable source-media SHA-256;
- whether disposable runtime media still exists after cleanup;
- operator isolation confirmations;
- retained AtariSandbox evidence file sizes and SHA-256 identities;
- final PASS/FAIL verdict.

At least two core evidence objects among `session.json`, `events.jsonl`, and `asw-manifest.json` must be present.

## Exit gate

M7.1 PASS requires a retained qualification bundle from the dedicated physical workstation proving visible execution, ROM/source provenance, networking off, no writable host shares, retained evidence, and actual destruction of disposable runtime media.

A GitHub Actions run can test the collector itself later, but **cannot grant M7.1 PASS**. The authoritative verdict must come from the physical workstation.

No controlled real-malware execution is authorized until the full M7 physical-workstation gate is passed.
