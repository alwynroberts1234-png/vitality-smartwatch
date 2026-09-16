# Custom PCB integration gate

The schematic, GPIO mapping, oscillator choices, PMIC variant, AMOLED controller,
panel initialization sequence, touch interrupt/reset and flash wiring are not supplied.
There is deliberately no flashable board definition with invented pin numbers.

Use the upstream nrf52840dk/nrf52840 for the headless firmware milestone.
Its onboard flash capacity is NOT the proposed custom watch's 32 MiB flash.
Do not apply the watch memory layout to the development kit.

When the schematic is available:
1. Add a Zephyr hardware-model-v2 board (board.yml, DTS, defconfig, Kconfig and runners).
2. Define display and input devices, clocks, regulators and bus pinctrl.
3. Confirm flash ID, capacity, addressing, QSPI pins and erase geometry.
4. Define vitality_assets_partition and non-overlapping history/OTA partitions.
5. Merge config/ui.conf and config/qspi.conf only after those devices work.
6. Verify RGB565 byte order, round display cropping, touch coordinates and sleep/wake.
7. Measure link map, stack high-water marks, heap usage and display throughput.
8. Add MCUboot, signing and the confirmed update partition layout.

qspi_image/layout.json is a proposed allocation, not a programming command.
The full 32 MiB part needs addressing verification beyond the 16 MiB boundary.
Do not flash until that is tested against the exact flash part and controller configuration.
