"""Opt-in smoke check for a local desktop with Tk installed."""
import importlib.util
from pathlib import Path
import time
import tkinter as tk

def main():
    root_path=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location("watch",root_path/"preview"/"watch_preview.py")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    window=tk.Tk()
    window.withdraw()
    try:
        app=module.Preview(window,tk,persist_rewards=False)
        for theme in range(len(app.themes)):
            app.model.theme=theme
            for screen in range(6):
                app.model.screen=screen
                app.draw()
                window.update_idletasks()
                assert len(app.canvas.find_all())>30
        before=app.model.elapsed
        end=time.monotonic()+.18
        while time.monotonic()<end:
            window.update()
            time.sleep(.005)
        assert app.model.elapsed>before, "Live Tk timer did not advance"
        app.toggle_sleep()
        before=app.model.elapsed
        end=time.monotonic()+.1
        while time.monotonic()<end:
            window.update()
            time.sleep(.005)
        assert app.model.elapsed==before, "Sleep should pause animation"
        assert any(app.canvas.itemcget(i,"text")=="Sleeping"
                   for i in app.canvas.find_all() if app.canvas.type(i)=="text")
        print("PASS: Tk draws all 60 screen/theme combinations; live timer and sleep pause.")
    finally:
        window.destroy()

if __name__ == "__main__":
    main()
