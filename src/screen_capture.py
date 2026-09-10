import io
import tkinter as tk
from typing import Optional

import mss
from PIL import Image

Region = tuple[int, int, int, int]


def select_region() -> Optional[Region]:
    result = {}

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-alpha", 0.3)
    root.attributes("-topmost", True)
    root.configure(bg="black")

    canvas = tk.Canvas(root, cursor="cross", bg="grey", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    start = {}
    rect_id = {}

    def on_press(event):
        start["x"], start["y"] = event.x, event.y
        rect_id["id"] = canvas.create_rectangle(
            event.x, event.y, event.x, event.y, outline="#ff4444", width=2
        )

    def on_drag(event):
        canvas.coords(rect_id["id"], start["x"], start["y"], event.x, event.y)

    def on_release(event):
        x1, x2 = sorted((start["x"], event.x))
        y1, y2 = sorted((start["y"], event.y))
        result["region"] = (x1, y1, x2, y2)
        root.destroy()

    def on_escape(_event):
        result["region"] = None
        root.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", on_escape)

    root.mainloop()
    return result.get("region")


def capture_region(region: Region) -> bytes:
    x1, y1, x2, y2 = region
    with mss.mss() as sct:
        monitor = {"left": x1, "top": y1, "width": x2 - x1, "height": y2 - y1}
        shot = sct.grab(monitor)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
