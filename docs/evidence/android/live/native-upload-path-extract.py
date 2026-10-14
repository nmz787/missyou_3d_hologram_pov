"""Read-only ELF relocation/registration and bounded AArch64 BL evidence.

This deliberately decodes only direct BL immediates, not general instructions.
The Ghidra dossiers supply decompilation and the RegisterNatives use-site.
"""

from pathlib import Path
import hashlib
import json
import struct


def main():
    binary = Path("analysis/android/libSPCore.so")
    data = binary.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != "20d90219ddf46083844ace9bb225f583f44802d78d05e2f409cd189f0654645b":
        raise ValueError("Selectors require the exact APK library")
    shoff = struct.unpack_from("<Q", data, 40)[0]
    size, count, names_index = struct.unpack_from("<HHH", data, 58)
    headers = [struct.unpack_from("<IIQQQQIIQQ", data, shoff + i * size) for i in range(count)]
    names_header = headers[names_index]
    names = data[names_header[4]:names_header[4] + names_header[5]]

    def cstr(source, offset):
        return source[offset:source.index(b"\0", offset)].decode("utf-8")

    sections = {cstr(names, h[0]): h for h in headers}
    rela = sections[".rela.dyn"]
    relocations = {target: addend for target, info, addend in
                   [struct.unpack_from("<QQq", data, i) for i in range(rela[4], rela[4] + rela[5], 24)]
                   if info & 0xffffffff == 1027}
    table = []
    for index in range(13):
        entry = 0x274360 + index * 24
        name, signature, function = [relocations[entry + x] for x in (0, 8, 16)]
        table.append({"index": index, "entry_elf_vaddr": entry,
                      "name_elf_vaddr": name, "name": cstr(data, name),
                      "signature_elf_vaddr": signature, "jni_signature": cstr(data, signature),
                      "function_elf_vaddr": function,
                      "relocation_type": "R_AARCH64_RELATIVE (1027)",
                      "relocation_targets": [entry, entry + 8, entry + 16]})
    rela = sections[".rela.plt"]
    dynsym, dynstr = sections[".dynsym"], sections[".dynstr"]
    strings = data[dynstr[4]:dynstr[4] + dynstr[5]]
    plt_names = {}
    for index, at in enumerate(range(rela[4], rela[4] + rela[5], 24)):
        _, info, _ = struct.unpack_from("<QQq", data, at)
        symbol = struct.unpack_from("<IBBHQQ", data, dynsym[4] + (info >> 32) * 24)
        plt_names[sections[".plt"][3] + 32 + 16 * index] = cstr(strings, symbol[0])
    worker = data[0xf6e18:0xf6e64]
    calls = []
    for address in range(0xf6e18, 0xf6e64, 4):
        word = struct.unpack_from("<I", data, address)[0]
        if word >> 26 == 0b100101:
            immediate = word & 0x3ffffff
            if immediate & 0x2000000:
                immediate -= 0x4000000
            target = address + immediate * 4
            calls.append({"source_elf_vaddr": address, "instruction_word_hex": f"{word:08x}",
                          "target_elf_vaddr": target, "plt_symbol": plt_names.get(target)})
    output = {"authority": "Direct offline ELF bytes, dynamic relocations, JNI table, and bounded BL decoding",
              "path": str(binary), "member_sha256": digest,
              "jni_method_table_elf_vaddr": 0x274360, "method_count": 13,
              "method_count_basis": "nativeInit Ghidra RegisterNatives argument 0xd",
              "jni_registration_table": table,
              "worker": {"start_elf_vaddr": 0xf6e18, "end_exclusive_elf_vaddr": 0xf6e64,
                         "raw_hex": worker.hex(), "raw_sha256": hashlib.sha256(worker).hexdigest(),
                         "bounds_basis": "async pthread_create worker address and next exported function create_twofish_crypter_for_log",
                         "decoded_direct_calls": calls},
              "limitations": ["Static registration and calls do not independently establish application execution.",
                              "Worker bytes are retained in full; only direct BL instructions are decoded by this script.",
                              "All addresses are original ELF virtual addresses; Ghidra dossiers add a 0x100000 image base."]}
    destination = Path("docs/evidence/android/live/native-upload-path-registration.json")
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print(destination)


if __name__ == "__main__":
    main()
