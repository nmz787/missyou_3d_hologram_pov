# Encoder regression fixtures

`original-replay.json` records deterministic output hashes and headers from
isolated original conversion methods for all eleven profiles. `luts.json`
contains the gamma and header lookup tables. These small fixtures let tests
run without vendor binaries or analysis tools.

Extraction and replay code, original identities and full findings are preserved
on the `reverse-engineering` branch. Fixture values are retained unchanged;
the original machine-specific assembly path was omitted.
