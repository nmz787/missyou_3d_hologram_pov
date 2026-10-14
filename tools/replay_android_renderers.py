"""Render the APK's extracted Text Ball and Box scripts in offline desktop Chrome.

Requires playwright and Pillow; uses installed Chrome, not an Android runtime.
Templates and their artifact-qualified extraction records live beside the results.
"""
import base64
import hashlib
import io
from importlib.metadata import version as distribution_version
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "docs/evidence/android/features"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    records = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/usr/bin/google-chrome", headless=True,
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
        )
        version = browser.version
        for name in ["text-ball", "box-0", "box-1", "box-2"]:
            page = browser.new_page(viewport={"width": 500, "height": 500}, device_scale_factor=1)
            page.route("**/*", lambda route: route.abort())
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.set_content("<html><body></body></html>")
            page.evaluate("""() => {
                window.probeMessages = [];
                window.ReactNativeWebView = {postMessage(s) {probeMessages.push(JSON.parse(s));}};
            }""")
            if name == "text-ball":
                html_path = FOLDER / "text-ball-360-sphere-html.template.html"
                script_path = FOLDER / "text-ball-360-sphere-script.template.js"
                html = html_path.read_text().replace("{{COLOR}}", "#25fc11")
                page.set_content(html)
                script = script_path.read_text().replace("{{TEXT}}", "HELLO").replace(
                    "{{PLATFORM}}", "android").replace("{{COLOR}}", "#25fc11")
                page.add_script_tag(content=script)
                page.wait_for_function("Number(document.querySelector('li').style.opacity) > 0")
                sources = {path.name: digest(path) for path in [html_path, script_path]}
                substitutions = {"text": "HELLO", "color": "#25fc11", "platform": "android"}
            else:
                template = FOLDER / "spinning-box-renderer-template.html"
                image = FOLDER / "spinning-box-default.jpg"
                data_url = "data:image/jpeg;base64," + base64.b64encode(image.read_bytes()).decode()
                style = int(name[-1])
                html = template.read_text().replace("__TYPE__", str(style)).replace(
                    "__DIST__", "30" if style == 1 else "20").replace(
                    "__IMAGE_SRCS__", json.dumps([data_url] * 6))
                page.set_content(html)
                sources = {path.name: digest(path) for path in [template, image]}
                substitutions = {"type": style, "dist": 30 if style == 1 else 20,
                                 "images": "the packaged default JPEG on all six faces"}
                page.wait_for_function("window.__spinningBoxReady === true")
            page.wait_for_function("typeof window.exportFrames === 'function'")
            page.evaluate("window.pauseAnimation()")
            page.screenshot(path=str(FOLDER / f"browser-{name}-preview.png"))
            page.evaluate("window.exportFrames(200)")
            page.wait_for_function("probeMessages.some(m => m.t === 'd')", timeout=60000)
            messages = page.evaluate("probeMessages")
            frames = [f for m in messages if m.get("t") == "b" for f in m["f"]]
            assert len(frames) == 200
            assert [f["i"] for f in frames] == list(range(200))
            selected, images = [], []
            for index in [0, 50, 100, 150, 199]:
                raw = base64.b64decode(frames[index]["d"].split(",", 1)[1])
                image = Image.open(io.BytesIO(raw)).convert("RGB")
                assert image.size == (720, 720)
                assert sum(ImageStat.Stat(image).mean) > 0, "Unexpected empty rendering"
                out = FOLDER / f"browser-{name}-frame-{index:03}.jpg"
                out.write_bytes(raw)
                selected.append({"index": index, "file": out.name, "bytes": len(raw),
                                 "sha256": digest(out), "size": list(image.size),
                                 "mean_rgb": ImageStat.Stat(image).mean})
                images.append(image)
            differences = [sum(ImageStat.Stat(ImageChops.difference(images[0], image)).mean)
                           for image in images[1:]]
            assert max(differences) > 1, "No observable animation"
            video = FOLDER / f"browser-{name}.mp4"
            command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "image2pipe",
                       "-framerate", "20", "-i", "pipe:0", "-c:v", "libx264", "-preset",
                       "ultrafast", "-crf", "23", "-r", "20", "-threads", "4", "-pix_fmt",
                       "yuv420p", str(video)]
            subprocess.run(command, input=b"".join(base64.b64decode(f["d"].split(",", 1)[1])
                                                  for f in frames), check=True)
            records.append({"renderer": name, "source_sha256": sources,
                            "substitutions": substitutions, "frame_count": len(frames),
                            "batch_sizes": [len(m["f"]) for m in messages if m.get("t") == "b"],
                            "completion": [m for m in messages if m.get("t") == "d"],
                            "selected_frames": selected, "difference_from_first_mean_rgb_sum": differences,
                            "desktop_ffmpeg_video": {"file": video.name, "sha256": digest(video),
                                                     "command": command, "expected_duration_seconds": 10},
                            "javascript_errors": errors})
            assert not errors, errors
            page.close()
        browser.close()
    result = {"evidence_type": "offline execution of extracted APK rendering scripts in desktop Chrome",
              "chrome_version": version, "playwright_version": distribution_version("playwright"),
              "viewport": [500, 500], "network": "all page requests blocked; image inputs are data URLs",
              "limits": ["No Android React Native/WebView runtime execution",
                         "No native encoder, phone media save, or display upload execution",
                         "Desktop fonts and SwiftShader can differ from Android rendering",
                         "Chosen demonstration text and packaged default images, not user content"],
              "results": records}
    (FOLDER / "browser-renderer-replay.json").write_text(json.dumps(result, indent=2) + "\n")
    print("Four extracted renderer variants produced 200 720x720 frames each; pixel statistics retained.")


if __name__ == "__main__":
    main()
