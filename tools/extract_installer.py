"""Recover the managed converter from the supplied Advanced Installer SFX.

Requires py7zr. Checks exact installer/application identities and lets py7zr
verify member CRCs. Does not run the installer or modify its bytes.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path

import py7zr

INSTALLER_SHA256 = "8bee60df3fe0b039dff1633999b1ae23e20663d0799e62f040651fed97ac2e07"
APPLICATION_SHA256 = "678a03614e6f25819c15a2a5d90d7637fddf79f12efd38f9d924482af27868be"
OFFSET = 0x252E00
LENGTH = 0x2459225


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installer", type=Path)
    parser.add_argument("--output", type=Path, default=Path("analysis/application"))
    args = parser.parse_args()
    original = args.installer.read_bytes()
    if hashlib.sha256(original).hexdigest() != INSTALLER_SHA256:
        parser.error("This extractor is specific to the supplied 5DDisplayer 1.0.2 installer SHA-256")
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    if (output / "5DDisplayer.exe").exists():
        parser.error("Extracted application already exists; choose a new output directory")
    embedded = original[OFFSET:OFFSET + LENGTH]
    restored = bytes(x ^ 255 for x in embedded[:512]) + embedded[512:]
    with py7zr.SevenZipFile(io.BytesIO(restored)) as archive:
        members = archive.getnames()
        archive.extract(path=output, targets=["5DDisplayer.exe", "5DDisplayer.exe.config"])
    application_hash = hashlib.sha256((output / "5DDisplayer.exe").read_bytes()).hexdigest()
    if application_hash != APPLICATION_SHA256:
        raise ValueError("Extracted application SHA-256 mismatch")
    evidence = {
        "installer_sha256": INSTALLER_SHA256, "installer_bytes": len(original),
        "archive_file_offset": OFFSET, "archive_bytes": LENGTH,
        "archive_transform": "XOR the first 512 bytes with 0xff; leave the remaining bytes unchanged",
        "embedded_archive_sha256": hashlib.sha256(embedded).hexdigest(),
        "restored_archive_sha256": hashlib.sha256(restored).hexdigest(), "archive_members": members,
        "application_sha256": application_hash, "application_bytes": (output / "5DDisplayer.exe").stat().st_size,
    }
    (output / "extraction.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
