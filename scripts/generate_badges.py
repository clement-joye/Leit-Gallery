"""
Badge SVG generator for Leit Gallery.

Generates static SVG badge files for each gallery entry.
These are committed to the repo and served via GitHub Pages.

Usage:
    python scripts/generate_badges.py
"""

import json
import os
from pathlib import Path

GALLERY_DATA = Path(__file__).parent.parent / "src" / "data" / "gallery.json"
OUTPUT_DIR = Path(__file__).parent.parent / "public" / "badges"


def generate_badge_svg(name: str, genre: str) -> str:
    """Generate an SVG badge for a repository."""
    genre_label = genre.replace("_", " ").title()
    # Calculate width based on text content
    text = f"♪ Hear {name}"
    text_width = len(text) * 6.5 + 20
    genre_width = len(genre_label) * 6.5 + 16
    total_width = text_width + genre_width + 8

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{int(total_width)}" height="28" viewBox="0 0 {int(total_width)} 28">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#1e1b4b"/>
      <stop offset="100%" style="stop-color:#312e81"/>
    </linearGradient>
  </defs>
  <rect rx="6" width="{int(total_width)}" height="28" fill="url(#bg)"/>
  <rect rx="6" width="{int(total_width)}" height="28" fill="none" stroke="#7c3aed" stroke-opacity="0.4" stroke-width="1"/>
  <!-- Play icon -->
  <circle cx="12" cy="14" r="5" fill="#8b5cf6" opacity="0.8"/>
  <polygon points="11,12 14,14 11,16" fill="white"/>
  <!-- Repo name -->
  <text x="22" y="18" font-family="Arial,sans-serif" font-size="11" font-weight="600" fill="#e9d5ff">{text[2:]}</text>
  <!-- Genre pill -->
  <rect x="{int(text_width)}" y="5" rx="4" width="{int(genre_width)}" height="18" fill="#7c3aed" opacity="0.3"/>
  <text x="{int(text_width + 8)}" y="18" font-family="Arial,sans-serif" font-size="10" fill="#c4b5fd">{genre_label}</text>
</svg>"""


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(GALLERY_DATA, "r") as f:
        data = json.load(f)

    for entry in data["entries"]:
        svg = generate_badge_svg(entry["name"], entry["genre"])
        output_path = OUTPUT_DIR / f"{entry['slug']}.svg"
        with open(output_path, "w") as f:
            f.write(svg)
        print(f"  ✓ {output_path.name}")

    print(f"\nGenerated {len(data['entries'])} badges in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
