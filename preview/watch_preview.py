"""Portable animated Vitality design preview using Python's optional Tk module."""
from __future__ import annotations
from datetime import datetime, timedelta
import json
import math
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
THEMES = ("vitality_flow", "nature", "clinical", "sport", "minimal", "recovery",
          "ocean", "sunrise", "lavender", "midnight")
SCREENS = ("Watch face", "Vitality rewards", "Heart rate", "Activity", "Environment", "Settings")


def load_themes(root=ROOT):
    return [json.loads((root / "vitality_watch_assets" / "themes" / (name + ".json")).read_text(encoding="utf-8"))
            for name in THEMES]


def ease(progress):
    return 1 - (1 - max(0, min(1, progress))) ** 3


def wave(seconds):
    phase = (seconds * 1.2) % 1
    return sum(height * math.exp(-((phase - center) / width) ** 2)
               for center, width, height in ((.12, .055, 4), (.25, .022, -7),
                   (.30, .019, 24), (.35, .025, -12), (.58, .09, 6)))


class Rewards:
    """Local self-reported demo goals; sensor values never award points."""
    GOALS = ("Daily check-in", "Personal care goal", "Rest & recharge")

    def __init__(self, path=None, today=None):
        self.path = Path(path) if path else None
        self.today = today or (lambda: datetime.now().date().isoformat())
        self.date, self.completed, self.claimed = "", [False]*3, False
        self.message = "Small steps, at your own pace."
        if self.path and self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                done = data["completed"]
                if len(done) != 3 or any(type(item) is not bool for item in done):
                    raise ValueError("Invalid goals")
                self.date, self.completed = data["date"], done
                self.claimed = data.get("badge_claimed") is True and all(done)
            except (OSError, ValueError, KeyError, TypeError):
                self.message = "Starting a fresh rewards demo."
        self.refresh()

    @property
    def points(self):
        return sum(self.completed)*20

    def refresh(self):
        today = self.today()
        if self.date != today:
            self.date, self.completed, self.claimed = today, [False]*3, False
            self.message = "A fresh day. Start at your pace."

    def complete(self, index):
        self.refresh()
        if not 0 <= index < 3 or self.completed[index]:
            return False
        self.completed[index] = True
        self.message = "Your Balance badge is ready!" if self.points == 60 else "+20 points. Your effort counts."
        self.save()
        return True

    def claim(self):
        self.refresh()
        if self.points < 60 or self.claimed:
            return False
        self.claimed = True
        self.message = "Balance badge earned. Well done!"
        self.save()
        return True

    def save(self):
        if self.path is None:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps(dict(date=self.date, completed=self.completed,
                                                badge_claimed=self.claimed)), encoding="utf-8")
            temporary.replace(self.path)
        except OSError:
            self.message = "Progress is available this session only."


class Model:
    def __init__(self):
        self.screen, self.theme = 1, 0
        self.rewards = Rewards()
        self.simulated = self.live_clock = True
        self.sleeping = self.workout = False
        self.elapsed = self.entered = 0.0
        self.measure_started = None

    def tick(self, dt):
        self.rewards.refresh()
        if not self.sleeping:
            self.elapsed += max(0, min(dt, .2))

    def navigate(self, delta=0, screen=None):
        self.screen = (self.screen + delta) % len(SCREENS) if screen is None else screen
        self.sleeping = False
        self.entered = self.elapsed

    def theme_next(self, value=None):
        self.theme = (self.theme + 1) % len(THEMES) if value is None else value
        self.entered = self.elapsed

    def measure(self):
        if self.simulated:
            self.measure_started = self.elapsed

    @property
    def remaining(self):
        if self.measure_started is None:
            return 0
        return max(0, math.ceil(10 - (self.elapsed - self.measure_started)))

    def set_simulated(self, value):
        self.simulated = value
        if not value:
            self.workout = False
            self.measure_started = None


class InstanceLock:
    """OS-held advisory lock; automatically released even if the preview crashes."""
    def __init__(self, path):
        self.path = path
        self.file = None

    def acquire(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open("a+b")
        self.file.seek(0, 2)
        if not self.file.tell():
            self.file.write(b"0")
            self.file.flush()
        self.file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            self.file.close()
            self.file = None
            return False

    def close(self):
        if self.file:
            self.file.close()
            self.file = None


class Preview:
    def __init__(self, window, tk, persist_rewards=True):
        self.tk, self.window = tk, window
        self.model, self.themes = Model(), load_themes()
        if persist_rewards:
            self.model.rewards = Rewards(ROOT / "build" / "rewards-portable.json")
        self.last = time.monotonic()
        window.title("Vitality / Portable Watch Studio")
        self.app_icon = tk.PhotoImage(file=str(ROOT / "assets" / "app" / "vitality.png"))
        window.iconphoto(True, self.app_icon)
        window.configure(bg="#101917")
        window.resizable(False, False)
        self.canvas = tk.Canvas(window, width=940, height=710, bg="#101917", highlightthickness=0)
        self.canvas.pack()
        self.drag = None
        self.canvas.bind("<ButtonPress-1>", lambda e: setattr(self, "drag", (e.x, e.y)))
        self.canvas.bind("<ButtonRelease-1>", self.click)
        window.bind("<Left>", lambda e: self.model.navigate(-1))
        window.bind("<Right>", lambda e: self.model.navigate(1))
        window.bind("<Home>", lambda e: self.model.navigate(screen=0))
        window.bind("<space>", lambda e: self.toggle_sleep())
        self.frame()

    def text(self, x, y, value, size=14, color="#eaf4ef", anchor="center", bold=False):
        self.canvas.create_text(x, y, text=value, fill=color, anchor=anchor,
                                font=("Helvetica", -size, "bold" if bold else "normal"))

    def arc(self, x, y, diameter, color, width, start, sweep):
        if sweep <= 0:
            return
        self.canvas.create_arc(x, y, x + diameter, y + diameter, outline=color, width=width,
                               style="arc", start=-start, extent=-min(359.9, sweep))

    def face_text(self, x, y, value, size=14, color=None, bold=False):
        self.text(430 + x, 123 + y, value, size,
                  color or self.themes[self.model.theme]["text"], bold=bold)

    def mark(self, x, y, size):
        c, scale = self.canvas, size / 128
        def points(coords):
            return [v * scale + (x if i % 2 == 0 else y) for i, v in enumerate(coords)]
        c.create_polygon(points([64,113,42,95,39,48,12,27,44,20,65,49,66,91]),
                         fill="#00bcf2", smooth=True, splinesteps=24)
        c.create_polygon(points([64,113,68,59,82,33,116,19,116,58,98,83]),
                         fill="#21df9a", smooth=True, splinesteps=24)
        c.create_line(points([64,113,76,80,86,53,111,26]), fill="#c5ffe7", width=2, smooth=True)
        c.create_oval(x+53*scale,y+21*scale,x+73*scale,y+41*scale,fill="#16dcb0",outline="")

    def heart(self, x, y, size):
        points = []
        for i in range(80):
            t = 2 * math.pi * i / 80
            points.extend((x + size * (16 * math.sin(t)**3) / 32,
                           y - size * (13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t)) / 32))
        self.canvas.create_polygon(points, fill="#ff4975", outline="")

    def toggle_sleep(self):
        self.model.sleeping = not self.model.sleeping
        self.model.entered = self.model.elapsed
        self.draw()

    def click(self, e):
        m = self.model
        if self.drag and self.drag[0] > 400 and e.x > 400 and abs(e.x-self.drag[0]) > 65:
            m.navigate(1 if e.x < self.drag[0] else -1)
            return
        if 24 <= e.x <= 236:
            for i in range(6):
                if 165+i*51 <= e.y <= 209+i*51:
                    m.navigate(screen=i)
            if 518 <= e.y <= 550:
                m.set_simulated(not m.simulated)
            if 566 <= e.y <= 599:
                m.live_clock = not m.live_clock
        if 307 <= e.x < 922 and 620 <= e.y < 700:
            m.theme_next((e.y-620)//40*5+(e.x-307)//123)
        if not m.sleeping and m.screen == 1 and 530 <= e.x <= 796:
            y = e.y-123
            for i in range(3):
                if 228+i*39 <= y < 261+i*39:
                    m.rewards.complete(i)
            if 351 <= y < 389:
                m.rewards.claim()
        if 900 <= e.x <= 928 and 267 <= e.y <= 322:
            self.toggle_sleep()
        if not m.sleeping and 535 <= e.x <= 791 and 454 <= e.y <= 495:
            if m.screen == 2:
                m.measure()
            elif m.screen == 3 and m.simulated:
                m.workout = not m.workout
            elif m.screen == 5:
                m.theme_next()
        self.draw()

    def frame(self):
        now = time.monotonic()
        dt, self.last = now-self.last, now
        if self.window.state() != "iconic":
            self.model.tick(dt)
            if not self.model.sleeping:
                self.draw()
        self.window.after(33, self.frame)

    def draw(self):
        c, m = self.canvas, self.model
        th = self.themes[m.theme]
        c.delete("all")
        c.create_rectangle(0,0,264,710,fill="#15221e",outline="")
        self.mark(26,28,42)
        self.text(78,49,"vitality",27,anchor="w",bold=True)
        self.text(30,99,"WATCH STUDIO",10,"#7e9390",anchor="w")
        self.text(30,142,"EXPLORE YOUR WATCH",10,"#7e9390",anchor="w")
        for i, name in enumerate(SCREENS):
            y = 165 + i*51
            if m.screen == i:
                c.create_rectangle(24,y,239,y+44,fill="#283e32",outline="")
            self.text(38,y+22,str(i+1).zfill(2),11,"#a4e3b3",anchor="w")
            self.text(75,y+22,name,15,anchor="w")
        for name,on,y in (("Simulated sensors",m.simulated,535),("Computer clock",m.live_clock,582)):
            self.text(32,y,name,13,anchor="w")
            c.create_oval(207,y-9,239,y+9,fill="#7bcb91" if on else "#3c4941",outline="")
            x = 229 if on else 217
            c.create_oval(x-6,y-6,x+6,y+6,fill="#eef8f0",outline="")
        self.text(32,643,"Portable preview / simulated data",10,"#7e9390",anchor="w")
        self.text(308,44,"Small steps. Real encouragement.",26,anchor="w",bold=True)
        self.text(308,80,"Vitality rewards / personal goals, at your own pace.",14,"#7e9390",anchor="w")
        c.create_oval(415,108,911,604,fill="#526359",outline="#71847a",width=2)
        c.create_oval(423,116,903,596,fill="#050a08",outline="")
        c.create_oval(430,123,896,589,fill="#000000" if m.sleeping else th["bg"],outline="")
        c.create_rectangle(904,269,925,320,fill="#526359",outline="")
        for i, theme in enumerate(self.themes):
            x,y=307+i%5*123,620+i//5*40
            if i==m.theme:
                c.create_rectangle(x,y,x+119,y+36,fill="#2a3b30",outline="")
            c.create_oval(x+9,y+14,x+17,y+22,fill=theme["primary"],outline="")
            self.text(x+24,y+18,theme["name"].replace("Vitality ",""),11,anchor="w")
        if m.sleeping:
            self.face_text(233,233,"Sleeping",18,"#7e9390")
            return
        t=m.elapsed
        progress=ease((t-m.entered)/.9)
        self.arc(445,138,436,"#2c3d40",7,130,280)
        if m.simulated or m.screen == 1:
            outer_progress = 280*m.rewards.points/60 if m.screen == 1 else 230
            self.arc(445,138,436,th["primary"],7,130,outer_progress*progress)
            if outer_progress:
                self.arc(445,138,436,th["secondary"],7,130+(t*.2%1)*max(0,outer_progress-14)*progress,14*progress)
        self.mark(641,150,44)
        self.face_text(233,91,SCREENS[m.screen].upper(),13,th["muted"],True)
        now=datetime.now() if m.live_clock else datetime(2024,4,23,10,8)+timedelta(seconds=t)
        demo=lambda value: value if m.simulated else "--"
        if m.screen==0:
            if m.theme in (1,4):
                for i in range(12):
                    a=i*math.pi/6
                    c.create_line(663+math.sin(a)*145,346-math.cos(a)*145,
                                  663+math.sin(a)*151,346-math.cos(a)*151,fill=th["muted"],width=2)
                for a,length,width,color in (
                    ((now.hour%12+now.minute/60)*math.pi/6,93,5,th["text"]),
                    ((now.minute+now.second/60)*math.pi/30,133,3,th["text"]),
                    ((now.second+now.microsecond/1e6)*math.pi/30,138,1,th["secondary"])):
                    c.create_line(663,346,663+math.sin(a)*length,346-math.cos(a)*length,fill=color,width=width)
            else:
                self.face_text(233,210,now.strftime("%H:%M"),74,bold=True)
                self.face_text(233,263,now.strftime("%a, %d %b / %S").upper(),12,th["secondary"])
            for x,value,label in ((110,"72","BPM"),(233,"8,421","STEPS"),(356,"7h 24","SLEEP")):
                self.face_text(x,356,demo(value),23,bold=True)
                self.face_text(x,385,label,10,th["muted"])
            if m.simulated:
                self.heart(540,447,19+4*math.exp(-(((t*1.2)%1-.15)/.09)**2))
        elif m.screen==1:
            rewards=m.rewards
            self.arc(605,222,116,th["muted"],4,130,280)
            self.arc(605,222,116,th["secondary"],5,130,280*rewards.points/60*progress)
            radius=2+math.sin(t*2)
            c.create_oval(663-radius,228-radius,663+radius,228+radius,fill=th["primary"],outline="")
            self.face_text(233,151,str(rewards.points),49,bold=True)
            self.face_text(233,184,"OF 60 DAILY POINTS",9,th["muted"])
            self.face_text(233,212,"Tap a goal you completed today",11,th["secondary"])
            for i,label in enumerate(rewards.GOALS):
                y=351+i*39
                c.create_rectangle(530,y,796,y+33,fill=th["primary"] if rewards.completed[i] else th["bg"],
                                   outline=th["primary"])
                self.face_text(233,y-123+16,("Done  " if rewards.completed[i] else "+20  ")+label,
                               12,th["bg"] if rewards.completed[i] else th["text"],True)
            c.create_rectangle(548,474,778,512,fill=th["bg"],outline=th["secondary"])
            label="Balance badge earned" if rewards.claimed else "Claim Balance badge" if rewards.points==60 else "Balance badge / 60 pts"
            self.face_text(233,370,label,12,th["secondary"],True)
            self.face_text(233,403,rewards.message,10,th["muted"])
        elif m.screen==2:
            size=35+(7*math.exp(-(((t*1.2)%1-.15)/.09)**2) if m.simulated else 0)
            self.heart(663,268,size)
            self.face_text(233,218,demo("72"),72,bold=True)
            self.face_text(233,265,"BEATS PER MINUTE",10,th["muted"])
            if m.simulated:
                pts=[]
                for i in range(181):
                    pts.extend((520+i*1.6,421-wave(t-(180-i)/90)))
                c.create_line(pts,fill="#ff4975",width=2)
            if m.remaining:
                self.arc(629,234,68,th["primary"],3,t*200%360,85)
            self.button("Demo measuring ... "+str(m.remaining)+"s" if m.remaining else "Run demo measurement",th)
            self.face_text(233,397,"SpO2 "+demo("98%"),12,th["muted"])
        elif m.screen==3:
            self.face_text(233,213,demo("8,421"),62,bold=True)
            self.face_text(233,268,"SAMPLE STEP COUNT",11,th["muted"])
            c.create_line(537,417,789,417,fill="#28373c",width=7)
            if m.simulated:
                c.create_line(537,417,537+212*progress,417,fill=th["secondary"],width=7)
            self.button("Stop demo workout" if m.workout else "Start demo workout",th)
            self.face_text(233,397,"Workout active" if m.workout else "Follow your personal activity plan.",12,th["muted"])
        elif m.screen==4:
            self.face_text(233,217,demo("26°"),74,bold=True)
            self.face_text(233,270,"AMBIENT TEMPERATURE",10,th["muted"])
            self.face_text(150,337,demo("52%"),25,th["primary"])
            self.face_text(315,337,demo("118 m"),25,th["secondary"])
            self.face_text(150,367,"Humidity",11,th["muted"])
            self.face_text(315,367,"Altitude",11,th["muted"])
            self.face_text(233,402,"Skin temperature "+demo("33.4°C"),12,th["muted"])
        else:
            self.face_text(233,205,th["name"],33,bold=True)
            self.face_text(233,253,"MAKE IT YOURS",10,th["muted"])
            for i,theme in enumerate(self.themes):
                c.create_oval(518+i*30,399,540+i*30,421,fill=theme["primary"],outline="")
            self.button("Change watch theme",th)
            self.face_text(233,397,"Battery "+demo("78%")+" / Bluetooth unavailable",11,th["muted"])
        self.face_text(233,430,"DEMO REWARDS / SELF-REPORTED" if m.screen==1 else "SIMULATED DATA" if m.simulated else "NO SENSOR CONNECTION",9,th["muted"])

    def button(self, label, theme):
        self.canvas.create_rectangle(535,454,791,495,fill="#19373c",outline="")
        self.text(663,475,label,13,theme["primary"])


def main():
    try:
        import tkinter as tk
    except ImportError:
        print("Tk is missing. Install Python with Tk support (Ubuntu/Debian: python3-tk).", file=sys.stderr)
        return 1
    lock=InstanceLock(ROOT / "build" / "portable-preview.lock")
    if not lock.acquire():
        print("Vitality portable preview is already running.", flush=True)
        return 0
    try:
        try:
            window=tk.Tk()
        except tk.TclError as error:
            print("Cannot open a desktop window: " + str(error) +
                  ". Use a local desktop session; remote/headless sessions need a display.", file=sys.stderr)
            return 1
        Preview(window,tk)
        window.update_idletasks()
        print("Vitality portable preview ready.", flush=True)
        window.mainloop()
        return 0
    finally:
        lock.close()


if __name__=="__main__":
    raise SystemExit(main())
