# JNI registration reaches the recovered legacy native sender

This follow-up is entirely offline. It reads the supplied APK's extracted
`lib/arm64-v8a/libSPCore.so` and retained evidence. It does not execute the APK
or library, access ADB, contact the display, or modify its files. The analyzed
library SHA-256 remains
`20d90219ddf46083844ace9bb225f583f44802d78d05e2f409cd189f0654645b`.

The static JNI upload path is resolved. There is no alternate packet generator
between the registered Java method and the previously analyzed native sender:

```text
MiddleNativeModule.handleCmd(MEDIA_FUNC_UPLOAD)
  → NativeCore.oldDevUploadFile(GBK bytes, byte count, path, callbacks)
  → registered native wrapper at ELF 0xf0bac
  → old_dev_tcp_upload_async at ELF 0xf6d38
  → pthread worker at ELF 0xf6e18
  → old_dev_tcp_upload at ELF 0xf64e0
```

This resolves the static call path for the legacy upload branch; it does not
independently observe which UI branch a running app selects.

## Exact registration and callback preparation

`Java_com_sp_core_jni_NativeCore_nativeInit`, ELF `0xf02f0`, invokes
`RegisterNatives` with table address `0x274360` and **13 methods**. The tenth
entry (zero-based index 9) at `0x274438` is exactly:

```text
name:      oldDevUploadFile
signature: ([BILjava/lang/String;Lcom/sp/core/bean/OnFun2Listener;Lcom/sp/core/bean/OnFun2Listener;)V
function:  0xf0bac
```

All three fields are established by original `R_AARCH64_RELATIVE`
relocation addends. [registration.json](native-upload-path-registration.json)
preserves all 13 entries, exact addresses, the selected worker bytes and hash,
and its decoded direct calls. The reproduction script only decodes bounded
AArch64 `BL` immediates; it does not execute code.

The [JNI wrapper dossier](native-upload-path-jni-wrapper.json), Evidence
`ev_c790a93bb3ac0304f957b9207bcc168e9f5173769330b5f25cd24d230c16ccf0`,
shows that wrapper acquiring callback global references, copying the supplied
filename bytes, obtaining the path's Java string bytes, and directly calling
`old_dev_tcp_upload_async`. It does not edit the framing globals or build a
different upload packet. Readable [pseudocode](native-upload-path-jni-wrapper.c.txt)
and [assembly](native-upload-path-jni-wrapper.asm.txt) accompany the dossier.

The [async dossier](native-upload-path-async.json), Evidence
`ev_73a1b71ec8b2080a695ab010f89e8e5043ddc2264d8e81ee5d888f2ce9585609`,
shows `strdup` of filename and path, copying four callback/context pointers,
then `pthread_create` of worker `0xf6e18` and detaching the thread. It does not
rewrite framing globals. The worker's original instruction at ELF `0xf6e38`
is word `940593a2`, a direct `BL` to the PLT entry for `old_dev_tcp_upload`.
Its remaining direct calls free the copied arguments. This connects the
Java-visible method to the exact sender already reconstructed in
[legacy-upload-findings.md](../comms/legacy-upload-findings.md).

One unrelated boundary concern is visible in the wrapper: it allocates exactly
the supplied filename-byte count, then copies that many bytes without an
explicit trailing NUL. The async wrapper subsequently calls `strdup` on that
buffer. Static code therefore does not establish correctly terminated name
storage in that wrapper. This observation does not establish a particular
failure on the user's phone; the standalone native sender uses its caller's
name buffer instead.

## What native initialization actually does

The complete [nativeInit dossier](native-upload-path-native-init.json), Evidence
`ev_01a623c7c3a89388f1fe665a3dd8787e32307c3f19d086a66b46d1d339fb89ae`,
shows these operations:

- Obtain the logging string and call `init_f_log`.
- Call `check_access` with the Java VM, JNI environment, and Java context.
- Initialize mutex/JNI bookkeeping and cache `NativeCore`, `OnFun2Listener`,
  and its `onFun2(ZLjava/lang/String;)V` callback method.
- Register the 13-method native table; release/clear references on failure.

The body contains **no write to FILE_INFO_HEADER, FILE_INFO_TAIL, CHUNK_HEADER,
or CHUNK_TAIL**. Its actual JNI/mutex writes target other globals around
`0x274898`, not the framing arrays beginning at `0x274498`.
The transitive implementations of `init_f_log` and `check_access` were not
individually decompiled in this follow-up, so this body alone is not a blanket
claim about every possible indirect initializer effect.

The complete [JNI_OnLoad dossier](native-upload-path-jni-onload.json), Evidence
`ev_ac0d77b0c894096c627111a3d880c4621715b383e3577117058c6d48c786555b`,
contains only storing the Java VM and returning JNI version `0x10004` (1.4).
It has no header transformation or packet setup.

Calling `dlopen` alone does not run the Java `nativeInit` method. NativeInit
sets up logging and JNI callbacks; a standalone harness that calls the exported
sender with its own C callbacks follows a different initialization route.
This follow-up did not establish logging safety for that route. The separately
reported root-agent harness interposes `f_log`; its live execution evidence is
outside this static pass.

## Writable framing globals: observed references, not an immutability claim

The four arrays reside in writable ELF data. To check the proposed
initialization-transform explanation, one retained Ghidra session queried
direct cross-references to **every byte** of their 34-byte combined range.
[header-reference-summary.json](native-upload-path-header-reference-summary.json)
links all returned evidence IDs and the sender/ACK references with read/write
flags.

The resolved instruction references are exclusively **READ** references:

| Ghidra instruction | Original ELF data target | Meaning |
| --- | --- | --- |
| `0x1f6624`, `0x1f6628` | `0x274498`, `0x27449c` | Read file-info header |
| `0x1f6654` | `0x27449e` | Read file-info tail |
| `0x1f6934`, `0x1f6938` | `0x2744a6`, `0x2744ae` | Read chunk header |
| `0x1f694c`, `0x1f6950` | `0x2744af`, `0x2744b6` | Read chunk tail |
| `0x1f6c9c` | `0x27449e` | Read expected ACK suffix |

The other references are GOT/data pointer references. No direct WRITE
reference to these arrays was found in the fully analyzed library. This
supports the on-disk ASCII `d31d88JMP` and `000a4a8c2e3` values as the static
sender's framing; it supplies **no evidence of a JNI-init rewrite**. An
arbitrary or address-derived indirect write can lack a direct cross-reference,
so static negative results do not prove immutable runtime memory.

## ACK middle fields have no recovered success/failure interpretation

The previously retained complete
[ACK helper](../comms/legacy-upload-native-ack-function.json) checks only the
first six ASCII bytes, a minimum accumulated length of 14, and the last eight
ASCII bytes. It does not inspect middle `DEJ`, `ffff`, or `0000` bytes. Thus
both `d30d88DEJffffa4a8c2e3` and `d30d88DEJ0000a4a8c2e3` meet that helper's
acceptance rule. Interpreting `0000` as firmware rejection is still an
inference requiring other evidence. The native result `0` alone cannot settle
whether the display persisted the file; the sender also ignores incomplete
completion-marker sending as already documented.

No new checksum, sequence field, or alternate `JMP` encoding appears in the
resolved JNI/async path. The device's persistence failure and any firmware
meaning of the middle fields remain outside the evidence available in this
offline trace.

## Reproduction and coverage

```bash
python3 docs/evidence/android/live/native-upload-path-extract.py
python3 docs/evidence/android/live/native-upload-path-session.py
```

The second command uses a private REA MCP stdio server and **one Ghidra
import** for nativeInit, JNI_OnLoad, the async method, and every framing-byte
xref. It closes that ephemeral analysis session. It launches analysis tools,
not the selected library, APK, or Android app. Exact provider parameters,
tool schemas, REA evidence, raw assembly, byte hashes, and limitations are
retained beside this report. Original ELF addresses differ from this Ghidra
session's default addresses by the recorded `0x100000` analysis image base.
