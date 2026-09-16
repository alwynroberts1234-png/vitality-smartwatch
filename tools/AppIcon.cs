using System;
using System.IO;
using System.Drawing;
using System.Drawing.Imaging;

// Derive platform app icons from the SVG master using the existing renderer.
public static class AppIcon {
    public static int Main(string[] args) {
        int[] sizes = {16, 24, 32, 48, 64, 128, 256};
        byte[][] frames = new byte[sizes.Length][];
        for (int i = 0; i < sizes.Length; i++) {
            using (Bitmap bitmap = VectorAssets.Render(args[0], sizes[i]))
            using (MemoryStream png = new MemoryStream()) {
                bitmap.Save(png, ImageFormat.Png);
                frames[i] = png.ToArray();
                if (sizes[i] == 256) File.WriteAllBytes(args[2], frames[i]);
            }
        }
        using (BinaryWriter writer = new BinaryWriter(File.Create(args[1]))) {
            writer.Write((ushort)0); writer.Write((ushort)1); writer.Write((ushort)sizes.Length);
            int offset = 6 + 16 * sizes.Length;
            for (int i = 0; i < sizes.Length; i++) {
                writer.Write((byte)(sizes[i] == 256 ? 0 : sizes[i]));
                writer.Write((byte)(sizes[i] == 256 ? 0 : sizes[i]));
                writer.Write((byte)0); writer.Write((byte)0);
                writer.Write((ushort)1); writer.Write((ushort)32);
                writer.Write(frames[i].Length); writer.Write(offset);
                offset += frames[i].Length;
            }
            foreach (byte[] frame in frames) writer.Write(frame);
        }
        return 0;
    }
}
