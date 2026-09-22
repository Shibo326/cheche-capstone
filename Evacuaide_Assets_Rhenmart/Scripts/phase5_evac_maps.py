"""
EVACUAIDE - Phase 5: Bilingual SVG Evacuation Maps
==================================================
Generates 5 clean, minimal SVG floor maps matching the
"MANILA INNOVATIONS TOWER" reference: bilingual (FIL/EN) room labels,
green emergency exit routes, red hazard/pantry markers, blue stairwell,
yellow assembly area, and a per-floor legend. Sized for Unity UI Canvas.

Run:  python phase5_evac_maps.py
Outputs to ../EvacuationMaps:
    EvacMap_Floor01.svg ... EvacMap_Floor05.svg
"""

import os

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()
ROOT = os.path.dirname(SCRIPT_DIR)
MAP_DIR = os.path.join(ROOT, "EvacuationMaps")
os.makedirs(MAP_DIR, exist_ok=True)

# ---- palette (matches reference) ----
C_EXIT = "#2E7D32"      # green route
C_HAZARD = "#D32F2F"    # red hazard / pantry
C_STAIR = "#1565C0"     # blue stairwell
C_ASSEMBLY = "#F2C200"  # yellow assembly
C_ROOM = "#FFFFFF"
C_STROKE = "#111111"
C_DESK = "#9AA0A6"
C_TITLE = "#000000"

W, H = 1024, 768
MARGIN = 24


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class Svg:
    def __init__(self):
        self.parts = []

    def rect(self, x, y, w, h, fill=C_ROOM, stroke=C_STROKE, sw=2, rx=0):
        self.parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}" rx="{rx}"/>')

    def line(self, x1, y1, x2, y2, stroke=C_STROKE, sw=2, dash=None, marker=False):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#arrow)"' if marker else ""
        self.parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
            f'stroke-width="{sw}"{d}{m}/>')

    def polyline(self, pts, stroke=C_EXIT, sw=5, marker=True):
        p = " ".join(f"{x},{y}" for x, y in pts)
        m = ' marker-end="url(#arrow)"' if marker else ""
        self.parts.append(
            f'<polyline points="{p}" fill="none" stroke="{stroke}" '
            f'stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round"{m}/>')

    def circle(self, cx, cy, r, fill, stroke=C_STROKE, sw=2):
        self.parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>')

    def text(self, x, y, s, size=13, anchor="middle", weight="normal", fill="#000"):
        self.parts.append(
            f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" '
            f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
            f'fill="{fill}">{esc(s)}</text>')

    def room(self, x, y, w, h, fil, en, fill=C_ROOM):
        self.rect(x, y, w, h, fill=fill)
        cx, cy = x + w / 2, y + h / 2
        self.text(cx, cy - 2, fil, size=12, weight="bold")
        self.text(cx, cy + 14, en, size=10, fill="#444")

    def desk(self, x, y):
        self.rect(x, y, 34, 22, fill=C_DESK, sw=1)

    def render(self):
        body = "\n  ".join(self.parts)
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}">
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="7" refY="3"
            orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L7,3 L0,6 Z" fill="{C_EXIT}"/>
    </marker>
  </defs>
  <rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>
  {body}
</svg>'''


def header(s, title_fil, title_en):
    s.rect(MARGIN, MARGIN, W - 2 * MARGIN, 60, fill="#FFFFFF", stroke=C_STROKE, sw=3)
    s.text(W / 2, MARGIN + 26, "MANILA INNOVATIONS TOWER", size=24, weight="bold")
    s.text(W / 2, MARGIN + 48, f"{title_fil}  /  {title_en}", size=13, fill="#333")


def legend(s):
    lx, ly = MARGIN + 8, H - 96
    s.text(lx, ly - 8, "LEGEND", size=13, weight="bold", anchor="start")
    items = [
        (C_EXIT, "Ruta ng Paglabas / Emergency Exit Route", "line"),
        (C_HAZARD, "Mapanganib na Lugar / Hazard Zone", "box"),
        (C_STAIR, "Hagdanan / Stairwell", "box"),
        (C_ASSEMBLY, "Tipunang Lugar / Assembly Area", "dot"),
    ]
    for i, (col, label, kind) in enumerate(items):
        yy = ly + 10 + i * 20
        if kind == "line":
            s.line(lx, yy, lx + 26, yy, stroke=col, sw=5, marker=True)
        elif kind == "dot":
            s.circle(lx + 13, yy, 8, col)
        else:
            s.rect(lx, yy - 8, 26, 16, fill=col, sw=1)
        s.text(lx + 36, yy + 4, label, size=11, anchor="start")


def frame(s):
    # building outline
    s.rect(MARGIN, MARGIN + 72, W - 2 * MARGIN, H - MARGIN - 200,
           fill="#F7F7F7", stroke=C_STROKE, sw=3)


def stairwell(s, x, y, w=90, h=110):
    s.rect(x, y, w, h, fill=C_STAIR)
    for i in range(5):
        s.line(x + 8, y + 15 + i * 18, x + w - 8, y + 15 + i * 18,
               stroke="#FFFFFF", sw=2)
    s.text(x + w / 2, y + h + 14, "HAGDANAN", size=9, weight="bold", fill=C_STAIR)
    s.text(x + w / 2, y + h + 25, "STAIRWELL", size=8, fill=C_STAIR)


def hazard(s, x, y, fil="PANTRY", en="KUSINA"):
    s.rect(x, y, 46, 46, fill=C_HAZARD)
    s.text(x + 23, y + 62, fil, size=9, weight="bold", fill=C_HAZARD)
    s.text(x + 23, y + 73, en, size=8, fill=C_HAZARD)


def assembly(s, x, y):
    s.circle(x, y, 22, C_ASSEMBLY)
    s.text(x, y + 40, "TIPUNAN", size=9, weight="bold", fill="#8a6d00")
    s.text(x, y + 51, "ASSEMBLY", size=8, fill="#8a6d00")


# ---------------- floor builders ----------------
def cubicle_grid(s, x0, y0, cols, rows, gx=70, gy=64):
    for r in range(rows):
        for c in range(cols):
            s.desk(x0 + c * gx, y0 + r * gy)


def floor1(s):
    header(s, "Unang Palapag (Ground Floor)", "Lobby & Reception")
    frame(s)
    # rooms
    s.room(80, 180, 150, 90, "RESEPSYON", "Reception")
    s.room(80, 300, 150, 90, "SEGURIDAD", "Security")
    s.room(430, 170, 140, 80, "ELEBEYTOR", "Elevators", fill="#E8E8E8")
    s.room(430, 270, 140, 80, "ELEBEYTOR", "Elevators", fill="#E8E8E8")
    s.room(600, 200, 150, 80, "TANGGAPAN", "Front Desk")
    stairwell(s, 610, 330, 100, 120)
    # exits + routes
    s.text(250, 165, "LABAS / EXIT", size=11, weight="bold", fill=C_EXIT, anchor="start")
    s.polyline([(300, 250), (400, 250), (400, 430), (760, 430)])
    s.polyline([(300, 340), (300, 500), (780, 500)])
    s.text(70, 445, "LABAS / EXIT", size=11, weight="bold", fill=C_EXIT, anchor="start")
    assembly(s, 860, 300)
    assembly(s, 900, 470)
    legend(s)


def open_office(s, title_fil, title_en, tech=False, meetings=False):
    header(s, title_fil, title_en)
    frame(s)
    # left + right cubicle clusters
    cubicle_grid(s, 90, 200, 3, 4)
    cubicle_grid(s, 760, 200, 2, 4)
    # center pantry hazard
    hazard(s, 470, 210)
    # stairwell center-left
    stairwell(s, 430, 320)
    if tech:
        s.room(650, 180, 150, 70, "KWARTO TEKNIKAL", "Tech Room", fill="#DDDDDD")
        s.room(650, 300, 150, 70, "KWARTO TEKNIKAL", "Tech Room", fill="#DDDDDD")
    if meetings:
        for i in range(3):
            s.room(340 + i * 150, 150, 130, 70, "PULONG", "Meeting Room", fill="#EFEFEF")
    # evac routes to stairwell then down
    s.polyline([(180, 380), (420, 380)])
    s.polyline([(820, 380), (540, 380)])
    s.polyline([(475, 445), (475, 560), (520, 560)])
    s.text(520, 566, "PABABA / DOWN", size=10, weight="bold", fill=C_EXIT, anchor="start")
    assembly(s, 900, 300)
    legend(s)


def floor5(s):
    header(s, "Ika-limang Palapag (Fifth Floor)", "Executive Suites")
    frame(s)
    s.room(80, 180, 150, 80, "OPISINA NG CEO", "CEO Office")
    s.room(80, 290, 150, 80, "OPISINA NG CEO", "CEO Office")
    s.room(250, 150, 160, 70, "PAGPAPAHINGAHAN", "Private Lounge")
    s.room(600, 150, 150, 70, "LUXURY OFFICE", "Luxury Office")
    s.room(770, 180, 150, 80, "IBANG OPISINA", "Other Office")
    hazard(s, 560, 300, "PANTRY", "KUSINA")
    stairwell(s, 430, 300)
    s.polyline([(180, 400), (420, 400)])
    s.polyline([(690, 400), (540, 400)])
    s.polyline([(475, 425), (475, 560), (520, 560)])
    s.text(520, 566, "PABABA / DOWN", size=10, weight="bold", fill=C_EXIT, anchor="start")
    assembly(s, 900, 300)
    legend(s)


FLOORS = [
    ("EvacMap_Floor01.svg", floor1),
    ("EvacMap_Floor02.svg", lambda s: open_office(
        s, "Ikalawang Palapag (Second Floor)", "Open Office Zone")),
    ("EvacMap_Floor03.svg", lambda s: open_office(
        s, "Ikatlong Palapag (Third Floor)", "Open Office + Tech Zone", tech=True)),
    ("EvacMap_Floor04.svg", lambda s: open_office(
        s, "Ika-apat na Palapag (Fourth Floor)", "Open Office + Meeting Rooms",
        meetings=True)),
    ("EvacMap_Floor05.svg", floor5),
]


def main():
    for fname, builder in FLOORS:
        s = Svg()
        builder(s)
        with open(os.path.join(MAP_DIR, fname), "w", encoding="utf-8") as f:
            f.write(s.render())
        print("Wrote", fname)
    print("DONE maps:", len(FLOORS))


if __name__ == "__main__":
    main()
