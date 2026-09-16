# Architecture and implementation status

The implemented first milestone is a portable firmware core, a Zephyr headless
application, an optional LVGL UI, a QSPI asset path, and an independent Windows design preview.

| Area | Implemented | Remaining |
|---|---|---|
| Application | Pure C state machine, bounded Zephyr event queue, separate simulated sensor thread | Real button/touch event producer; inactivity timers |
| Data | Units, validity flags, explicit simulator provenance; stale samples rejected | Sensor adapters, quality/freshness policy, validated processing |
| UI | Six screens, six theme palettes, LVGL primitives, bounded partial buffers | Rich parity with desktop preview, full app menu, touch gestures, RTC time |
| Assets | SVG masters → LVGL9 RGB565A8 → checksummed VPK1; bounded flash reads; Q: bridge | Board provisioning, hardware flash measurements |
| Power | Active/idle/sleep/workout state transitions; display blanking API | PMIC, wake sources, coordinated device PM and current measurements |
| BLE | Planned service contract below | All BLE transport and phone integration |
| History | Proposed partition and record contract | LittleFS, wear/corruption recovery, storage worker |
| OTA | Proposed staging space | MCUboot integration, signing, authenticated BLE DFU, rollback tests |
| Desktop | Windows Forms preview, interactive screens/themes/workout/demo measurement, sleep | It is not an LVGL emulator or the firmware executable |

## Data flow and ownership

Sensor thread → copied snapshot in k_msgq → app state → LVGL.
Only the main/UI thread touches LVGL. Queue capacity is 16; enqueue is non-blocking
and overflow is logged. The portable state machine has no driver dependencies.
No-simulator builds start with no valid measurements and show unavailable values.
No fake physical sensor drivers return successful readings.

The score is an explicitly simulated fixture:
35% movement + 30% recovery + 20% heart + 15% balance, rounded to an integer.
Real measurements never automatically produce a score. Sleep/HRV/recovery algorithms
are intentionally unimplemented at this milestone.

## Memory

The 466 × 466 RGB565 full frame is 434,312 bytes, too large for 256 KiB RAM.
config/ui.conf requests two partial buffers at 8% of the frame each: roughly
69,490 bytes combined, plus alignment. LVGL heap is 24 KiB. Actual stack/BLE/driver
usage must be inspected in the final link map. Do not use a screen-sized canvas.
LVGL 9 lv_color_t must not be assumed to occupy two bytes; the display format and
Zephyr buffer byte count are configured explicitly.

VPK1 is a packed read-only image in external flash, not a filesystem image.
The Q: bridge translates names into bounded offsets. CRCs are checked on open;
they detect accidental corruption, not malicious updates. Four concurrent asset
handles and a 256-byte verification scratch buffer bound this subsystem's memory.
Large watchface graphics are not compiled into MCU flash.

## Corrected boot sequence

Zephyr device/clock/log initialization → board PMIC/buses → QSPI probe →
storage/settings → display + LVGL initialization → boot animation →
sensors → BLE → application. The current minimal app relies on Zephyr's LVGL auto-init
and starts directly at home; animated boot/storage/BLE phases are future work.
An LVGL boot animation cannot precede initialization of LVGL.

## Future services

BLE: Battery, Heart Rate, Device Information, a versioned custom Vitality service,
notifications, authenticated time synchronization and MCUboot-compatible DFU.
Define units, lengths, endianness, permissions and unavailable-value semantics before shipping.

History: versioned little-endian records with explicit serialization and CRC.
Do not dump a native C struct with compiler padding into flash. Scaled integers
are preferred; timestamp source and validity need to be part of each record.

OTA: separate partition ownership, signed images, power-loss recovery and rollback.
The desktop demonstration does not claim a connected phone or an installed update.
