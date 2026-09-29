#!/usr/bin/env python3
"""Generate the animated SVG assets of Diana's profile README.

Same "Nature distilled" system as portfoliodiana.netlify.app: cream paper, plum
ink, terracotta, lavender and sage, Fraunces for display and Instrument Sans
for text. GitHub serves README images as <img>, so the SVGs only use CSS
animation (no JavaScript, no external fonts): each file embeds its own font
subset as a data URI, and text widths come from the real glyph metrics.

Usage:
    python3 scripts/build_assets.py

Fonts are downloaded once into .fonts/ (git-ignored). Requires fontTools.
"""

from __future__ import annotations

import base64
import io
import urllib.request
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONT_CACHE = ROOT / ".fonts"

CREAM = "#F6F1E7"
PAPER = "#FCF9F3"
LINE = "#DDD0BA"
PLUM = "#2A1B2E"
PLUM_SOFT = "#5C4B5F"
TERRACOTTA = "#D2553A"
CLAY = "#A63C24"
LAVENDER = "#B7A6E3"
LAVENDER_SOFT = "#E4DCF5"
SAGE = "#8DB39B"
SAGE_SOFT = "#DCE9DF"

OFL = "https://github.com/google/fonts/raw/main/ofl"
FONT_SOURCES = {
    # role: (file, url, variation instance)
    "display": (
        "Fraunces.ttf",
        f"{OFL}/fraunces/Fraunces%5BSOFT,WONK,opsz,wght%5D.ttf",
        {"wght": 500, "opsz": 96, "SOFT": 100, "WONK": 0},
    ),
    "italic": (
        "Fraunces-Italic.ttf",
        f"{OFL}/fraunces/Fraunces-Italic%5BSOFT,WONK,opsz,wght%5D.ttf",
        {"wght": 500, "opsz": 96, "SOFT": 100, "WONK": 1},
    ),
    "body": (
        "InstrumentSans.ttf",
        f"{OFL}/instrumentsans/InstrumentSans%5Bwdth,wght%5D.ttf",
        {"wght": 500, "wdth": 100},
    ),
    "bold": (
        "InstrumentSans.ttf",
        f"{OFL}/instrumentsans/InstrumentSans%5Bwdth,wght%5D.ttf",
        {"wght": 600, "wdth": 100},
    ),
}


class Face:
    """A static font instance that measures text and emits a subset @font-face."""

    def __init__(self, family: str, font: TTFont):
        self.family = family
        # Never rewrite the head timestamp, so reruns produce identical SVGs
        font.recalcTimestamp = False
        self.font = font
        self.cmap = font.getBestCmap()
        self.upem = font["head"].unitsPerEm
        self.used: set[str] = set()

    def width(self, text: str, size: float) -> float:
        missing = [char for char in text if ord(char) not in self.cmap]
        if missing:
            raise ValueError(f"{self.family} has no glyph for {missing!r}")
        hmtx = self.font["hmtx"]
        return sum(hmtx[self.cmap[ord(char)]][0] for char in text) * size / self.upem

    def use(self, text: str) -> str:
        self.used.update(text)
        return text

    def font_face(self) -> str:
        options = subset.Options()
        options.hinting = False
        options.layout_features = ["kern", "liga"]
        subsetter = subset.Subsetter(options)
        subsetter.populate(text="".join(sorted(self.used)))
        buffer = io.BytesIO()
        self.font.save(buffer)
        # Keep the head timestamp: identical input must produce identical SVGs
        font = TTFont(io.BytesIO(buffer.getvalue()), recalcTimestamp=False)
        subsetter.subset(font)
        out = io.BytesIO()
        font.save(out)
        data = base64.b64encode(out.getvalue()).decode("ascii")
        return f"@font-face{{font-family:'{self.family}';src:url(data:font/ttf;base64,{data}) format('truetype');}}"


def load_faces() -> dict[str, TTFont]:
    FONT_CACHE.mkdir(exist_ok=True)
    fonts: dict[str, TTFont] = {}
    for role, (filename, url, axes) in FONT_SOURCES.items():
        path = FONT_CACHE / filename
        if not path.exists():
            print(f"Downloading {filename}…")
            urllib.request.urlretrieve(url, path)
        fonts[role] = instancer.instantiateVariableFont(TTFont(path), axes)
    return fonts


def faces_for(fonts: dict[str, TTFont]) -> dict[str, Face]:
    """Each SVG embeds only the glyphs it uses."""
    return {role: Face(f"dp-{role}", font) for role, font in fonts.items()}


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def document(
    width: int, height: int, faces: dict[str, Face], css: str, body: str, label: str
) -> str:
    font_faces = "".join(face.font_face() for face in faces.values() if face.used)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}">
  <title>{esc(label)}</title>
  <style>
    {font_faces}
    {css}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>
{body}
</svg>
"""


BASE_CSS = """
    .rise { animation: rise 0.9s cubic-bezier(.16,1,.3,1) both; }
    @keyframes rise { from { transform: translateY(70px); } to { transform: none; } }
    .fade { animation: fade 0.8s ease-out both; }
    @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
"""


# ── Header: headline + live funnel card ───────────────────────────────

STAGES = [
    ("New lead", "Web form · Meta Ads"),
    ("Added to the CRM", "GoHighLevel · tagged and assigned"),
    ("WhatsApp reply", "Personal welcome in under a minute"),
    ("Call booked", "Calendar invite and reminders"),
]


def build_header(fonts: dict[str, TTFont]) -> str:
    faces = faces_for(fonts)
    display, italic, body, bold = (
        faces["display"],
        faces["italic"],
        faces["body"],
        faces["bold"],
    )
    width, height = 1200, 480

    size = 84
    lines = [
        ("Every lead,", display, PLUM, 196),
        ("followed up.", display, PLUM, 196 + 86),
        ("Automatically.", italic, CLAY, 196 + 172),
    ]
    italic_width = italic.width("Automatically.", size)

    headline = "".join(
        f"""
  <g clip-path="url(#l{i})">
    <text class="rise" style="animation-delay:{0.1 + i * 0.12:.2f}s" x="56" y="{y}" font-family="{face.family}" font-size="{size}" fill="{color}">{esc(face.use(text))}</text>
  </g>"""
        for i, (text, face, color, y) in enumerate(lines)
    )
    clips = "".join(
        f'<clipPath id="l{i}"><rect x="0" y="{y - 80}" width="700" height="104"/></clipPath>'
        for i, (_, _, _, y) in enumerate(lines)
    )

    # Funnel card (right). A plum chip walks down the four stages in a loop.
    cx, cy, cw = 752, 60, 400
    row_h, gap = 64, 10
    rows = []
    for i, (title, detail) in enumerate(STAGES):
        y = cy + 72 + i * (row_h + gap)
        rows.append(f"""
    <rect class="row row{i}" x="{cx + 16}" y="{y}" width="{cw - 32}" height="{row_h}" rx="18"/>
    <circle cx="{cx + 48}" cy="{y + row_h / 2}" r="17" fill="{PAPER}" stroke="{PLUM}" stroke-width="1.6"/>
    <text x="{cx + 80}" y="{y + 29}" font-family="{bold.family}" font-size="17" fill="{PLUM}">{esc(bold.use(title))}</text>
    <text x="{cx + 80}" y="{y + 50}" font-family="{body.family}" font-size="14" fill="{PLUM_SOFT}">{esc(body.use(detail))}</text>""")
    chip_label = "Laura M."
    chip_w = body.width(chip_label, 13) + 40
    first_y = cy + 72 + 8  # top line of the row, clear of the detail text
    card = f"""
  <rect x="{cx}" y="{cy}" width="{cw}" height="{72 + 4 * (row_h + gap) + 8}" rx="30" fill="{PAPER}" stroke="{LINE}" stroke-width="2"/>
  <text x="{cx + 24}" y="{cy + 44}" font-family="{display.family}" font-size="21" fill="{PLUM}">{esc(display.use("A lead's first five minutes"))}</text>
  <rect x="{cx + cw - 104}" y="{cy + 26}" width="80" height="26" rx="13" fill="{SAGE_SOFT}"/>
  <circle class="ping" cx="{cx + cw - 88}" cy="{cy + 39}" r="4" fill="{SAGE}"/>
  <text x="{cx + cw - 78}" y="{cy + 44}" font-family="{bold.family}" font-size="13" fill="{PLUM}">{esc(bold.use("Live"))}</text>
  <line x1="{cx + 48}" y1="{cy + 104}" x2="{cx + 48}" y2="{cy + 72 + 3 * (row_h + gap) + row_h / 2}" stroke="{LINE}" stroke-width="3"/>
  {"".join(rows)}
  <g class="chip">
    <rect x="{cx + cw - 32 - chip_w - 6}" y="{first_y}" width="{chip_w}" height="26" rx="13" fill="{PLUM}"/>
    <circle cx="{cx + cw - 32 - chip_w + 8}" cy="{first_y + 13}" r="9" fill="{CLAY}"/>
    <text x="{cx + cw - 32 - chip_w + 22}" y="{first_y + 17.5}" font-family="{body.family}" font-size="13" fill="{CREAM}">{esc(body.use(chip_label))}</text>
  </g>"""

    step = row_h + gap
    css = (
        BASE_CSS
        + f"""
    .row {{ fill: transparent; }}
    .row0 {{ animation: row0 8s infinite; }}
    .row1 {{ animation: row1 8s infinite; }}
    .row2 {{ animation: row2 8s infinite; }}
    .row3 {{ animation: row3 8s infinite; }}
    @keyframes row0 {{ 0%,24% {{ fill: {LAVENDER_SOFT}; }} 25%,92% {{ fill: {SAGE_SOFT}; }} 93%,100% {{ fill: {LAVENDER_SOFT}; }} }}
    @keyframes row1 {{ 0%,24% {{ fill: transparent; }} 25%,49% {{ fill: {LAVENDER_SOFT}; }} 50%,92% {{ fill: {SAGE_SOFT}; }} 93%,100% {{ fill: transparent; }} }}
    @keyframes row2 {{ 0%,49% {{ fill: transparent; }} 50%,74% {{ fill: {LAVENDER_SOFT}; }} 75%,92% {{ fill: {SAGE_SOFT}; }} 93%,100% {{ fill: transparent; }} }}
    @keyframes row3 {{ 0%,74% {{ fill: transparent; }} 75%,92% {{ fill: {LAVENDER_SOFT}; }} 93%,100% {{ fill: transparent; }} }}
    .chip {{ animation: chip 8s cubic-bezier(.5,0,.2,1) infinite; }}
    @keyframes chip {{
      0%,20% {{ transform: translateY(0); }}
      25%,45% {{ transform: translateY({step}px); }}
      50%,70% {{ transform: translateY({2 * step}px); }}
      75%,92% {{ transform: translateY({3 * step}px); }}
      96%,100% {{ transform: translateY(0); opacity: 1; }}
    }}
    .ping {{ animation: ping 1.6s ease-out infinite; transform-box: fill-box; transform-origin: center; }}
    @keyframes ping {{ 0% {{ transform: scale(1); opacity: 1; }} 100% {{ transform: scale(2.4); opacity: 0; }} }}
"""
    )
    body_svg = f"""
  <defs>{clips}
    <filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="50"/></filter>
  </defs>
  <rect width="{width}" height="{height}" fill="{CREAM}"/>
  <circle cx="1120" cy="60" r="200" fill="{LAVENDER_SOFT}" filter="url(#soft)"/>
  <circle cx="60" cy="460" r="170" fill="{SAGE_SOFT}" filter="url(#soft)"/>
  <circle cx="64" cy="92" r="5" fill="{TERRACOTTA}"/>
  <text class="fade" x="80" y="98" font-family="{body.family}" font-size="18" fill="{PLUM_SOFT}">{esc(body.use("Diana Pinzon · Marketing automation & growth"))}</text>
  <rect class="fade" style="animation-delay:.5s" x="54" y="{lines[2][3] - 30}" width="{italic_width + 8:.1f}" height="26" fill="{LAVENDER_SOFT}"/>
  {headline}
  <text class="fade" style="animation-delay:.6s" x="58" y="{lines[2][3] + 62}" font-family="{body.family}" font-size="19" fill="{PLUM}">{esc(body.use("n8n · GoHighLevel · HubSpot · Django · Next.js — Colombia, remote"))}</text>
  {card}"""
    return document(
        width,
        height,
        faces,
        css,
        body_svg,
        "Diana Pinzon — Every lead, followed up. Automatically.",
    )


# ── Section banners ───────────────────────────────────────────────────

SECTIONS = [
    ("01", "The system", "I build", "system"),
    ("02", "What I", "can do for you", "services"),
    ("03", "Selected", "work", "work"),
    ("04", "Tools I", "reach for", "tools"),
    ("05", "Where I", "work", "experience"),
    ("06", "Why a psychologist", "writes workflows", "background"),
]
ACCENTS = [LAVENDER_SOFT, SAGE_SOFT, "#EDE4D3", LAVENDER_SOFT, SAGE_SOFT, "#EDE4D3"]


def build_section(
    fonts: dict[str, TTFont], index: str, title: str, em: str, accent: str
) -> str:
    faces = faces_for(fonts)
    display, italic, bold = faces["display"], faces["italic"], faces["bold"]
    width, height, size = 1200, 120, 54
    title_w = display.width(title + " ", size)
    body = f"""
  <rect width="{width}" height="{height}" fill="{CREAM}"/>
  <rect x="0" y="0" width="{width}" height="{height}" rx="0" fill="{accent}" opacity="0.55"/>
  <rect x="40" y="{height / 2 - 20}" width="56" height="40" rx="20" fill="{PLUM}"/>
  <text x="68" y="{height / 2 + 6}" text-anchor="middle" font-family="{bold.family}" font-size="17" fill="{CREAM}">{esc(bold.use(index))}</text>
  <g clip-path="url(#t)">
    <g class="rise">
      <text x="118" y="{height / 2 + 18}" font-family="{display.family}" font-size="{size}" fill="{PLUM}">{esc(display.use(title))}</text>
      <text x="{118 + title_w:.1f}" y="{height / 2 + 18}" font-family="{italic.family}" font-size="{size}" fill="{CLAY}">{esc(italic.use(em))}</text>
    </g>
  </g>
  <defs><clipPath id="t"><rect x="0" y="8" width="{width}" height="{height - 16}"/></clipPath></defs>
  <circle cx="1150" cy="{height / 2}" r="7" fill="{TERRACOTTA}"/>"""
    return document(width, height, faces, BASE_CSS, body, f"{index} — {title} {em}")


# ── Footer ────────────────────────────────────────────────────────────


def build_footer(fonts: dict[str, TTFont]) -> str:
    faces = faces_for(fonts)
    display, italic, body = faces["display"], faces["italic"], faces["body"]
    width, height, size = 1200, 260, 72
    lead = "Let's automate "
    lead_w = display.width(lead, size)
    body_svg = f"""
  <defs><filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="40"/></filter>
    <clipPath id="f"><rect x="0" y="40" width="{width}" height="110"/></clipPath></defs>
  <clipPath id="card"><rect width="{width}" height="{height}" rx="44"/></clipPath>
  <g clip-path="url(#card)">
    <rect width="{width}" height="{height}" fill="{LAVENDER}"/>
    <circle cx="1100" cy="40" r="140" fill="{TERRACOTTA}" opacity="0.28" filter="url(#soft)"/>
  </g>
  <g clip-path="url(#f)">
    <g class="rise">
      <text x="64" y="128" font-family="{display.family}" font-size="{size}" fill="{PLUM}">{esc(display.use(lead))}</text>
      <text x="{64 + lead_w:.1f}" y="128" font-family="{italic.family}" font-size="{size}" fill="{CLAY}">{esc(italic.use("the busywork."))}</text>
    </g>
  </g>
  <text class="fade" style="animation-delay:.4s" x="66" y="190" font-family="{body.family}" font-size="21" fill="{PLUM}">{esc(body.use("Tell me which task your team repeats every day — a 30-minute call is enough to start."))}</text>"""
    return document(
        width, height, faces, BASE_CSS, body_svg, "Let's automate the busywork."
    )


def main() -> None:
    fonts = load_faces()
    ASSETS.mkdir(exist_ok=True)
    outputs = {"header.svg": build_header(fonts), "footer.svg": build_footer(fonts)}
    for (index, title, em, slug), accent in zip(SECTIONS, ACCENTS):
        outputs[f"section-{slug}.svg"] = build_section(fonts, index, title, em, accent)
    for name, content in outputs.items():
        (ASSETS / name).write_text(content, encoding="utf-8")
        print(f"assets/{name}  {len(content.encode()) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
