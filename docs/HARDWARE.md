# Hardware contract from the supplied specification

These are the requested components, not a verified PCB or completed driver list.
Every hardware adapter is pending schematic and bench integration.

| Function | Requested component | Bus | Normalized output / intended rate |
|---|---|---|---|
| MCU | nRF52840-QIAA | — | Application, BLE; 1 MiB flash / 256 KiB RAM target |
| Flash | W25Q256JV | QSPI | 32 MiB; static assets, history, OTA staging |
| Display | 1.43 inch round AMOLED | SPI, module TBD | 466 × 466, RGB565 |
| Touch | CST816S | I²C + IRQ/reset | x/y/event in display coordinates |
| PPG | MAX30102 | I²C | Red/IR counts at 50–100 Hz; processed HR/SpO2 only after algorithm validation |
| IMU | BMI270 | I²C/SPI | Acceleration mg; gyro mdps; 25 Hz idle / 100 Hz workout |
| Skin | MAX30208 | I²C | °C × 100; 0.2–1 Hz |
| Environment | SHT40 | I²C | °C × 100, %RH × 100; 0.1–1 Hz |
| Pressure | BMP390 | I²C/SPI | Pa; 1–25 Hz; calibrated derived altitude in cm |
| Magnetometer | LIS2MDL | I²C | nT on 3 axes; 10–20 Hz; calibrated heading ° × 100 |
| Fuel gauge | MAX17048 | I²C | mV and percent; 10–60 s |
| RTC | RV-3028-C7 | I²C | Unix timestamp after time synchronization |
| Haptics | DRV2605L | I²C | LRA/ERM patterns; actuator TBD |
| PMIC | BQ25120A-class, exact part TBD | I²C/GPIO | Charger/regulators/charge interrupts |
| Battery | 3.7 V Li-Po | Power | 250–400 mAh target |

The current sample timestamp is monotonic uptime in milliseconds, not Unix time.
RTC/time sync must introduce an explicit mapping; never silently store uptime as wall time.
Axis values without validity bits are reserved and must not be displayed as readings.

Pending inputs: board revision, schematic, display module datasheet, pin assignments,
flash suffix and voltage, oscillator arrangement, PMIC, battery/actuator details.
No glucose estimate is implemented. Future validated CGM/ECG/EDA adapters must carry
provenance, measurement time, quality and availability through the sensor manager.
