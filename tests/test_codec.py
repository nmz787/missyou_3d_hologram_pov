import hashlib
import json
from pathlib import Path
import unittest

import numpy as np

from povbin.codec import Encoder, GAMMA, OFFSET, PROFILES, make_header, parse_header

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class OriginalMethodParity(unittest.TestCase):
    """Goldens produced by invoking the extracted original assembly, not Python."""

    def test_original_methods_all_eleven_profiles(self):
        manifest = json.loads((FIXTURES / "original-replay.json").read_text())
        y, x, c = np.indices((672, 672, 3))
        rgb = ((x * 17 + y * 31 + c * 73) & 255).astype(np.uint8)[..., ::-1]
        digest = lambda data: hashlib.sha256(data).hexdigest().upper()
        for original in manifest["records"]:
            with self.subTest(device=original["device"]):
                p = PROFILES[original["device"]]
                encoder = Encoder(p)
                samples = encoder.sample(rgb)
                self.assertEqual(digest(samples.tobytes()), original["sampleHash"])
                self.assertEqual(digest(encoder.pack(samples)), original["packedHash"])
                i = np.arange(p.rows * p.leds * 3)
                random_samples = ((i * 37 + (i // 256) * 11) & 255).astype(np.uint8).reshape(p.rows, p.leds, 3)
                self.assertEqual(digest(encoder.pack(random_samples)), original["randomPackedHash"])
                header = bytes.fromhex(original["header"])
                self.assertEqual(make_header(p, header[2:4]), header)
                self.assertEqual(parse_header(header)["header_bytes"], original["headerLength"])

    def test_tables_match_artifact_initializer_bytes(self):
        tables = json.loads((FIXTURES / "luts.json").read_text())
        self.assertEqual(GAMMA.tolist(), tables["gamma_tab"])
        self.assertEqual(list(OFFSET), tables["offset_image"])


class FormatEdges(unittest.TestCase):
    def test_leading_padding_and_plane_order(self):
        for dtype, first in ((1, 0x0F), (10, 0x01), (11, 0x7F)):
            p = PROFILES[dtype]
            encoder = Encoder(p)
            with self.subTest(device=dtype):
                samples = np.full((p.rows, p.leds, 3), 255, dtype=np.uint8)
                plane = bytes((first,)) + b"\xff" * (p.plane_bytes - 1)
                self.assertEqual(encoder.pack(samples), plane * p.bits * p.rows)
                np.testing.assert_array_equal(encoder.unpack(encoder.pack(samples)), samples & ((255 << (8 - p.bits)) & 255))

    def test_only_top_bits_are_written(self):
        p = PROFILES[7]
        encoder = Encoder(p)
        data = np.full((p.rows, p.leds, 3), 7, dtype=np.uint8)
        self.assertEqual(encoder.pack(data), bytes(p.video_bytes))
        data[:, :, 0] = 128  # B is first, then G, R in each LED.
        self.assertEqual(encoder.pack(data)[:3], b"\x92\x49\x24")

    def test_header_corruption_and_first_digit_alias(self):
        header = make_header(PROFILES[1], b"\x01\x02")
        self.assertEqual(len(header), 856)
        self.assertEqual(header[:4], b"\xee\x31\x01\x02")
        self.assertEqual(parse_header(header)["device_types"], [1, 10, 11])
        self.assertEqual(make_header(PROFILES[10], b"\x01\x02"), header)
        with self.assertRaises(ValueError):
            parse_header(header[:10])
        with self.assertRaises(ValueError):
            parse_header(header[:4] + bytes((header[4] ^ 1,)) + header[5:])
        with self.assertRaises(ValueError):
            make_header(PROFILES[1], b"\xff\x00")

    def test_scanline_alignment_and_input_shape(self):
        with self.assertRaises(ValueError):
            Encoder(PROFILES[1], 671)
        with self.assertRaises(ValueError):
            Encoder(PROFILES[1]).encode(np.zeros((20, 20, 3), dtype=np.uint8))
