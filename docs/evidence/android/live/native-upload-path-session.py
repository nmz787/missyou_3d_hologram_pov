"""Use one private REA MCP stdio session for offline native upload traces.

This launches only analysis tools; it never executes the APK/library or opens
a device/network connection. Explicit paths match the existing local tools.
"""

import json
import os
from pathlib import Path
import subprocess


ROOT = Path("/home/nathan/git/5d_pov")
OUT = ROOT / "docs/evidence/android/live"
NODE = "/home/nathan/.nvm/versions/node/v24.21.0/bin/node"
REA = "/home/nathan/.npm/_npx/af752b90495482d7/node_modules/rea-agents/scripts/rea.mjs"


def main():
    env = dict(os.environ)
    env["JAVA_HOME"] = str(ROOT / "tools/java/jdk-25.0.4.1+1")
    env["GHIDRA_INSTALL_DIR"] = str(ROOT / "tools/ghidra/ghidra_12.1.4_PUBLIC")
    OUT.mkdir(parents=True, exist_ok=True)
    with (ROOT / "analysis/android/native-upload-path-session.log").open("w") as log:
        proc = subprocess.Popen([NODE, REA, "--mcp"], cwd=ROOT, env=env,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log,
                                text=True)
        request_id = 0

        def rpc(method, params):
            nonlocal request_id
            request_id += 1
            proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": request_id,
                                         "method": method, "params": params}) + "\n")
            proc.stdin.flush()
            while True:
                line = proc.stdout.readline()
                if not line:
                    raise RuntimeError("REA stdio server exited")
                response = json.loads(line)
                if response.get("id") == request_id:
                    if "error" in response:
                        raise RuntimeError(response["error"])
                    return response["result"]

        def call(name, args, label):
            result = rpc("tools/call", {"name": name, "arguments": args})
            (OUT / f"native-upload-path-{label}.mcp.json").write_text(json.dumps(result, indent=2) + "\n")
            evidence = result.get("structuredContent")
            if evidence is None:
                items = [x["text"] for x in result.get("content", []) if x.get("type") == "text"]
                if len(items) == 1:
                    try:
                        evidence = json.loads(items[0])
                    except ValueError:
                        pass
            if evidence is not None:
                (OUT / f"native-upload-path-{label}.json").write_text(json.dumps(evidence, indent=2) + "\n")
            print(label, "saved", "error" if result.get("isError") else "ok", flush=True)
            return evidence

        try:
            rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                               "clientInfo": {"name": "offline-native-upload-trace", "version": "1"}})
            proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
            proc.stdin.flush()
            catalog = rpc("tools/list", {})
            needed = {"open_binary", "analyze_function", "xrefs", "close_binary", "inspect_native_instruction"}
            selected = [t for t in catalog["tools"] if t["name"] in needed]
            (OUT / "native-upload-path-tool-schemas.json").write_text(json.dumps(selected, indent=2) + "\n")
            if {t["name"] for t in selected} != needed:
                raise RuntimeError("Required tools not in current REA catalog")
            call("open_binary", {"path": str(ROOT / "analysis/android/libSPCore.so"), "provider_id": "ghidra"}, "open")
            call("analyze_function", {"procedure": "0x1f02f0"}, "native-init")
            call("analyze_function", {"procedure": "0x1f04b4"}, "jni-onload")
            call("analyze_function", {"procedure": "0x1f6d38"}, "async")
            for name, start, size in [("file-info-header", 0x374498, 6), ("file-info-tail", 0x37449e, 8),
                                      ("chunk-header", 0x3744a6, 9), ("chunk-tail", 0x3744af, 11)]:
                for offset in range(size):
                    call("xrefs", {"address": hex(start + offset)}, f"xref-{name}-{offset}")
        finally:
            try:
                call("close_binary", {}, "close")
            finally:
                proc.stdin.close()
                proc.terminate()
                proc.wait(timeout=30)


if __name__ == "__main__":
    main()
