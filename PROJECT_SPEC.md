# Vitality Watch — project contract

Build a watch for nRF52840 with a 466×466 round AMOLED, CST816S touch,
32 MiB W25Q256JV QSPI NOR, Zephyr, LVGL and the supplied Vitality visual identity.
The detailed input is archived in docs/SOURCE_SPEC.txt.

The agreed initial deliverable is firmware plus a runnable desktop UI preview.
Prioritize the supplied specification's first milestone: simulated sensor data and
separate, replaceable hardware interfaces before physical health sensors.

Required architecture:
1. Drivers never call UI code; UI consumes application state.
2. Normalize measurements and include availability, units and simulated provenance.
3. Communicate through a bounded event queue; account for overflow.
4. Keep SVGs as masters and place larger runtime assets in QSPI.
5. Use Q: paths for LVGL assets; no UI raw flash offsets.
6. Partial RGB565 display buffers; no full framebuffer on nRF52840.
7. Implement hardware suspend/resume when real adapters are added.
8. Treat MCUboot/BLE DFU, storage, BLE and sensors as separate integration milestones.
9. Keep portable components testable without hardware.
10. No fabricated glucose readings; future validated CGM interface only.

Visual direction: dark AMOLED-friendly surfaces; blue/cyan/green leaf/person identity;
daily vitality rings; readable health metrics; Flow, Nature, Clinical, Sport, Minimal,
Recovery. Prototype screens: Watch Face, Vitality, Heart, Activity, Environment, Settings.

Default demo readings: HR 72 BPM, SpO2 98%, steps 8421, skin 33.4°C, ambient 26°C,
humidity 52%, altitude 118 m, battery 78%, vitality 82. These are simulated fixtures.

Blocked hardware decisions: exact display controller/module and initialization,
PCB GPIOs, clocks, power rails/PMIC, interrupts and precise flash configuration.
Do not invent them. Headless nRF52840 DK build is the initial hardware-independent path.

Acceptance for this repository milestone: runnable preview, source-driven themes and
clean assets, deterministic pack generation, portable firmware state/data/asset core,
Zephyr application/configuration, optional LVGL/QSPI adapters, meaningful tests and
honest separation between tested desktop code and pending target integration.
