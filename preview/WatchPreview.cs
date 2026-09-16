using System;
using System.IO;
using System.Diagnostics;
using System.Drawing.Imaging;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Text;
using System.Windows.Forms;
using System.Collections.Generic;
using System.Web.Script.Serialization;

public sealed class Theme {
    public string name, bg, primary, secondary, accent, text, muted;
    public Color C(string value) { return ColorTranslator.FromHtml(value); }
}
public sealed class WatchModel {
    public int Screen, ThemeIndex;
    public bool Simulated=true, Sleeping, Workout, LiveClock=true;
    public int MeasurementSeconds;
    public DateTime MeasurementStarted;
    public void Navigate(int delta) { Screen=(Screen+delta+6)%6; Sleeping=false; }
    public void Measure() { if(Simulated) { MeasurementStarted=DateTime.UtcNow; MeasurementSeconds=10; } }
    public void Tick() {
        if(MeasurementSeconds>0) MeasurementSeconds=Math.Max(0,10-(int)(DateTime.UtcNow-MeasurementStarted).TotalSeconds);
    }
}
public sealed class WatchPreview : Form {
    static readonly string Root=Path.GetFullPath(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,".."));
    static readonly string[] ThemeFiles={"vitality_flow","nature","clinical","sport","minimal","recovery"};
    static readonly string[] Screens={"Watch face","Vitality","Heart rate","Activity","Environment","Settings"};
    readonly Theme[] themes=new Theme[6];
    readonly Dictionary<string,Image> images=new Dictionary<string,Image>();
    readonly WatchModel model=new WatchModel();
    readonly Timer timer=new Timer();
    Point dragStart;
    readonly Stopwatch animationClock=Stopwatch.StartNew();
    double lastTick, animationTime, enteredAt, transitionAt;
    Bitmap outgoingFace;
    const double TransitionSeconds=0.35;
    float Entrance { get { return Ease((animationTime-enteredAt)/0.9); } }
    static float Ease(double progress) {
        double t=Math.Max(0,Math.Min(1,progress));return (float)(1-Math.Pow(1-t,3));
    }
    double BeatPhase { get { return (animationTime*72/60)%1; } }
    float HeartPulse { get { return (float)(Math.Exp(-Math.Pow((BeatPhase-.15)/.09,2))+
        .45*Math.Exp(-Math.Pow((BeatPhase-.38)/.08,2))); } }
    readonly Color Ink=ColorTranslator.FromHtml("#eaf4ef"), Muted=ColorTranslator.FromHtml("#7e9390");
    public WatchPreview() {
        Text="Vitality / Watch Studio";
        Icon=Icon.ExtractAssociatedIcon(Application.ExecutablePath);
        ClientSize=new Size(1120,780); MinimumSize=SizeFromClientSize(new Size(1120,780));
        MaximumSize=MinimumSize; FormBorderStyle=FormBorderStyle.FixedSingle;
        MaximizeBox=false; BackColor=ColorTranslator.FromHtml("#101917");
        DoubleBuffered=true; KeyPreview=true;
        JavaScriptSerializer json=new JavaScriptSerializer();
        for(int i=0;i<6;i++) themes[i]=json.Deserialize<Theme>(File.ReadAllText(Path.Combine(Root,"vitality_watch_assets","themes",ThemeFiles[i]+".json")));
        foreach(string icon in new[]{"heart","spo2","steps","sleep","environment","temperature","humidity","altitude","battery"}) {
            string p=Path.Combine(Root,"assets","masters",icon+".svg");
            if(File.Exists(p)) images[icon]=VectorAssets.Render(p,64);
        }
        MouseDown+=(s,e)=>dragStart=e.Location;
        MouseUp+=OnPointer;
        KeyDown+=(s,e)=> {
            if(e.KeyCode==Keys.Right) Change(()=>model.Navigate(1));
            if(e.KeyCode==Keys.Left) Change(()=>model.Navigate(-1));
            if(e.KeyCode==Keys.Home) Change(()=>{model.Screen=0;model.Sleeping=false;});
            if(e.KeyCode==Keys.Space) Change(()=>model.Sleeping=!model.Sleeping);
        };
        // Monotonic elapsed time keeps animation speed independent of dropped frames.
        timer.Interval=33;
        timer.Tick+=(s,e)=>{
            double now=animationClock.Elapsed.TotalSeconds;
            double elapsed=Math.Max(0,now-lastTick);lastTick=now;
            model.Tick();
            if(WindowState==FormWindowState.Minimized) return;
            if(model.Sleeping && outgoingFace==null) return;
            animationTime+=elapsed;
            if(outgoingFace!=null && animationTime-transitionAt>=TransitionSeconds) {
                outgoingFace.Dispose();outgoingFace=null;
            }
            Invalidate(new Rectangle(444,171,470,470));
        };
        lastTick=animationClock.Elapsed.TotalSeconds;
        timer.Start();
    }
    protected override void Dispose(bool disposing) {
        if(disposing) {timer.Dispose();if(outgoingFace!=null)outgoingFace.Dispose();foreach(Image im in images.Values) im.Dispose();}
        base.Dispose(disposing);
    }
    void Change(System.Action update) {
        Bitmap old=new Bitmap(466,466);
        using(Graphics g=Graphics.FromImage(old)) {
            g.SmoothingMode=SmoothingMode.AntiAlias;g.TextRenderingHint=TextRenderingHint.AntiAliasGridFit;
            DrawAnimatedFace(g);
        }
        if(outgoingFace!=null)outgoingFace.Dispose();
        outgoingFace=old;
        update();
        enteredAt=transitionAt=animationTime;
        Invalidate();
    }
    void OnPointer(object sender,MouseEventArgs e) {
        if(e.X>360 && Math.Abs(e.X-dragStart.X)>65) {
            Change(()=>model.Navigate(e.X<dragStart.X?1:-1));return;
        }
        if(e.X>=30 && e.X<=252) {
            for(int i=0;i<6;i++) if(e.Y>=207+i*55 && e.Y<253+i*55) {
                int target=i;Change(()=>{model.Screen=target;model.Sleeping=false;});return;
            }
            if(e.Y>=615 && e.Y<=650) Change(()=>{
                model.Simulated=!model.Simulated;model.MeasurementSeconds=0;
                if(!model.Simulated)model.Workout=false;
            });
            if(e.Y>=662 && e.Y<=697) Change(()=>model.LiveClock=!model.LiveClock);
        }
        if(e.X>=365 && e.X<1025 && e.Y>=705 && e.Y<=747) {
            int i=(e.X-365)/110;if(i<6)Change(()=>model.ThemeIndex=i);
        }
        if(e.X>=945 && e.X<=993 && e.Y>=303 && e.Y<=357) Change(()=>model.Sleeping=!model.Sleeping);
        if(!model.Sleeping && e.X>=551 && e.X<=807 && e.Y>=494 && e.Y<=538) {
            if(model.Screen==2) model.Measure();
            if(model.Screen==3 && model.Simulated) model.Workout=!model.Workout;
            if(model.Screen==5) Change(()=>model.ThemeIndex=(model.ThemeIndex+1)%6);
        }
        Invalidate();
    }
    void DrawAnimatedFace(Graphics g) {
        if(outgoingFace!=null && animationTime<=transitionAt) {
            g.DrawImageUnscaled(outgoingFace,0,0);return;
        }
        DrawFace(g);
        if(outgoingFace==null)return;
        float alpha=1-Ease((animationTime-transitionAt)/TransitionSeconds);
        if(alpha<=0)return;
        using(ImageAttributes attributes=new ImageAttributes()) {
            ColorMatrix matrix=new ColorMatrix();matrix.Matrix33=alpha;
            attributes.SetColorMatrix(matrix);
            g.DrawImage(outgoingFace,new Rectangle(0,0,466,466),0,0,466,466,GraphicsUnit.Pixel,attributes);
        }
    }
    void RingHighlight(Graphics g,Color color,float x,float y,float diameter,float start,float sweep,float width) {
        if(!model.Simulated)return;
        // Light moves within the fixed progress arc, without changing the score.
        float position=(float)((animationTime*.20)%1);
        float head=start+position*Math.Max(0,sweep-16);
        float opacity=(float)Math.Sin(position*Math.PI);
        Arc(g,Color.FromArgb((int)(45*opacity),color),width+8,x,y,diameter,head,16);
        Arc(g,Color.FromArgb((int)(210*opacity),color),width,x,y,diameter,head,16);
    }
    void HeartTrace(Graphics g,Color color) {
        if(!model.Simulated)return;
        PointF[] points=new PointF[181];
        for(int i=0;i<points.Length;i++) {
            double phase=((animationTime-(points.Length-1-i)/90.0)*1.2)%1;
            if(phase<0)phase+=1;
            double value=4*Math.Exp(-Math.Pow((phase-.12)/.055,2))
                -7*Math.Exp(-Math.Pow((phase-.25)/.022,2))
                +24*Math.Exp(-Math.Pow((phase-.30)/.019,2))
                -12*Math.Exp(-Math.Pow((phase-.35)/.025,2))
                +6*Math.Exp(-Math.Pow((phase-.58)/.09,2));
            points[i]=new PointF(90+i*1.6f,292-(float)value);
        }
        using(Pen glow=new Pen(Color.FromArgb(35,color),6))g.DrawLines(glow,points);
        using(Pen line=new Pen(color,2))g.DrawLines(line,points);
        PointF tip=points[points.Length-1];
        using(Brush b=new SolidBrush(color))g.FillEllipse(b,tip.X-3,tip.Y-3,6,6);
    }
    static void Rect(Graphics g,Brush brush,float x,float y,float w,float h,float r) {
        using(GraphicsPath p=new GraphicsPath()) {
            p.AddArc(x,y,r*2,r*2,180,90);p.AddArc(x+w-r*2,y,r*2,r*2,270,90);
            p.AddArc(x+w-r*2,y+h-r*2,r*2,r*2,0,90);p.AddArc(x,y+h-r*2,r*2,r*2,90,90);
            p.CloseFigure();g.FillPath(brush,p);
        }
    }
    static void T(Graphics g,string text,float size,Color color,float x,float y,float w, bool bold=false, bool center=false) {
        using(Font font=new Font("Segoe UI",size,bold?FontStyle.Bold:FontStyle.Regular,GraphicsUnit.Pixel))
        using(Brush b=new SolidBrush(color))
        using(StringFormat f=new StringFormat()) {
            f.Alignment=center?StringAlignment.Center:StringAlignment.Near;
            f.LineAlignment=StringAlignment.Near;
            g.DrawString(text,font,b,new RectangleF(x,y,w,100),f);
        }
    }
    static void Arc(Graphics g,Color color,float width,float x,float y,float size,float start,float sweep) {
        if(sweep<=0) return;
        using(Pen p=new Pen(color,width)) {p.StartCap=LineCap.Round;p.EndCap=LineCap.Round;g.DrawArc(p,x,y,size,size,start,sweep);}
    }
    static void Mark(Graphics g,float x,float y,float size) {
        GraphicsState state=g.Save();g.TranslateTransform(x,y);g.ScaleTransform(size/128,size/128);
        using(GraphicsPath a=new GraphicsPath()) {
            a.AddBezier(64,113,42,95,39,48,12,27);a.AddBezier(12,27,44,20,65,49,66,91);a.CloseFigure();
            using(LinearGradientBrush b=new LinearGradientBrush(new Point(12,27),new Point(66,113),Color.Cyan,Color.FromArgb(0,93,219))) g.FillPath(b,a);
        }
        using(GraphicsPath a=new GraphicsPath()) {
            a.AddBezier(64,113,68,59,82,33,116,19);a.AddBezier(116,19,116,58,98,83,64,113);a.CloseFigure();
            using(LinearGradientBrush b=new LinearGradientBrush(new Point(116,19),new Point(64,113),Color.FromArgb(109,248,62),Color.FromArgb(0,132,168))) g.FillPath(b,a);
        }
        using(Pen p=new Pen(Color.FromArgb(197,255,231),2))g.DrawBezier(p,64,113,76,80,86,53,111,26);
        using(LinearGradientBrush b=new LinearGradientBrush(new Point(53,21),new Point(73,41),Color.FromArgb(0,228,154),Color.FromArgb(0,134,211)))g.FillEllipse(b,53,21,20,20);
        g.Restore(state);
    }
    void DrawIcon(Graphics g,string name,float x,float y,int size) {if(images.ContainsKey(name))g.DrawImage(images[name],x,y,size,size);}
    protected override void OnPaint(PaintEventArgs e) {
        base.OnPaint(e); DrawStudio(e.Graphics);
    }
    void DrawStudio(Graphics g) {
        g.SmoothingMode=SmoothingMode.AntiAlias;g.TextRenderingHint=TextRenderingHint.AntiAliasGridFit;
        g.Clear(BackColor);
        using(Brush b=new SolidBrush(Color.FromArgb(21,34,30)))g.FillRectangle(b,0,0,284,780);
        Mark(g,30,28,41);T(g,"vitality",28,Ink,83,34,180,true);
        T(g,"WATCH STUDIO",10,Muted,34,93,215);
        using(Pen p=new Pen(Color.FromArgb(44,62,53)))g.DrawLine(p,32,137,252,137);
        T(g,"EXPLORE YOUR WATCH",10,Muted,34,170,230);
        for(int i=0;i<6;i++) {
            if(model.Screen==i)using(Brush b=new SolidBrush(Color.FromArgb(40,62,50)))Rect(g,b,24,203+i*55,236,46,10);
            T(g,(i+1).ToString("00"),11,i==model.Screen?Color.FromArgb(164,227,179):Muted,39,219+i*55,30);
            T(g,Screens[i],15,i==model.Screen?Ink:Muted,78,216+i*55,170,i==model.Screen);
        }
        T(g,"DEVELOPMENT MODE",10,Muted,34,573,230);
        Toggle(g,"Simulated sensors",model.Simulated,618);
        Toggle(g,"Use computer clock",model.LiveClock,666);
        T(g,"v0.1  /  nRF52840",11,Muted,34,734,220);
        T(g,"A little more in balance.",28,Ink,336,40,660,true);
        T(g,"Your health. Your time. A better you.",14,Muted,337,82,610);
        using(Brush b=new SolidBrush(Color.FromArgb(37,64,45)))Rect(g,b,894,49,168,30,15);
        T(g,"DESKTOP PREVIEW",10,Color.FromArgb(166,226,181),894,58,168,false,true);
        // Physical enclosure surrounding the exact 466 x 466 display.
        using(LinearGradientBrush b=new LinearGradientBrush(new Point(542,110),new Point(795,685),Color.FromArgb(28,36,33),Color.FromArgb(42,50,46)))Rect(g,b,559,113,239,567,45);
        using(Pen p=new Pen(Color.FromArgb(48,60,53),1))for(int y=125;y<680;y+=12)g.DrawLine(p,577,y,781,y);
        using(Brush b=new SolidBrush(Color.FromArgb(4,8,7)))g.FillEllipse(b,416,153,538,538);
        using(LinearGradientBrush b=new LinearGradientBrush(new Point(424,155),new Point(922,664),Color.FromArgb(114,132,122),Color.FromArgb(27,36,31)))g.FillEllipse(b,419,146,520,520);
        using(Brush b=new SolidBrush(Color.FromArgb(7,11,10)))g.FillEllipse(b,426,153,506,506);
        using(Brush b=new SolidBrush(Color.FromArgb(84,100,90)))Rect(g,b,945,302,32,55,9);
        using(Pen p=new Pen(Color.FromArgb(37,49,41)))for(int y=309;y<350;y+=5)g.DrawLine(p,949,y,972,y);
        GraphicsState saved=g.Save();
        g.TranslateTransform(446,173);
        using(GraphicsPath clip=new GraphicsPath()) {clip.AddEllipse(0,0,466,466);g.SetClip(clip);}
        DrawAnimatedFace(g);
        g.Restore(saved);
        T(g,"Swipe or use arrow keys to explore  /  Crown or Space to sleep",11,Muted,351,681,685,false,true);
        for(int i=0;i<6;i++) {
            float x=365+i*110;
            if(model.ThemeIndex==i)using(Brush b=new SolidBrush(Color.FromArgb(42,59,48)))Rect(g,b,x,709,103,41,10);
            using(Brush b=new SolidBrush(themes[i].C(themes[i].primary)))g.FillEllipse(b,x+10,725,8,8);
            T(g,themes[i].name== "Vitality Flow"?"Flow":themes[i].name,11,i==model.ThemeIndex?Ink:Muted,x+24,721,80);
        }
    }
    void Toggle(Graphics g,string name,bool on,int y) {
        T(g,name,13,Ink,34,y,180);
        using(Brush b=new SolidBrush(on?Color.FromArgb(123,203,145):Color.FromArgb(60,73,65)))Rect(g,b,219,y,32,18,9);
        using(Brush b=new SolidBrush(Color.FromArgb(238,248,240)))g.FillEllipse(b,on?235:221,y+2,14,14);
    }
    void DrawFace(Graphics g) {
        Theme th=themes[model.ThemeIndex];
        Color bg=th.C(th.bg),fg=th.C(th.text),muted=th.C(th.muted),primary=th.C(th.primary),secondary=th.C(th.secondary);
        using(Brush b=new SolidBrush(model.Sleeping?Color.Black:bg))g.FillRectangle(b,0,0,466,466);
        if(model.Sleeping) {T(g,"Sleeping",18,Color.FromArgb(95,112,100),0,217,466,false,true);return;}
        if(model.ThemeIndex==1) {
            for(int i=0;i<9;i++) {
                GraphicsState st=g.Save();g.TranslateTransform(i%2==0?45:421,60+i*45);g.RotateTransform((i%2==0?-40:40)+(float)Math.Sin(animationTime*.8+i)*5);
                using(Brush b=new SolidBrush(Color.FromArgb(25,primary)))g.FillEllipse(b,-45,-18,100,37);
                g.Restore(st);
            }
        }
        if(model.ThemeIndex==5) {
            using(LinearGradientBrush b=new LinearGradientBrush(new Point(0,250),new Point(0,466),Color.FromArgb(4,9,7,26),Color.FromArgb(100,56,28,128)))g.FillEllipse(b,-90,240,650,400);
            for(int i=0;i<18;i++)using(Brush b=new SolidBrush(Color.FromArgb(
                70+(int)(80*(.5+.5*Math.Sin(animationTime*1.3+i))),203,204,255)))
                g.FillEllipse(b,35+(i*71)%400,40+(i*43)%295,2,2);
        }
        Color track=Color.FromArgb(45,muted);
        Arc(g,track,7,15,15,436,130,280);
        Arc(g,primary,7,15,15,436,130,model.Simulated?230*Entrance:0);
        RingHighlight(g,primary,15,15,436,130,230*Entrance,7);
        if(model.Screen==0) DrawHome(g,th,fg,muted,primary,secondary);
        else {
            T(g,Screens[model.Screen].ToUpperInvariant(),14,muted,65,75,336,true,true);
            Mark(g,211,22,44);
            if(model.Screen==1) {
                Arc(g,track,13,133,114,200,130,280);
                Arc(g,secondary,13,133,114,200,130,model.Simulated?230*Entrance:0);
                RingHighlight(g,secondary,133,114,200,130,230*Entrance,13);
                if(model.Simulated) {
                    float breath=(float)(.5+.5*Math.Sin(animationTime*1.8));
                    Arc(g,Color.FromArgb(20+(int)(25*breath),secondary),2,123-breath*3,104-breath*3,220+breath*6,0,359);
                }
                T(g,model.Simulated?((int)Math.Round(82*Entrance)).ToString():"--",74,fg,0,153,466,true,true);
                T(g,model.Simulated?"ENERGIZED":"UNAVAILABLE",11,secondary,0,239,466,true,true);
                Metric(g,"Movement",model.Simulated?"78":"--",99,324,primary);
                Metric(g,"Recovery",model.Simulated?"88":"--",199,324,secondary);
                Metric(g,"Sleep",model.Simulated?"84":"--",299,324,th.C(th.accent));
            } else if(model.Screen==2) {
                int heartSize=44+(model.Simulated?(int)(8*HeartPulse):0);
                DrawIcon(g,"heart",233-heartSize/2f,135-heartSize/2f,heartSize);
                if(model.MeasurementSeconds>0) {
                    Arc(g,Color.FromArgb(55,primary),2,199,101,68,0,359);
                    Arc(g,primary,3,199,101,68,(float)(animationTime*200%360),85);
                }
                T(g,model.Simulated?"72":"--",77,fg,0,155,466,true,true);
                T(g,"BEATS PER MINUTE",10,muted,0,243,466,false,true);
                HeartTrace(g,Color.FromArgb(255,70,112));
                Action(g,model.MeasurementSeconds>0?"Demo measuring ... "+model.MeasurementSeconds+"s":"Run demo measurement",primary);
                if(model.MeasurementSeconds>0) {
                    float progress=(float)Math.Max(0,Math.Min(1,(DateTime.UtcNow-model.MeasurementStarted).TotalSeconds/10));
                    using(Pen pen=new Pen(primary,2))g.DrawLine(pen,125,361,125+216*progress,361);
                }
                T(g,model.Simulated?"SpO2  98%":"SpO2 unavailable",13,muted,0,379,466,false,true);
            } else if(model.Screen==3) {
                DrawIcon(g,"steps",211,119+(model.Workout?(float)Math.Sin(animationTime*8)*4:0),44);
                T(g,model.Simulated?"8,421":"--",64,fg,0,170,466,true,true);
                T(g,"OF 10,000 STEPS",11,muted,0,247,466,false,true);
                using(Brush b=new SolidBrush(track))Rect(g,b,107,280,252,7,3);
                if(model.Simulated)using(Brush b=new SolidBrush(secondary))Rect(g,b,107,280,Math.Max(7,212*Entrance),7,3);
                Action(g,model.Workout?"Stop demo workout":"Start demo workout",primary);
                T(g,model.Workout?"Workout mode active":"Every step adds up.",13,muted,0,379,466,false,true);
            } else if(model.Screen==4) {
                DrawIcon(g,"environment",205,112+(float)Math.Sin(animationTime*1.7)*3,56);
                T(g,model.Simulated?"26°":"--",76,fg,0,169,466,true,true);
                T(g,"AMBIENT TEMPERATURE",10,muted,0,258,466,false,true);
                Metric(g,"Humidity",model.Simulated?"52%":"--",103,320,primary);
                Metric(g,"Altitude",model.Simulated?"118 m":"--",263,320,secondary);
                T(g,model.Simulated?"Skin temperature  33.4°C":"Sensors unavailable",12,muted,0,385,466,false,true);
            } else {
                T(g,th.name,34,fg,40,157,386,true,true);
                T(g,"MAKE IT YOURS",10,muted,0,211,466,false,true);
                for(int i=0;i<6;i++)using(Brush b=new SolidBrush(themes[i].C(themes[i].primary)))g.FillEllipse(b,119+i*39,262,28,28);
                Action(g,"Change watch theme",primary);
                T(g,"Battery "+(model.Simulated?"78%":"--")+"  /  Bluetooth unavailable",12,muted,0,383,466,false,true);
            }
        }
        T(g,model.Simulated?"SIMULATED DATA":"NO SENSOR CONNECTION",9,muted,0,422,466,false,true);
    }
    void DrawHome(Graphics g,Theme th,Color fg,Color muted,Color primary,Color secondary) {
        DateTime now=model.LiveClock?DateTime.Now:new DateTime(2024,4,23,10,8,0).AddSeconds(animationTime);
        string time=now.ToString("HH:mm");
        string date=now.ToString("ddd, dd MMM").ToUpperInvariant();
        float markSize=50+(float)Math.Sin(animationTime*1.7)*2;
        Mark(g,233-markSize/2,77-markSize/2,markSize);
        T(g,"VITALITY",10,muted,0,111,466,false,true);
        if(model.ThemeIndex==1 || model.ThemeIndex==4) {
            using(Pen tick=new Pen(Color.FromArgb(70,muted),2))for(int i=0;i<12;i++) {
                double a=i*Math.PI/6;g.DrawLine(tick,233+(float)Math.Sin(a)*151,223-(float)Math.Cos(a)*151,233+(float)Math.Sin(a)*157,223-(float)Math.Cos(a)*157);
            }
            Hand(g,(now.Hour%12+now.Minute/60.0)*Math.PI/6,100,5,fg);
            Hand(g,(now.Minute+now.Second/60.0)*Math.PI/30,137,3,fg);
            Hand(g,(now.Second+now.Millisecond/1000.0)*Math.PI/30,141,1,secondary);
            using(Brush b=new SolidBrush(secondary))g.FillEllipse(b,228,218,10,10);
            T(g,date,11,muted,0,294,466,false,true);
        } else {
            T(g,time,model.ThemeIndex==3?89:83,fg,0,148,466,true,true);
            T(g,date+"  /  "+now.ToString("ss"),12,secondary,0,250,466,false,true);
            T(g,model.Simulated?"A good day to go further.":"Waiting for your sensors.",12,muted,0,283,466,false,true);
        }
        HomeMetric(g,"heart",model.Simulated?"72":"--","BPM",109,fg,muted);
        HomeMetric(g,"steps",model.Simulated?"8,421":"--","STEPS",233,fg,muted);
        HomeMetric(g,"sleep",model.Simulated?"7h 24":"--","SLEEP",357,fg,muted);
        Arc(g,secondary,3,25,25,416,130,model.Simulated?195*Entrance:0);
        RingHighlight(g,secondary,25,25,416,130,195*Entrance,3);
    }
    static void Hand(Graphics g,double a,float length,float width,Color color) {
        using(Pen p=new Pen(color,width)) {p.EndCap=LineCap.Round;g.DrawLine(p,233,223,233+(float)Math.Sin(a)*length,223-(float)Math.Cos(a)*length);}
    }
    void HomeMetric(Graphics g,string icon,string value,string unit,int x,Color fg,Color muted) {
        int size=26+(icon=="heart"&&model.Simulated?(int)(4*HeartPulse):0);
        DrawIcon(g,icon,x-size/2f,342-size/2f,size);T(g,value,22,fg,x-55,359,110,true,true);T(g,unit,8,muted,x-55,389,110,false,true);
    }
    void Metric(Graphics g,string label,string value,int x,int y,Color color) {
        T(g,value,24,color,x-25,y,120,true,true);T(g,label,10,themes[model.ThemeIndex].C(themes[model.ThemeIndex].muted),x-25,y+33,120,false,true);
    }
    void Action(Graphics g,string text,Color primary) {
        using(Brush b=new SolidBrush(Color.FromArgb(30,primary)))Rect(g,b,105,321,256,44,22);
        T(g,text,13,primary,105,335,256,true,true);
    }
    void Render() {
        string output=Path.Combine(Root,"build","screenshots");Directory.CreateDirectory(output);
        using(Bitmap studio=new Bitmap(1120,780)) {using(Graphics g=Graphics.FromImage(studio))DrawStudio(g);studio.Save(Path.Combine(output,"studio.png"));}
        using(Bitmap grid=new Bitmap(466*3,466*2)) {
            using(Graphics g=Graphics.FromImage(grid)) {
                g.SmoothingMode=SmoothingMode.AntiAlias;g.TextRenderingHint=TextRenderingHint.AntiAliasGridFit;
                for(int i=0;i<6;i++) {model.ThemeIndex=i;GraphicsState st=g.Save();g.TranslateTransform(i%3*466,i/3*466);g.SetClip(new Rectangle(0,0,466,466));DrawFace(g);g.Restore(st);}
            }
            grid.Save(Path.Combine(output,"themes.png"));
        }
        model.ThemeIndex=0;
        for(int i=0;i<6;i++) {
            model.Screen=i;
            using(Bitmap b=new Bitmap(466,466)) {using(Graphics g=Graphics.FromImage(b)){g.SmoothingMode=SmoothingMode.AntiAlias;g.TextRenderingHint=TextRenderingHint.AntiAliasGridFit;DrawFace(g);}b.Save(Path.Combine(output,"screen-"+i+".png"));}
        }
    }
    Bitmap Frame(bool transition) {
        Bitmap b=new Bitmap(466,466);
        using(Graphics g=Graphics.FromImage(b)) {
            g.SmoothingMode=SmoothingMode.AntiAlias;g.TextRenderingHint=TextRenderingHint.AntiAliasGridFit;
            if(transition)DrawAnimatedFace(g);else DrawFace(g);
        }
        return b;
    }
    static int PixelChanges(Bitmap a,Bitmap b) {
        int count=0;
        for(int y=0;y<466;y+=2)for(int x=0;x<466;x+=2)
            if(a.GetPixel(x,y)!=b.GetPixel(x,y))count++;
        return count;
    }
    void AnimationTests() {
        model.LiveClock=false;model.Simulated=true;model.Sleeping=false;enteredAt=0;
        for(int screen=0;screen<6;screen++) {
            model.Screen=screen;model.ThemeIndex=0;animationTime=2;
            using(Bitmap first=Frame(false)) {
                animationTime=2.24;
                using(Bitmap next=Frame(false))
                    if(PixelChanges(first,next)<10)throw new Exception("Static animation screen "+screen);
            }
        }
        // Off-state frames must be identical even when time advances.
        model.Screen=2;model.Sleeping=true;animationTime=3;
        using(Bitmap first=Frame(false)) {
            animationTime=4;
            using(Bitmap next=Frame(false))
                if(PixelChanges(first,next)!=0)throw new Exception("Sleeping animation");
        }
        model.Sleeping=false;model.Simulated=false;animationTime=5;
        using(Bitmap first=Frame(false)) {
            animationTime=6;
            using(Bitmap next=Frame(false))
                if(PixelChanges(first,next)!=0)throw new Exception("Unavailable heart trace animated");
        }
        model.Simulated=true;model.Screen=0;animationTime=7;
        using(Bitmap first=Frame(false)) {
            Change(()=>model.Screen=1);
            using(Bitmap start=Frame(true))
                if(PixelChanges(first,start)!=0)throw new Exception("Transition first frame jumped");
            animationTime+=TransitionSeconds/2;
            using(Bitmap middle=Frame(true)) {
                if(PixelChanges(first,middle)<100)throw new Exception("Transition not advancing");
                animationTime+=TransitionSeconds;
                using(Bitmap last=Frame(true))
                    if(PixelChanges(middle,last)<100)throw new Exception("Transition not completing");
                using(Bitmap last=Frame(true))using(Bitmap direct=Frame(false))
                    if(PixelChanges(last,direct)!=0)throw new Exception("Transition endpoint mismatch");
            }
        }
        outgoingFace.Dispose();outgoingFace=null;
        // Exercise the real WinForms timer/message pump, not only injected frame times.
        double before=animationTime;Stopwatch wait=Stopwatch.StartNew();
        while(wait.ElapsedMilliseconds<180) {Application.DoEvents();System.Threading.Thread.Sleep(2);}
        if(animationTime<=before)throw new Exception("Animation timer did not advance");
        model.Sleeping=true;before=animationTime;wait.Restart();
        while(wait.ElapsedMilliseconds<100) {Application.DoEvents();System.Threading.Thread.Sleep(2);}
        if(animationTime!=before)throw new Exception("Timer animated sleeping display");
        model.Sleeping=false;model.Screen=0;model.ThemeIndex=0;animationTime=2;enteredAt=0;
        string output=Path.Combine(Root,"build","screenshots");Directory.CreateDirectory(output);
        model.Screen=2;
        using(Bitmap strip=new Bitmap(466*3,466)) {
            using(Graphics g=Graphics.FromImage(strip))for(int i=0;i<3;i++) {
                animationTime=2+i*.24;
                using(Bitmap frame=Frame(false))g.DrawImageUnscaled(frame,i*466,0);
            }
            strip.Save(Path.Combine(output,"animation-heart-strip.png"));
        }
        model.Screen=0;animationTime=2;
    }
    void SelfTest() {
        model.Screen=0;model.Navigate(-1);if(model.Screen!=5)throw new Exception("Previous wrap");
        model.Navigate(1);if(model.Screen!=0)throw new Exception("Next wrap");
        model.Simulated=false;model.Measure();if(model.MeasurementSeconds!=0)throw new Exception("Unavailable measurement");
        model.Simulated=true;model.Measure();if(model.MeasurementSeconds!=10)throw new Exception("Start measurement");
        model.MeasurementStarted=DateTime.UtcNow.AddSeconds(-11);model.Tick();if(model.MeasurementSeconds!=0)throw new Exception("Finish measurement");
        for(int i=0;i<6;i++)if(themes[i].name==null)throw new Exception("Missing theme");
        AnimationTests();
        File.WriteAllText(Path.Combine(Root,"build","preview-tests.txt"),
            "PASS: navigation wrap, unavailable measurement, demo measurement lifecycle, six source themes.\r\n"+
            "PASS: changing frames on all six screens, static sleep, no unavailable heart animation, transition start/middle/end, live timer ticks, sleeping timer pause.");
    }
    [STAThread] public static int Main(string[] args) {
        try {
            Application.EnableVisualStyles();
            using(WatchPreview form=new WatchPreview()) {
                if(args.Length>0 && args[0]=="--render") {form.SelfTest();form.model.Screen=0;form.Render();return 0;}
                Application.Run(form);
            }
            return 0;
        } catch(Exception ex) {
            File.WriteAllText(Path.Combine(Root,"build","preview-error.txt"),ex.ToString());return 1;
        }
    }
}
