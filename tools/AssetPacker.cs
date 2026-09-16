using System;
using System.IO;
using System.Text;
using System.Drawing;
using System.Collections.Generic;
using System.Web.Script.Serialization;
public static class AssetPacker {
    sealed class Entry {public string name,source; public byte[] data;public uint crc,offset;public ushort width,height;}
    static uint Crc(byte[] data) {uint crc=0xffffffff;foreach(byte b in data){crc^=b;for(int i=0;i<8;i++)crc=(crc>>1)^((crc&1)!=0?0xedb88320u:0);}return crc^0xffffffff;}
    static byte[] ImageBytes(Bitmap image) {
        using(MemoryStream m=new MemoryStream())using(BinaryWriter b=new BinaryWriter(m)) {
            // LVGL v9, RGB565A8: 12-byte header, RGB565 plane then A8 plane.
            b.Write((byte)0x19);b.Write((byte)0x14);b.Write((ushort)0);
            b.Write((ushort)image.Width);b.Write((ushort)image.Height);b.Write((ushort)(image.Width*2));b.Write((ushort)0);
            for(int y=0;y<image.Height;y++)for(int x=0;x<image.Width;x++){Color c=image.GetPixel(x,y);b.Write((ushort)(((c.R>>3)<<11)|((c.G>>2)<<5)|(c.B>>3)));}
            for(int y=0;y<image.Height;y++)for(int x=0;x<image.Width;x++)b.Write(image.GetPixel(x,y).A);
            return m.ToArray();
        }
    }
    static void Validate(byte[] pack) {
        using(BinaryReader r=new BinaryReader(new MemoryStream(pack))) {
            if(Encoding.ASCII.GetString(r.ReadBytes(4))!="VPK1")throw new InvalidDataException("Magic");
            uint count=r.ReadUInt32(),total=r.ReadUInt32(),version=r.ReadUInt32();
            if(count>128||version!=1||total!=pack.Length||total<16+count*80)throw new InvalidDataException("Header");
            HashSet<string> names=new HashSet<string>();
            uint end=16+count*80;
            for(int i=0;i<count;i++) {
                r.BaseStream.Position=16+i*80;byte[] name=r.ReadBytes(64);int zero=Array.IndexOf(name,(byte)0);
                if(zero<=0)throw new InvalidDataException("Name");
                if(!names.Add(Encoding.UTF8.GetString(name,0,zero)))throw new InvalidDataException("Duplicate");
                uint offset=r.ReadUInt32(),size=r.ReadUInt32(),crc=r.ReadUInt32();
                ushort w=r.ReadUInt16(),h=r.ReadUInt16();
                if(offset<end||offset>total||size>total-offset)throw new InvalidDataException("Bounds");
                end=offset+size;r.BaseStream.Position=offset;byte[] data=r.ReadBytes((int)size);
                if(Crc(data)!=crc)throw new InvalidDataException("CRC");
                if(w!=0&&(data.Length!=12+w*h*3||data[0]!=0x19||data[1]!=0x14))throw new InvalidDataException("LVGL image");
            }
        }
    }
    static void Reject(byte[] bytes) {try {Validate(bytes);}catch(InvalidDataException){return;}catch(EndOfStreamException){return;}throw new Exception("Accepted damaged pack");}
    public static int Main(string[] args) {
        try {
            string root=args[0],output=Path.Combine(root,"qspi_image","output");
            Directory.CreateDirectory(output);List<Entry> list=new List<Entry>();
            foreach(string svg in Directory.GetFiles(Path.Combine(root,"assets","masters"),"*.svg")) {
                string name=Path.GetFileNameWithoutExtension(svg);
                bool logo=name=="vitality_mark";
                using(Bitmap bitmap=VectorAssets.Render(svg,logo?48:64)) {
                    list.Add(new Entry{name=logo?"logo/mark.bin":"icons/"+name+".bin",source="assets/masters/"+Path.GetFileName(svg),data=ImageBytes(bitmap),width=(ushort)bitmap.Width,height=(ushort)bitmap.Height});
                    bitmap.Save(Path.Combine(output,name+".png"));
                }
            }
            foreach(string theme in Directory.GetFiles(Path.Combine(root,"vitality_watch_assets","themes"),"*.json")) {
                list.Add(new Entry{name="themes/"+Path.GetFileName(theme),source="vitality_watch_assets/themes/"+Path.GetFileName(theme),data=File.ReadAllBytes(theme)});
            }
            list.Sort((a,b)=>StringComparer.Ordinal.Compare(a.name,b.name));
            if(list.Count>128)throw new InvalidDataException("Too many assets");
            uint pos=(uint)(16+list.Count*80);
            foreach(Entry e in list){if(Encoding.UTF8.GetByteCount(e.name)>63)throw new InvalidDataException("Long name");e.offset=pos;e.crc=Crc(e.data);pos+=(uint)e.data.Length;}
            if(pos>0x1400000)throw new InvalidDataException("Assets exceed proposed 20 MiB partition");
            byte[] pack;
            using(MemoryStream m=new MemoryStream())using(BinaryWriter w=new BinaryWriter(m)) {
                w.Write(Encoding.ASCII.GetBytes("VPK1"));w.Write((uint)list.Count);w.Write(pos);w.Write(1u);
                foreach(Entry e in list){byte[] name=new byte[64];Encoding.UTF8.GetBytes(e.name).CopyTo(name,0);w.Write(name);w.Write(e.offset);w.Write((uint)e.data.Length);w.Write(e.crc);w.Write(e.width);w.Write(e.height);}
                foreach(Entry e in list)w.Write(e.data);pack=m.ToArray();
            }
            Validate(pack);
            if(Crc(Encoding.ASCII.GetBytes("123456789"))!=0xcbf43926)throw new Exception("CRC standard vector");
            byte[] bad=(byte[])pack.Clone();bad[0]=0;Reject(bad);
            bad=(byte[])pack.Clone();bad[bad.Length-1]^=1;Reject(bad);
            bad=(byte[])pack.Clone();bad[80]=255;bad[81]=255;bad[82]=255;bad[83]=255;Reject(bad);
            byte[] shortPack=new byte[pack.Length-1];Array.Copy(pack,shortPack,shortPack.Length);Reject(shortPack);
            File.WriteAllBytes(Path.Combine(output,"vitality_assets.bin"),pack);
            var manifest=new List<object>();
            foreach(Entry e in list)manifest.Add(new {name=e.name,source=e.source,offset=e.offset,size=e.data.Length,crc32=e.crc,width=e.width,height=e.height});
            File.WriteAllText(Path.Combine(output,"manifest.json"),new JavaScriptSerializer().Serialize(new {version=1,format="VPK1 / LVGL9 RGB565A8",bytes=pos,entries=manifest}));
            Console.WriteLine("PASS: "+list.Count+" assets; "+pos+" bytes; CRC vector, round-trip, corrupt header, corrupt payload, out-of-bounds offset, truncated pack.");
            return 0;
        } catch(Exception e){Console.Error.WriteLine(e);return 1;}
    }
}
