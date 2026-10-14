using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;

// Executes only isolated byte-array methods from the extracted original assembly.
// Does not start its entry point, GUI, network code, or bitmap APIs.
var assemblyPath = Path.GetFullPath(args[0]);
const string expectedHash = "678A03614E6F25819C15A2A5D90D7637FDDF79F12EFD38F9D924482AF27868BE";
if (Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(assemblyPath))) != expectedHash)
    throw new InvalidOperationException("Replay requires the exact extracted 5DDisplayer assembly hash.");
var output = Path.GetFullPath(args[1]);
Directory.CreateDirectory(output);
var assembly = Assembly.LoadFile(assemblyPath);
var type = assembly.GetType("F20AD.Utils.Bin", true)!;
var flags = BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public;
var records = new List<object>();
for (int device = 1; device <= 11; device++)
{
    var bin = Activator.CreateInstance(type, flags, null, new object[] { device }, null)!;
    int rows = (int)type.GetField("row_num", flags)!.GetValue(bin)!;
    int leds = (int)type.GetField("col_num", flags)!.GetValue(bin)!;
    bool rotate = (bool)type.GetField("isRotate", flags)!.GetValue(bin)!;
    const int width = 672;
    var input = new byte[width * width * 3];
    // Exact, platform-independent source pixels with all byte values and channel variation.
    for (int y = 0; y < width; y++)
        for (int x = 0; x < width; x++)
            for (int c = 0; c < 3; c++)
                input[(y * width + x) * 3 + c] = (byte)((x * 17 + y * 31 + c * 73) & 255);
    var model = type.GetMethod(rotate ? "makeModel" : "makeModelNotRotate", flags)!;
    var samples = (byte[])model.Invoke(bin, rotate
        ? new object[] { input, width / 2, width / 2, width, width, width }
        : new object[] { input, 1, (width - width / 3) / 2 + 1, width, width, width / 3 })!;
    var packed = (byte[])type.GetMethod("bgrToBin", flags)!.Invoke(bin, new object[] { samples })!;
    var randomSamples = new byte[rows * leds * 3];
    for (int i = 0; i < randomSamples.Length; i++) randomSamples[i] = (byte)((i * 37 + (i / 256) * 11) & 255);
    var randomPacked = (byte[])type.GetMethod("bgrToBin", flags)!.Invoke(bin, new object[] { randomSamples })!;
    var header = (byte[])type.GetMethod("getHeader", flags)!.Invoke(bin, null)!;
    File.WriteAllBytes(Path.Combine(output, $"type{device}.samples"), samples);
    File.WriteAllBytes(Path.Combine(output, $"type{device}.packed"), packed);
    File.WriteAllBytes(Path.Combine(output, $"type{device}.random-packed"), randomPacked);
    File.WriteAllBytes(Path.Combine(output, $"type{device}.header"), header);
    records.Add(new { device, rows, leds, rotate, sampleHash = Convert.ToHexString(SHA256.HashData(samples)), packedHash = Convert.ToHexString(SHA256.HashData(packed)), randomPackedHash = Convert.ToHexString(SHA256.HashData(randomPacked)), header = Convert.ToHexString(header), headerLength = header.Length });
}
File.WriteAllText(Path.Combine(output, "manifest.json"), JsonSerializer.Serialize(new { assemblyPath, assemblySha256 = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(assemblyPath))), runtime = System.Runtime.InteropServices.RuntimeInformation.FrameworkDescription, records }, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine($"Replayed original sampling, packing, and header methods for {records.Count} profiles.");
