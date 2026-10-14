"""Legacy Utils.Bin format; evidence and original method coordinates: docs/format.md."""

from dataclasses import dataclass
import math
import secrets

import numpy as np

AUDIO_BYTES = 1600
AUDIO_RATE = 32000
FPS = 20
TRAILER_BYTES = 100000


@dataclass(frozen=True)
class Profile:
    device_type: int
    name: str
    rows: int
    leds: int
    bits: int
    rotate: bool = True

    @property
    def plane_bytes(self) -> int:
        return (self.leds * 3 + 7) // 8

    @property
    def video_bytes(self) -> int:
        return self.rows * self.plane_bytes * self.bits

    @property
    def frame_bytes(self) -> int:
        return self.video_bytes + AUDIO_BYTES

    @property
    def type_byte(self) -> int:
        # Original truncates UTF-8 decimal text to one character, including 10/11.
        return ord(str(self.device_type)[0])


PROFILES = {
    p.device_type: p for p in (
        Profile(1, "F1", 520, 116, 6),
        Profile(2, "F2", 520, 144, 6),
        Profile(3, "F3", 520, 200, 6),
        Profile(4, "F-Mini18", 360, 80, 5),
        Profile(5, "F-360A", 520, 80, 6, False),
        Profile(6, "F-360B", 520, 144, 6, False),
        Profile(7, "F-Mini11", 300, 48, 5),
        Profile(8, "F-360C", 520, 200, 6, False),
        Profile(9, "F-Mini20", 360, 96, 5),
        Profile(10, "F4", 450, 171, 6),
        Profile(11, "F5", 520, 133, 6),
    )
}

# These byte tables are recovered data, not approximations of a gamma formula.
GAMMA = np.array([
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
    0,1,1,1,1,1,1,1,1,1,1,1,1,2,2,2,2,2,2,2,2,3,3,3,3,3,3,4,4,4,
    4,4,4,5,5,5,6,6,6,7,7,8,8,9,9,10,10,11,12,12,13,13,14,14,15,16,17,17,18,19,
    20,21,22,23,24,25,26,27,28,29,29,30,31,32,33,34,35,36,37,38,
    40,41,43,44,45,47,49,51,53,55,56,58,59,61,62,63,64,66,68,70,
    72,74,77,79,81,83,85,88,90,93,96,98,101,103,106,108,111,114,117,120,
    123,126,130,133,136,140,143,146,150,154,157,160,164,167,170,173,176,180,183,186,
    188,190,192,194,196,198,200,202,204,206,208,210,211,213,215,216,217,218,219,220,
    222,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,239,240,240,
    241,242,242,243,244,244,245,246,246,247,248,248,249,249,249,250,250,250,251,251,
    251,251,252,252,252,252,253,253,253,253,253,253,254,254,254,254,254,254,255,255,
    255,255,255,255,255,255,
], dtype=np.uint8)

OFFSET = bytes([
    0,192,193,1,195,3,2,194,198,6,7,199,5,197,196,4,204,12,13,205,
    15,207,206,14,10,202,203,11,201,9,8,200,216,24,25,217,27,219,218,26,
    30,222,223,31,221,29,28,220,20,212,213,21,215,23,22,214,210,18,19,211,
    17,209,208,16,240,48,49,241,51,243,242,50,54,246,247,55,245,53,52,244,
    60,252,253,61,255,63,62,254,250,58,59,251,57,249,248,56,40,232,233,41,
    235,43,42,234,238,46,47,239,45,237,236,44,228,36,37,229,39,231,230,38,
    34,226,227,35,225,33,32,224,160,96,97,161,99,163,162,98,102,166,167,103,
    165,101,100,164,108,172,173,109,175,111,110,174,170,106,107,171,105,169,168,104,
    120,184,185,121,187,123,122,186,190,126,127,191,125,189,188,124,180,116,117,181,
    119,183,182,118,114,178,179,115,177,113,112,176,80,144,145,81,147,83,82,146,
    150,86,87,151,85,149,148,84,156,92,93,157,95,159,158,94,90,154,155,91,
    153,89,88,152,136,72,73,137,75,139,138,74,78,142,143,79,141,77,76,140,
    68,132,133,69,135,71,70,134,130,66,67,131,65,129,128,64,
])


def make_header(profile: Profile, nonce: bytes | None = None) -> bytes:
    if nonce is None:
        nonce = bytes((secrets.randbelow(255), secrets.randbelow(255)))
    if len(nonce) != 2 or any(x == 255 for x in nonce):
        raise ValueError("Header nonce must contain two bytes in 0..254")
    a, b = nonce
    length = (OFFSET[profile.type_byte ^ a ^ b] + 1) * 4
    header = bytearray((0xEE, profile.type_byte, a, b))
    for i in range(4, length):
        header.append(header[-1] ^ OFFSET[i % 255])
    return bytes(header)


def parse_header(data: bytes) -> dict:
    if len(data) < 4 or data[0] != 0xEE:
        raise ValueError("Missing 5DDisplayer EE header")
    if data[1] not in {p.type_byte for p in PROFILES.values()}:
        raise ValueError("Unknown device marker in header")
    if data[2] == 255 or data[3] == 255:
        raise ValueError("Invalid header nonce")
    length = (OFFSET[data[1] ^ data[2] ^ data[3]] + 1) * 4
    if len(data) < length:
        raise ValueError("Truncated header")
    for i in range(4, length):
        if data[i] != (data[i - 1] ^ OFFSET[i % 255]):
            raise ValueError(f"Invalid header byte at offset {i}")
    return {"header_bytes": length, "type_marker": chr(data[1]), "nonce": data[2:4].hex(),
            "device_types": [p.device_type for p in PROFILES.values() if p.type_byte == data[1]]}


class Encoder:
    """Precomputed original sampling map; frames are top-down uint8 RGB arrays."""

    def __init__(self, profile: Profile, size: int = 672):
        if size < 16 or size % 4:
            raise ValueError("Frame size must be at least 16 and a multiple of four")
        self.profile = profile
        self.size = size
        self.indices = np.zeros((profile.rows, profile.leds), dtype=np.intp)
        self.valid = np.zeros_like(self.indices, dtype=bool)
        angle = 0.0
        radius = (size - 4) / 2.0
        step = radius / profile.leds
        for row in range(profile.rows):
            # Repeated addition/subtraction is intentional: reproduces original rounding.
            theta = angle * math.pi / 180.0
            cos, sin = math.cos(theta), math.sin(theta)
            r = radius
            for led in range(profile.leds):
                if profile.rotate:
                    x = int(r * cos + size // 2)
                    y = int(size // 2 - r * sin)
                    r -= step
                else:
                    x = int(row * (size / profile.rows)) + 1
                    h = size // 3
                    y = int(led * (h / profile.leds)) + (size - h) // 2 + 2
                if 0 < x < size and 0 < y < size:
                    self.indices[row, led] = (y - 1) * size + x - 1
                    self.valid[row, led] = True
            angle += 360.0 / profile.rows

    def sample(self, rgb: np.ndarray) -> np.ndarray:
        if rgb.shape != (self.size, self.size, 3) or rgb.dtype != np.uint8:
            raise ValueError(f"Expected uint8 RGB shape {(self.size, self.size, 3)}")
        bgr = rgb.reshape(-1, 3)[self.indices][..., ::-1]
        sampled = GAMMA[bgr]
        sampled[~self.valid] = 0
        return sampled

    def pack(self, sampled_bgr: np.ndarray) -> bytes:
        p = self.profile
        if sampled_bgr.shape != (p.rows, p.leds, 3) or sampled_bgr.dtype != np.uint8:
            raise ValueError("Samples must be uint8 BGR in angular-row/LED/channel order")
        bits = ((sampled_bgr.reshape(p.rows, 1, -1) >>
                 np.arange(7, 7 - p.bits, -1, dtype=np.uint8).reshape(1, -1, 1)) & 1)
        padding = p.plane_bytes * 8 - p.leds * 3
        if padding:
            bits = np.pad(bits, ((0, 0), (0, 0), (padding, 0)))
        return np.packbits(bits, axis=2, bitorder="big").tobytes()

    def encode(self, rgb: np.ndarray) -> bytes:
        return self.pack(self.sample(rgb))

    def unpack(self, video: bytes) -> np.ndarray:
        p = self.profile
        if len(video) != p.video_bytes:
            raise ValueError("Incorrect packed frame length")
        packed = np.frombuffer(video, dtype=np.uint8).reshape(p.rows, p.bits, p.plane_bytes)
        bits = np.unpackbits(packed, axis=2, bitorder="big")
        padding = p.plane_bytes * 8 - p.leds * 3
        bits = bits[:, :, padding:]
        values = np.sum(bits.astype(np.uint16) <<
                        np.arange(7, 7 - p.bits, -1).reshape(1, -1, 1), axis=1)
        return values.astype(np.uint8).reshape(p.rows, p.leds, 3)

    def preview(self, video: bytes) -> np.ndarray:
        # Display sampled LED intensities, approximately undoing quantization/gamma.
        values = self.unpack(video)
        inverse = np.array([int(np.argmin(np.abs(GAMMA.astype(int) - x)))
                            for x in range(256)], dtype=np.uint8)
        pixels = inverse[values][..., ::-1]
        canvas = np.zeros((self.size * self.size, 3), dtype=np.uint8)
        canvas[self.indices[self.valid]] = pixels[self.valid]
        return canvas.reshape(self.size, self.size, 3)
