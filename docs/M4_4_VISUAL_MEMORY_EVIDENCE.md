# M4.4 — Runtime visual and memory evidence

M4.4 adds bounded visual and memory-state evidence to the harmless AtariSandbox runtime qualification path.

## Evidence path

The qualifier boots real Hatari with the official free EmuTOS CI ROM and uses Hatari's existing remote-control interface. After a bounded runtime interval it invokes the native `screenshot` and `savemem` shortcuts. The memory-save path is explicitly redirected into the analysis directory; Hatari runs with that directory as its working directory so screenshot output is constrained there as well.

No emulator-core snapshot semantics are replaced by AtariSandbox. M4.4 qualifies Hatari's native screenshot and memory-state capture paths and wraps their outputs in AtariSandbox evidence metadata.

## Evidence contract

`atarisandbox.m4_4.evidence/1` records:

- backend revision and machine profile
- EmuTOS ROM SHA-256
- deny-by-default network/host-share state
- exactly one screenshot object
- exactly one bounded memory snapshot object
- relative analysis-directory path, byte count, and SHA-256 for each object

`atarisandbox.m4_4.qualification/1` records the final PASS/FAIL gate and the SHA-256 of the evidence manifest.

## Bounds and safety

CI uses harmless EmuTOS only. Networking and writable host shared folders remain disabled. Evidence must remain under the dedicated analysis directory. The default qualification limits are 4 MiB for the screenshot and 4 MiB for the memory-state object; exceeding either limit fails closed.

## Exit gate

GitHub Actions must boot real Hatari + EmuTOS, capture a non-empty screenshot and memory-state object through Hatari's native runtime paths, verify their hashes and sizes against the manifest, and upload the complete evidence bundle.

## Qualification result

Status: **PASS**.

- GitHub Actions workflow: `AtariSandbox M4.4`
- run: `34720995579`
- qualified commit: `db35a3de30dcac0951d75bfd9be9c697ce695c82`
- build: PASS
- EmuTOS runtime: PASS
- screenshot capture: PASS
- memory-state capture: PASS
- evidence validation: PASS
- evidence artifact upload: PASS

M4.4 is runtime-qualified. The next roadmap milestone is M5 — ASW adapter.
