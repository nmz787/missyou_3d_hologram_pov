from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import errno

from povbin.codec import AUDIO_BYTES, PROFILES, TRAILER_BYTES
from povbin.media import convert_video, inspect_file


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class VideoIntegration(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.root = Path(self.work.name)
        self.source = self.root / "clip with spaces.mkv"
        subprocess.run([
            "ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=96x64:rate=30:duration=0.4",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=32000:duration=0.4",
            "-c:v", "ffv1", "-c:a", "pcm_u8", "-shortest", str(self.source),
        ], check=True, capture_output=True)

    def tearDown(self):
        self.work.cleanup()

    def test_video_frame_boundaries_audio_and_trailer(self):
        output = self.root / "clip.bin"
        result = convert_video(self.source, output, device_type=1, nonce=b"\x01\x02")
        self.assertEqual(result["frames"], 8)
        self.assertTrue(result["audio"])
        self.assertEqual(output.stat().st_size, 856 + 8 * PROFILES[1].frame_bytes + TRAILER_BYTES)
        info = inspect_file(output, 1)
        self.assertEqual(info["candidates"][0]["frames"], 8)
        expected = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", str(self.source),
                                   "-map", "0:a:0", "-f", "u8", "-ac", "1", "-ar", "32000", "pipe:1"],
                                  capture_output=True, check=True).stdout
        data = output.read_bytes()
        actual = b"".join(data[856 + i * PROFILES[1].frame_bytes + PROFILES[1].video_bytes:
                               856 + (i + 1) * PROFILES[1].frame_bytes] for i in range(8))
        self.assertEqual(actual, expected[:8 * AUDIO_BYTES])
        self.assertEqual(data[-TRAILER_BYTES:], bytes(TRAILER_BYTES))
        with self.assertRaises(ValueError):
            inspect_file(output, 2)

    def test_no_audio_trim_and_overwrite_protection(self):
        output = self.root / "clip.bin"
        result = convert_video(self.source, output, device_type=7, start=0.1, duration=0.2, audio=False)
        self.assertEqual(result["frames"], 4)
        data = output.read_bytes()
        begin = result["header_bytes"]
        for i in range(4):
            offset = begin + i * PROFILES[7].frame_bytes + PROFILES[7].video_bytes
            self.assertEqual(data[offset:offset + AUDIO_BYTES], bytes(AUDIO_BYTES))
        with self.assertRaises(ValueError):
            convert_video(self.source, output, device_type=7)
        self.assertEqual(output.read_bytes(), data)
        with self.assertRaises(ValueError):
            convert_video(self.source, output, device_type=7, overwrite=True, start=10)
        self.assertEqual(output.read_bytes(), data)

    def test_invalid_video_leaves_no_output(self):
        invalid = self.root / "bad.mp4"
        invalid.write_bytes(b"invalid video")
        output = self.root / "bad.bin"
        with self.assertRaises(ValueError):
            convert_video(invalid, output, device_type=1)
        self.assertFalse(output.exists())
        self.assertFalse(list(self.root.glob(".povbin-*")))

    def test_export_to_filesystem_without_hard_links(self):
        output = self.root / "sdcard.bin"
        with patch("povbin.media.os.link", side_effect=OSError(errno.EPERM, "Hard links unsupported")):
            convert_video(self.source, output, device_type=7, audio=False)
        self.assertEqual(inspect_file(output, 7)["candidates"][0]["frames"], 8)
        self.assertFalse(list(self.root.glob(".povbin-*")))
