using System;
using System.IO;
using System.Xml;
using System.Globalization;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Text.RegularExpressions;
// Small, strict renderer for assets/masters only. Unsupported SVG constructs fail.
public static class VectorAssets {
    static float N(string s,float fallback) {return String.IsNullOrEmpty(s)?fallback:float.Parse(s,CultureInfo.InvariantCulture);}
    static float A(XmlElement e,string a,float d=0) {return N(e.GetAttribute(a),d);}
    static GraphicsPath Path(XmlElement e) {
        GraphicsPath p=new GraphicsPath();
        switch(e.LocalName) {
        case "circle": float r=A(e,"r");p.AddEllipse(A(e,"cx")-r,A(e,"cy")-r,2*r,2*r);break;
        case "ellipse":p.AddEllipse(A(e,"cx")-A(e,"rx"),A(e,"cy")-A(e,"ry"),2*A(e,"rx"),2*A(e,"ry"));break;
        case "rect":p.AddRectangle(new RectangleF(A(e,"x"),A(e,"y"),A(e,"width"),A(e,"height")));break;
        case "line":p.AddLine(A(e,"x1"),A(e,"y1"),A(e,"x2"),A(e,"y2"));break;
        case "path":
            MatchCollection tokens=Regex.Matches(e.GetAttribute("d"),@"[A-Za-z]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?");
            int i=0;float x=0,y=0;char command=' ';float startX=0,startY=0;
            while(i<tokens.Count) {
                if(Char.IsLetter(tokens[i].Value[0]))command=tokens[i++].Value[0];
                if(command=='Z') {p.CloseFigure();x=startX;y=startY;command=' ';continue;}
                if(command=='M') {x=N(tokens[i++].Value,0);y=N(tokens[i++].Value,0);p.StartFigure();startX=x;startY=y;command='L';}
                else if(command=='L') {float xx=N(tokens[i++].Value,0),yy=N(tokens[i++].Value,0);p.AddLine(x,y,xx,yy);x=xx;y=yy;}
                else if(command=='C') {float x1=N(tokens[i++].Value,0),y1=N(tokens[i++].Value,0),x2=N(tokens[i++].Value,0),y2=N(tokens[i++].Value,0),xx=N(tokens[i++].Value,0),yy=N(tokens[i++].Value,0);p.AddBezier(x,y,x1,y1,x2,y2,xx,yy);x=xx;y=yy;}
                else throw new InvalidDataException("Unsupported SVG path command "+command);
            }
            break;
        default: throw new InvalidDataException("Unsupported SVG element "+e.LocalName);
        }
        return p;
    }
    static Brush Fill(XmlDocument doc,string spec,RectangleF bounds) {
        if(spec.StartsWith("url(#")) {
            string id=spec.Substring(5,spec.Length-6);
            XmlElement gradient=doc.SelectSingleNode("//*[@id='"+id+"']") as XmlElement;
            if(gradient==null || gradient.LocalName!="linearGradient")throw new InvalidDataException("Unknown gradient");
            PointF a=new PointF(bounds.X+A(gradient,"x1")*bounds.Width,bounds.Y+A(gradient,"y1")*bounds.Height);
            PointF b=new PointF(bounds.X+A(gradient,"x2",1)*bounds.Width,bounds.Y+A(gradient,"y2")*bounds.Height);
            var stops=gradient.GetElementsByTagName("stop");
            ColorBlend blend=new ColorBlend(stops.Count);
            for(int i=0;i<stops.Count;i++) {XmlElement st=(XmlElement)stops[i];blend.Positions[i]=A(st,"offset");blend.Colors[i]=ColorTranslator.FromHtml(st.GetAttribute("stop-color"));}
            LinearGradientBrush brush=new LinearGradientBrush(a,b,Color.Black,Color.White);brush.InterpolationColors=blend;return brush;
        }
        return new SolidBrush(ColorTranslator.FromHtml(String.IsNullOrEmpty(spec)?"#000000":spec));
    }
    public static Bitmap Render(string file,int size) {
        XmlDocument doc=new XmlDocument();doc.XmlResolver=null;doc.Load(file);
        XmlElement svg=doc.DocumentElement;
        Bitmap bitmap=new Bitmap(size,size,System.Drawing.Imaging.PixelFormat.Format32bppArgb);
        try {
            using(Graphics g=Graphics.FromImage(bitmap)) {
                g.SmoothingMode=SmoothingMode.AntiAlias;
                g.ScaleTransform(size/A(svg,"width",128),size/A(svg,"height",128));
                foreach(XmlNode node in svg.ChildNodes) {
                    XmlElement e=node as XmlElement;if(e==null || e.LocalName=="defs")continue;
                    if(e.HasAttribute("transform"))throw new InvalidDataException("Transforms require full SVG renderer");
                    using(GraphicsPath p=Path(e)) {
                        string fill=e.GetAttribute("fill");
                        if(fill!="none") using(Brush b=Fill(doc,fill,p.GetBounds()))g.FillPath(b,p);
                        if(e.HasAttribute("stroke") && e.GetAttribute("stroke")!="none")using(Pen pen=new Pen(ColorTranslator.FromHtml(e.GetAttribute("stroke")),A(e,"stroke-width",1))) {
                            pen.StartCap=LineCap.Round;pen.EndCap=LineCap.Round;pen.LineJoin=LineJoin.Round;g.DrawPath(pen,p);
                        }
                    }
                }
            }
            return bitmap;
        } catch {bitmap.Dispose();throw;}
    }
}
