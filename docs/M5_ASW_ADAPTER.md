# M5 — ASW adapter

M5 defines the AtariSandbox-to-ASW ingestion boundary. The adapter does not run samples or alter emulator state. It validates an already qualified AtariSandbox evidence directory and emits a small, hash-bound manifest that ASW can ingest.

## Adapter

`tools/atarisandbox_asw_adapter.py` consumes an M4.4 analysis directory and requires:

- `evidence-m4_4.json` with schema `atarisandbox.m4_4.evidence/1`
- `qualification-m4_4.json` with schema `atarisandbox.m4_4.qualification/1` and `result=PASS`
- networking disabled
- writable host shared folders disabled
- every referenced evidence object present under the analysis directory
- size and SHA-256 identity matching the source manifest
- bounded object count and object size
- supported evidence object namespaces only

The adapter emits `asw-manifest.json` with schema `atarisandbox.asw-ingest/1`.

## ASW manifest fields

The manifest carries:

- producer identity (`AtariSandbox`)
- machine profile
- backend revision
- ROM SHA-256
- source evidence manifest name and SHA-256
- normalized deny-by-default runtime policy state
- bounded evidence object list
- relative path, byte count, SHA-256 and kind for every object

Paths are relative to the analysis directory. Any path escaping the analysis directory fails closed. M4.4's string-valued `network` / `host_shared_folders` policy fields are validated as `disabled` and normalized to boolean-disabled fields at the ASW boundary.

## Trust boundary

AtariSandbox owns emulator execution and evidence generation. ASW owns scheduling, sample custody, ingestion, long-term storage and later signature-generation workflows. M5 intentionally keeps that boundary narrow: ASW receives only validated, hash-bound evidence metadata and files.

## Exit gate

CI must generate harmless M4.4 Hatari + EmuTOS evidence, pass it through the M5 adapter, independently verify the ASW manifest and hashes, and upload the resulting evidence bundle.

## Qualification result

Status: **PASS**.

- GitHub Actions workflow: `AtariSandbox M5`
- run: `34730495915`
- qualified commit: `9e162c39eff8bafb5a1c7b1f682c04b5d51f2758`
- harmless M4.4 evidence generation: PASS
- M5 ASW adapter: PASS
- ASW ingestion-manifest validation: PASS
- evidence artifact upload: PASS
- artifact: `atarisandbox-m5-asw-evidence`
- artifact digest: `sha256:1dc0b518369a28799ade1f4bc58b357aeea9a63ec889d25b1eac29a1d05c33cd`

M5 is runtime-qualified. The next roadmap milestone is M6 — cross-repo harmless E2E.
