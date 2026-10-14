# Pixel conversion findings

## Scope and provenance

Static inspection of the extracted managed assembly `analysis/application/5DDisplayer.exe`, SHA-256 `678a03614e6f25819c15a2a5d90d7637fddf79f12efd38f9d924482af27868be`. This file is the application payload, not the outer installer with the same filename. REA identity/inspection records are `ev_6876a1602c41731d3d6624822580f08d346eb52e25796d635b1cb0c60efbdd01` and `ev_6f800d142072c8d8c2d43c1990afeb1f86f86ba75db8590d6e4f4d939850594d`. REA reported managed member coverage **unavailable** because its metadata admission failed; these records do not establish the method behavior below. Method observations here come from the independent dnfile/dncil and ILSpy decodes. `conversion.cil.txt` provides independently decoded full CIL for the focused methods, including code-relative offsets, tokens, RVA, file offsets and raw CIL SHA-256. Reproduce with `.venv/bin/python docs/evidence/dump_cil.py [path/to/extracted/5DDisplayer.exe]`. ILSpy's readable equivalents are `decompiled/F20AD.Utils/Bin.cs` and `decompiled/F20AD.Connect/BinTool.cs`.

The observed code has two encoders. `Utils.Bin` is used for the offline legacy `.bin` path. `Connect.BinTool` is used with device-provided configuration elsewhere; it is not interchangeable with `Utils.Bin`. This report does not assert that either output was exercised by physical hardware.

## Legacy profiles

`Utils.Bin::.ctor`, token `0x060003e6`, sets these values. Menu labels are observed in `TransformWindow::.ctor`, token `0x0600022d`, IL_00da–IL_01d2; `Device_SelectionChanged`, token `0x06000247`, maps selected ID+1 to DEVICETYPE. Menu array position is not device type.

| Device type | Menu label | Angular rows | Radial LEDs | Bits/channel | Mapping | Pixel bytes/frame |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| 1 | F1 | 520 | 116 | 6 | polar | 137280 |
| 2 | F2 | 520 | 144 | 6 | polar | 168480 |
| 3 | F3 | 520 | 200 | 6 | polar | 234000 |
| 4 | F-Mini18 | 360 | 80 | 5 | polar | 54000 |
| 5 | F-360A | 520 | 80 | 6 | strip | 93600 |
| 6 | F-360B | 520 | 144 | 6 | strip | 168480 |
| 7 | F-Mini11 | 300 | 48 | 5 | polar | 27000 |
| 8 | F-360C | 520 | 200 | 6 | strip | 234000 |
| 9 | F-Mini20 | 360 | 96 | 5 | polar | 64800 |
| 10 | F4 | 450 | 171 | 6 | polar | 175500 |
| 11 | F5 | 520 | 133 | 6 | polar | 156000 |

`getFrameLen`, token `0x060003e7`, IL_0000–IL_0036: `rows * ceil(LEDs*3/8) * bits + 1600`. The 1600 bytes are outside the pixel encoder (audio slot handled by caller). Constructor fallback for unsupported dtype is incomplete (bit defaults zero), so reconstruction should validate type1–11.

## Legacy polar sampling

`makeModel`, token `0x060003ec`, RVA `0x242c0`: IL_0015–IL_0056 establishes angle step `360/rows`, radius `(diam-4)/2`, radial step `radius/LEDs`. IL_006e–IL_00cb starts each row at outer radius and samples `(int)(r*cos(angle)+cx)`, `(int)(cy-r*sin(angle))`, then subtracts the radial step. IL_00cd–IL_00e1 checks strictly `0<x<width` and `0<y<height`. IL_00ee onward reads the 1-based coordinates from packed 24-bit source offset `((y-1)*width + x-1)*3`. Three channels retain their B,G,R byte positions; each passes through `gamma_tab`. Out-of-bounds samples stay black. Radius is repeatedly subtracted and angle repeatedly added; computing either directly from the loop index can change boundary pixels due to floating point rounding.

`bitmapToBin`, token `0x060003ee`, chooses this routine when isRotate and isRGB; all supported constructor profiles have isRGB=true. The name isRGB does not mean that makeModel reverses incoming bytes: it preserves BGR. The alternative makeModelBGR reverses B/R but is not selected by any valid profile here.

`getRGBBytes`, token `0x060003e9`, uses System.Drawing `LockBits` with Format24bppRgb (numeric 137224), copies `Stride*Height` bytes starting Scan0. Standard Windows 24-bit RGB memory is BGR. Later addressing ignores stride, so exact compatibility requires widths with 24-bit scanlines aligned to four bytes (e.g. original cropped square frame width672). The unlocked buffer is copied after UnlockBits; this questionable order is an observation, not a recommended implementation.

## Legacy strip sampling

For device types5/6/8, bitmapToBin IL_0045–IL_0063 sets strip height `width/3` (integer division), y origin `(bitmapHeight-stripHeight)/2+1`, calls makeModelNotRotate with x origin1. `makeModelNotRotate`, token `0x060003eb`, scales row index by width/rows and LED index by stripHeight/LEDs; it computes x=`int(row*width/rows)+1`, y=`int(led*stripHeight/LEDs)+yOrigin+1`, reads source `(x-1,y-1)` with gamma correction. Thus output row indexes progress across image x; LEDs progress down the central horizontal strip. A literal compatibility implementation preserves the extra +1 at the strip's top. The original checks y<width rather than y<height in this helper.

## Legacy bit packing

`bgrToBin`, token `0x060003ea`, RVA `0x24038`, IL_0000–IL_0015 calculates padding `(-3*LEDs)%8`. IL_0064 starts source mask128 each angular row; IL_0073 sets output mask `128 >> padding` at each bitplane. IL_0087–IL_012c tests three adjacent source channels in B,G,R order per LED, writes bits MSB-first, advances output byte when output mask shifts to0. IL_0141–IL_0159 shifts source mask each plane.

Output order is angular row, bitplane from channel bit7 down to bit(8-bits), LED outer-to-inner, B/G/R. Each row-plane is `ceil(3*LEDs/8)` bytes. Unused bits are **leading zero bits in the first byte**, not trailing zeros in the last byte. This matters for type1 (4 padding bits), type10 (7), type11 (1); the other profiles have no row-plane padding. Channels are gamma-adjusted with the exact table and then their lower bits discarded; applying a generic gamma exponent or RGB565 would produce different bytes.

`Bin::.cctor`, token `0x060003ef`, IL_000b loads source static field `0x040004b8` into gamma_tab. The 256 byte field is RVA0x250110 / file offset0x24e310, SHA256 `4fe1cdb64658f8dcf02c2507a1085b12abe75f5efc089cb120e213b6253620ec`. Raw lookup arrays independently extracted from FieldRVA appear in `luts.json`.

## Legacy header

`getHeader`, token `0x060003e8`, RVA0x23ef8 / file offset0x220f8; CIL SHA256 `2fffcb7ecce361f2195533f4b92df0f1bbc170d0c1c1c5a9289a3eda64edbfa4`:

- IL_000e: header[0]=0xee.
- IL_0014–IL_002f: dtype.ToString() -> TypeConversion.GetBytes(str,1)[0], i.e. first UTF8 digit **ASCII**, not numeric dtype. Types10 and11 both write ASCII `'1'` (0x31), same as type1. TypeConversion.GetBytes(string,int), token0x060004b4, includes explicit truncation to the requested byte count.
- IL_0031–IL_005c: create Random; draw Next(255) twice; take final byte of big-endian int, yielding independent byte values0..254 (255 excluded).
- IL_005d–IL_008f: header length=`(offset_image[asciiType ^ a ^ b]+1)*4` (4..1024 bytes).
- IL_0096–IL_00a9: write `[0xee,asciiType,a,b]`.
- IL_00af–IL_00ca: for i>=4, `header[i]=header[i-1] ^ offset_image[i%255]`. Modulus255, not256.

`offset_image` is not pixel scrambling: it determines header length and header filler. Source field0x040004b7 RVA0x250010 / file offset0x24e210, SHA256 `2f1ee281848602f6204161d2571044c5ef136c0d6e609643b9a8074bca4f1b44`. Because the header type digit aliases1/10/11 and profile byte sizes can coincide (2/6,3/8), a decoder should accept an explicit profile rather than claim fully reliable inference from arbitrary files.

## Device-configured encoder (different path)

`BinTool::setConfigure`, token0x0600059d, imports led_num, rows, orientation, color, adjust[256], light[led_num], subsection, bit, lamps, per_bar; zero per_bar becomes lamps. `takeMold(width,height)`, token0x0600059e IL_0000–IL_003a: cx=floor(width/2)+1.5, cy=floor(height/2)+1.5, radius=min(width,height)/2-3. Private takeMold, token0x0600059f, angle step=+360/rows for orientation0, negative otherwise; repeated outer-to-inner radius samples use the same 1-based addressing but no bounds tests.

`Bitmap2Byte`, token0x060005a8, saves BMP then copies width*height*3 bytes at byte54. This selects BMP's BGR pixel storage, conventionally bottom-up, and ignores padding/alternate BMP headers. The six color mappings, observed toBin token0x060005a0: color0 BRG;1 BGR;2 GRB;3 GBR;4 RGB;5 RBG. Each sampled channel transforms to `(byte)(adjust[input]*light[radialIndex])` (truncating conversion, with no explicit clamping).

`toPov`, token0x060005a1, packs bitplanes MSB-first without legacy padding. Let L=leds, R=rows, B=lamps, S=subsection, P=per_bar or B, G=B/P, N=3LR, C=3L/S, D=N/B, Q=N/G, T=R/B. For group g, row t, bitplane k, base-channel c, lamp m, section s, in exactly that nested order, source byte index is `g*Q+t*3L+c+m*D+s*C`; write its bit `(128>>k)`. Output length=N*bit/8 integer division. Valid hardware configurations must satisfy required divisibility; the original does not validate these assumptions.

Residual unknown: which of the listed profiles matches the user's MISSYOU unit. The marketing name alone does not establish LED count/geometry/firmware. Newer devices may require the configured encoder or JPEG FTLV path instead of this legacy format; physical validation is outside static inspection.
