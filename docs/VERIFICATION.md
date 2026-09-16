# Verification — 2026-09-16

Current startup is UI-only. Firmware source and optional manual build helpers are
retained; the automatic SDK downloader and VS Code firmware build task were removed.

Passed locally:
- UI-only startup: 13 Python tests ran, with 12 passing and one native Unix setup
  test skipped on Windows. The setup regression checks confirm there is no firmware
  task or SDK downloader and the Windows preparation stage needs zero downloads.
  PowerShell and Bash syntax checks passed. Windows preview render checks passed,
  and the complete Windows setup script launched the visible preview using only
  existing Windows components. No dependencies were installed for these checks.
- Portable launcher/UI: 10 regression tests passed on Windows, including OS task
  overrides, paths with spaces, build failure propagation, mock output validation,
  animation/state and duplicate-instance locks. A real hidden Tk window rendered
  all 36 screen/theme combinations and passed live timer/sleep checks.
  Linux/macOS CI jobs were added but not executed remotely in this session.
- VS Code task JSON and PowerShell scripts validated. Startup no longer checks for
  a Zephyr environment; Windows checks its .NET UI compiler. Folder-open requires VS Code
  reload/reopen and was not driven through the editor during these checks.
- Animation: changing rendered frames on all six screens, static sleeping display,
  no heart trace with sensors unavailable, transition start/midpoint/end, real
  WinForms timer ticks and pause during sleep. Inspected the three-frame heart strip.
- Windows .NET Framework compilation of WatchPreview.cs and VectorAssets.cs.
- Preview self-tests: navigation wrapping, unavailable/demo measurement behavior,
  completed measurement, and loading all six supplied themes.
- Rendered the studio, six faces and six screens. Inspected the studio, theme contact
  sheet and Heart screen. Replaced the original faint/tiny PNG glyphs with clean SVGs.
- AssetPacker generated 16 entries, 119,873 bytes (about 117 KiB).
- Standard CRC32 vector, pack round-trip, damaged magic, damaged payload,
  out-of-bounds offset and truncated-pack rejection.
- TinyCC compiled portable firmware components with -Wall -Werror.
- C tests passed: navigation/theme wrap, sleep/workout transitions, unavailable
  initial data, stale-sample rejection, demo scores, real-data score rejection,
  bounded asset reads, malformed pack rejection and integrity checks.
- The C asset reader opened and verified logo, heart and Nature theme entries
  in the actual C#-generated pack.

A portable TinyCC archive of 489,586 bytes was downloaded to .tools for C tests.
No extra UI framework or package was installed. The preview uses Windows .NET Framework.

Not run:
- A Zephyr cross-compilation/link or nRF Connect SDK build: SDK/toolchain absent.
- Hardware QSPI, display, touch, sensor, power, BLE or OTA tests.
- GitHub Actions: workflow supplied, not remotely executed.

Target builds remain unverified until the SDK is installed. The current repository
is a working desktop prototype and firmware foundation, not production watch firmware.

Reference APIs checked during implementation:
- [Zephyr nRF52840 DK](https://docs.zephyrproject.org/latest/boards/nordic/nrf52840dk/doc/index.html)
- [Pinned LVGL buffer configuration](https://github.com/zephyrproject-rtos/zephyr/blob/v4.1.0/modules/lvgl/Kconfig.memory)
- [LVGL9 image header](https://github.com/lvgl/lvgl/blob/v9.2.2/src/draw/lv_image_dsc.h)
- [LVGL9 image color formats](https://github.com/lvgl/lvgl/blob/v9.2.2/src/misc/lv_color.h)

Generated outputs: build/VitalityPreview.exe, build/screenshots, build/core_tests.exe,
build/preview-tests.txt, qspi_image/output/vitality_assets.bin and manifest.json.
