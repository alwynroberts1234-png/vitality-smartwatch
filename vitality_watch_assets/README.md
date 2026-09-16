# Vitality Watch Assets

Programming-ready source assets for the Vitality smartwatch UI.

Included:
- User-supplied Vitality logo cleaned for transparent use
- Multiple logo and mark sizes
- Recolorable SVG icon set
- 48/64/96 px PNG icon fallbacks
- Six theme JSON files
- C color-token header
- Six 466×466 watchface SVG sources
- Three lightweight animation sprite sheets + JSON metadata
- Font specification and LVGL integration notes

Target:
- nRF52840
- Zephyr / nRF Connect SDK
- LVGL
- 466×466 round AMOLED

Important:
- SVGs are source/design assets. Convert them to your final LVGL image format during the build.
- Animation sprite sheets may be too large for internal flash if kept uncompressed; use QSPI flash or generate the animation with LVGL primitives.
