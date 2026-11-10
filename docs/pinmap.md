# Pin map (build spec v1, RP2350-Zero)

| Signal | GPIO | Note |
|---|---|---|
| Display SCK | GP18 | SPI0 |
| Display MOSI | GP19 | SPI0 |
| Display DC | GP16 | |
| Display CS | GP17 | |
| Display RST | GP20 | |
| IMU SDA | GP4 | I2C0 |
| IMU SCL | GP5 | I2C0 |
| Button A | GP2 | active low, 10k pull-up |
| Button B | GP3 | active low, 10k pull-up |
| Button C | GP6 | active low, 10k pull-up |
| Piezo | GP7 | PWM |
| Motor | GP8 | via NPN transistor, flyback diode |

On the RP2350-Zero, GP16 to GP25 are on the castellated pads on the back of the board, not the side headers. Either wire the display to those pads or move the display to GP8 to GP15 on the side and update this table and `firmware/kinetic_echo/config.h`.

These are the pins in `kinetic_echo_ascii.ino` today (Arduino_RPiPicoSPI(16, 17, 18, 19): DC 16, CS 17, SCK 18, MOSI 19; GC9A01 RST 20; Wire SDA 4, SCL 5). Confirmed on the RP2350-Zero: _to be filled on 21 Nov 2026_.
