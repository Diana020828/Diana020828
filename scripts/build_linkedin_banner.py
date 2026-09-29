#!/usr/bin/env python3
"""Render Diana's LinkedIn profile banner in the "Nature distilled" system.

Layout rules taken from reviews of well-performing LinkedIn banners:
- 1584x396 px. The profile photo covers about 568x264 px of the lower-left
  corner on desktop, so that area only carries soft background shapes.
- Mobile shows roughly the central 60% of the width: the value proposition and
  the call to action live in the centre; the lead card on the right is support.
- LinkedIn prints the name right below the banner, so the banner states the
  outcome for the client plus a soft call to action.

Usage:
    python3 scripts/build_assets.py          # downloads the fonts into .fonts/
    python3 scripts/build_linkedin_banner.py

Requires Google Chrome for the headless screenshot.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from build_assets import (
    CLAY,
    CREAM,
    FONT_CACHE,
    LAVENDER,
    LAVENDER_SOFT,
    LINE,
    PAPER,
    PLUM,
    PLUM_SOFT,
    SAGE,
    SAGE_SOFT,
    TERRACOTTA,
)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "assets" / "linkedin-banner.png"
WIDTH, HEIGHT = 1584, 396

# (step, detail) of the lead journey shown on the card
STEPS = [
    ("New lead", "Web form, Meta Ads"),
    ("Added to the CRM", "GoHighLevel, tagged and assigned"),
    ("Call booked", "Calendar invite and reminders"),
]


def page() -> str:
    fonts = FONT_CACHE.resolve()
    steps = "".join(
        f"""
      <li class="{"active" if index == 0 else ""}">
        <b></b><div><strong>{step}</strong><span>{detail}</span></div>
      </li>"""
        for index, (step, detail) in enumerate(STEPS)
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
@font-face {{ font-family: Fraunces; src: url("file://{fonts}/Fraunces.ttf"); font-weight: 100 900; }}
@font-face {{ font-family: Fraunces; font-style: italic; src: url("file://{fonts}/Fraunces-Italic.ttf"); font-weight: 100 900; }}
@font-face {{ font-family: Instrument; src: url("file://{fonts}/InstrumentSans.ttf"); font-weight: 400 700; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ width: {WIDTH}px; height: {HEIGHT}px; overflow: hidden; position: relative;
        background: {CREAM}; font-family: Instrument, sans-serif; color: {PLUM}; }}
/* Soft organic shapes: the sage one sits under the profile photo */
.blob {{ position: absolute; border-radius: 50%; filter: blur(2px); }}
.blob--sage {{ left: -120px; bottom: -190px; width: 640px; height: 460px;
               background: radial-gradient(closest-side, {SAGE_SOFT}, transparent); }}
.blob--lavender {{ right: -140px; top: -200px; width: 720px; height: 520px;
                   background: radial-gradient(closest-side, {LAVENDER_SOFT}, transparent); }}
.copy {{ position: absolute; left: 600px; top: 68px; }}
.kicker {{ font-size: 19px; color: {PLUM_SOFT}; display: flex; align-items: center; gap: 10px; }}
.kicker::before {{ content: ""; width: 10px; height: 10px; border-radius: 50%; background: {TERRACOTTA}; }}
h1 {{ font-family: Fraunces, serif; font-weight: 500; font-size: 60px; line-height: 1.04;
      letter-spacing: -0.01em; margin-top: 12px; font-variation-settings: "opsz" 96, "SOFT" 100, "WONK" 0; }}
h1 em {{ color: {CLAY}; font-variation-settings: "opsz" 96, "SOFT" 100, "WONK" 1;
         background: linear-gradient(transparent 62%, {LAVENDER_SOFT} 62%, {LAVENDER_SOFT} 92%, transparent 92%); }}
.sub {{ font-size: 19px; color: {PLUM_SOFT}; margin-top: 14px; }}
.cta {{ display: inline-block; margin-top: 18px; padding: 10px 20px; border-radius: 999px;
        background: {PLUM}; color: {CREAM}; font-size: 17px; font-weight: 600; }}
.cta span {{ color: {LAVENDER}; }}
.card {{ position: absolute; right: 40px; top: 66px; width: 312px; padding: 18px 18px 14px;
         background: {PAPER}; border: 1.5px solid {LINE}; border-radius: 26px;
         box-shadow: 0 18px 40px -22px rgba(42, 27, 46, 0.35); }}
.card h2 {{ font-family: Fraunces, serif; font-weight: 500; font-size: 19px;
            display: flex; justify-content: space-between; align-items: center; }}
.card h2 i {{ font-family: Instrument, sans-serif; font-style: normal; font-size: 13px;
              background: {SAGE_SOFT}; padding: 3px 10px; border-radius: 999px; }}
.card ul {{ list-style: none; margin-top: 12px; position: relative; }}
.card ul::before {{ content: ""; position: absolute; left: 24px; top: 24px; bottom: 30px;
                    width: 2px; background: {LINE}; }}
.card li {{ display: flex; gap: 14px; align-items: center; padding: 9px 10px; border-radius: 16px;
            position: relative; }}
.card li.active {{ background: {LAVENDER_SOFT}; }}
.card li b {{ width: 28px; height: 28px; border-radius: 50%; border: 2px solid {PLUM};
              background: {PAPER}; flex: none; }}
.card li.active b {{ background: {TERRACOTTA}; border-color: {TERRACOTTA}; }}
.card strong {{ display: block; font-size: 16px; font-weight: 600; }}
.card span {{ font-size: 13px; color: {PLUM_SOFT}; }}
</style></head><body>
  <div class="blob blob--sage"></div>
  <div class="blob blob--lavender"></div>
  <div class="copy">
    <p class="kicker">Marketing automation &amp; growth</p>
    <h1>Every lead, followed up.<br><em>Automatically.</em></h1>
    <p class="sub">CRM, WhatsApp and email flows in n8n and GoHighLevel.</p>
    <p class="cta">Book a call <span>→</span> portfoliodiana.netlify.app</p>
  </div>
  <div class="card">
    <h2>A lead's first five minutes <i>Live</i></h2>
    <ul>{steps}
    </ul>
  </div>
</body></html>"""


def render(html: str, output: Path) -> None:
    """Screenshot an HTML page at banner size with headless Chrome."""
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if chrome is None:
        raise SystemExit("Google Chrome or Chromium is required to render the banner")
    with tempfile.TemporaryDirectory() as tmp:
        page_path = Path(tmp) / "banner.html"
        page_path.write_text(html, encoding="utf-8")
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--allow-file-access-from-files",
                f"--window-size={WIDTH},{HEIGHT}",
                f"--screenshot={output}",
                page_path.as_uri(),
            ],
            check=True,
            capture_output=True,
        )


def main() -> None:
    if not (FONT_CACHE / "Fraunces.ttf").exists():
        raise SystemExit("Fonts missing: run scripts/build_assets.py first")
    render(page(), OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
