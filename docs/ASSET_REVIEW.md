# Supplied asset review

Original inputs are preserved in assets.png, vitality_watch_assets.zip and the
extracted vitality_watch_assets directory.

Retained:
- All six source theme JSON files; the desktop preview reads these directly.
- Original icons and watchface SVGs as reference material.
- Original animation JSON and sprite sheets for future animation work.

Changed for the active build:
- Supplied PNG icons appeared as tiny white glyphs, including a letter for steps.
  They were unsuitable for a crisp live display, especially the light Clinical theme.
- The supplied logo PNG had jagged light fringes. A clean editable vector
  approximation of the leaf/person mark now lives in assets/masters/vitality_mark.svg.
- Nine colored SVG icons were recreated in assets/masters.
- Watchfaces use dynamic text/arcs/hands instead of the original SVGs' baked-in
  10:08 time and health values. Nature and Minimal have analog desktop layouts.

These are new vector interpretations of the supplied direction, not exact reproductions
of the detailed photographic/leaf backgrounds in assets.png.

tools/VectorAssets.cs is a strict renderer for the curated SVG subset used by these
masters: paths with M/L/C/Z, circles, ellipses, rectangles, lines and linear gradients.
It is not a general-purpose SVG renderer. New complex artwork must be simplified to
the supported subset or rasterized with a complete SVG tool before pipeline integration.
Do not edit the generated PNGs or binary files as masters.

Runtime images use LVGL9 RGB565A8 (RGB565 color plane plus an 8-bit alpha plane).
The 12-byte LVGL9 image header is included; raw RGB565 without this header cannot be
passed to lv_image_set_src. Small icons preserve alpha on all six backgrounds.
Animations currently use no sprite-sheet RAM or flash; animation playback remains pending.
