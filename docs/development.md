# Reverse-engineering archive

This branch preserves the investigation and reconstruction of 5DDisplayer and
5D-Holo Android. The `main` branch provides the end-user CLI and usage guide.
Historical findings can contain original machine paths, device identifiers and
personal test filenames; they are retained here as evidence, not recommended
application defaults.

## What is preserved

| Location | Purpose | Origin |
| --- | --- | --- |
| `povbin/`, `tests/` | Working implementation and regression tests | Project source |
| `docs/*.md`, evidence `*-findings.md` | Interpretation, conclusions and limitations | Analyst-authored findings |
| `docs/evidence/` JSON, CIL, HASM, pseudocode and assembly | Artifact identities, extracted instructions, REA records, replay outputs and live observations | Generated/extracted evidence; not original application source |
| `tools/`, evidence extraction/replay scripts | Reproduce extraction, select relevant code and verify findings | Project analysis utilities |

The original APK/installer, extracted application/bytecode/native binaries and
full generated Hermes dumps remain **local inputs**, excluded from this branch.
Their identities and extraction steps are recorded in the reports and manifests.
Focused code excerpts retain original offsets and hashes, so findings remain
traceable without storing vendor packages in Git history.

The Windows installer is106,498,403bytes and the Android APK is about73MiB.
GitHub blocks ordinary Git files above100MiB and warns above50MiB; see
[GitHub's file limits](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).
No Git LFS storage or billing is configured. Small binary notification captures
and generated renderer samples are retained as supporting evidence.

SDK/JDK/Ghidra/JADX installations, Python environments, compiler caches,
duplicate working outputs and personal source/export videos are also not
versioned. None is required to run the CLI.

For reproduction, restore the original packages locally, extract the installer
with `tools/extract_installer.py`, and extract `assets/index.android.bundle` and
`lib/arm64-v8a/libSPCore.so` from the APK into `analysis/android/`. The Hermes
selection scripts additionally expect `bundle.hasm` and `bundle.pseudo.js`,
generated using hermes-dec0.1.6 as described in `docs/android.md`.

## Navigation and reproduction

- `docs/format.md`: desktop conversion and BIN layout.
- `docs/android.md`: device families and missing-list investigation.
- `docs/android-protocol.md`: discovery and both communication families.
- `docs/android-features.md`: the APK's rendering/generation features.
- `docs/evidence/android/live/device-findings.md`: authorized device experiments.
- `tools/verify_android_comms_evidence.py`: hashes and original instruction ranges.
- `tools/verify_android_feature_evidence.py`: rendering-feature evidence ranges.
- `tools/verify_device_evidence.py`: native packet comparison and recorded live results.

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tools/verify_android_comms_evidence.py
.venv/bin/python tools/verify_android_feature_evidence.py
```

Analysis providers need their separately installed tooling; refer to individual
reports for versions and commands. The live evidence verifier also requires the
original local `cd.bin` comparison clip; its digest is recorded in the evidence
index. Running these verifiers does not connect to or mutate a display.

To inspect this branch without disturbing an end-user checkout:

```bash
git worktree add ../povbin-research reverse-engineering
```
