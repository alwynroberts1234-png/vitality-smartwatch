# LVGL Integration Notes

Target display: 466×466 round AMOLED.

## Suggested directory mapping

assets/
├── logo/
├── fonts/
├── icons/
├── watchfaces/
├── animations/
└── themes/

## SVG conversion

For embedded production builds, convert SVGs to:
- LVGL binary image assets, or
- RGB565 / ARGB8888 C arrays, depending on memory budget.

Example using LVGL image converter:
- Keep SVG as the design source.
- Export 48, 64, or 96 px PNGs for runtime assets.
- Convert PNG to `lv_img_dsc_t` arrays during the build.

## Theme usage

`include/vitality_theme_tokens.h` contains compact color tokens.

Example:

```c
extern const vitality_theme_t THEME_VITALITY_FLOW;

lv_obj_set_style_bg_color(screen,
    lv_color_hex(THEME_VITALITY_FLOW.bg), 0);
```

## Animation sprite sheets

Each animation folder pair contains:
- `<name>_spritesheet.png`
- `<name>.json`

Read `frame_width`, `frame_height`, `frames`, and `fps` from the JSON file.

At 128×128 and 16 frames, the sprite sheets are intended as source assets.
For the nRF52840, strongly consider:
- reducing frame count,
- reducing resolution,
- external QSPI flash,
- or converting to vector/primitive animation in LVGL.

## Logo

Use:
- `vitality_mark_48.png` or `64.png` in status/boot elements.
- `vitality_logo_256.png` for documentation / full branding.
- monochrome mark variants for low-power / AOD modes.

## Color system

Default Vitality Flow:
- Background: #020B14
- Cyan: #00C8FF
- Green: #21E6A4
- Blue: #4F8CFF
- Text: #F7FBFF
- Muted: #8CA5B8
