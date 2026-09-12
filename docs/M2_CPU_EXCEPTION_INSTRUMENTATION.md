# M2 — CPU and exception instrumentation

M2 adds bounded CPU-oriented evidence on top of the M1/M1.1 session lifecycle.

## Evidence classes

AtariSandbox keeps the existing `atarisandbox.event/1` envelope and adds two event types:

- `cpu.snapshot`
- `cpu.exception`

A CPU snapshot may contain `pc`, `sr`, and a `registers` object containing any observed `d0`–`d7` and `a0`–`a7` values. A complete periodic snapshot target contains all sixteen general registers plus PC and SR.

An exception event records the observed vector number and, when available from the same Hatari diagnostic record, PC, SR and registers.

The original upstream Hatari diagnostic line is retained in `raw` for provenance and parser troubleshooting. Downstream consumers must treat `raw` as untrusted text.

## Bounded conversion

`tools/atarisandbox_trace_events.py` converts selected Hatari CPU/exception diagnostics into JSONL events. Conversion fails closed when either bound is exceeded:

- default maximum input trace: 16 MiB
- default maximum converted events: 4096
- maximum retained raw diagnostic line: 4096 characters

Both the trace-size and event-count limits are configurable downward or upward by the qualification harness, but an analysis profile must always define finite bounds.

The converter never executes trace content and never invokes a shell.

## Runtime strategy

Hatari already exposes the trace classes `cpu_regs`, `cpu_disasm` and `cpu_exception`. M2 uses those upstream facilities as evidence sources while keeping AtariSandbox's JSONL contract independent of Hatari's text format.

The implementation is intentionally split:

1. bounded, tested Hatari-text to AtariSandbox-event conversion;
2. controlled runtime sampling/trace activation;
3. GitHub EmuTOS qualification of real generated CPU evidence.

This prevents an unbounded per-instruction trace from becoming an accidental disk-exhaustion path.

## Qualification gates

Repository-side M2 foundation requires:

- parser tests for full 68000 register snapshots;
- exception/vector event tests;
- trace byte limit test;
- event count limit test;
- raw-line bound test;
- confirmation that the imported Hatari source still exposes the required CPU trace classes.

Full M2 runtime qualification additionally requires a harmless EmuTOS boot that produces real CPU evidence while preserving the already-qualified M1.1 lifecycle and network/share deny defaults.

Until that runtime gate is green, M2 must be described as implemented repository-side, not runtime-qualified.
