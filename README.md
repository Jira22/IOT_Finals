# IoT Final Project
Home assistant project: Smart room

**Features:**
- Light turns on when a person walks past the PIR sensor
- The fan turns on when the room is at a certain temperature
- The buzzer rings when the door has been open for 30 s, until the door is closed
- A light flickers when the water level is too high (water sensor)
- Home Assistant shows every sensor and can switch the light, the fan and the buzzer by hand

## Status (2026-10-21)
| Feature | Script | State |
|---|---|---|
| Temperature and humidity to HA | `fan_control.py` | working |
| Movement turns on the light (10 s) | `light_control.py` | working |
| Door open for 30 s: buzzer rings until closed | `door_sensor.py` | working |
| Fan turns on above 30 C | `fan_control.py` | working |
| Water level: LED flickers, HA shows Normal / High | `water_level.py` | working |
| HA switches for light, fan and buzzer | the scripts above | working, see "Home Assistant controls" |
| LCD | none | dropped |

## TRIG vs ECHO
- TRIG is an output from the Pi, which sends a short pulse to the sensor.
- ECHO is an input to the Pi, which listens for the sensor’s pulse.

## Items Borrowed (Some may not be used)
| Item | Amount |
| ----------- | ----------- |
| Red LED | 2 |
| White LED | 2 |
| PI GPIO | 1 |
| Raspberry pi 5 |  1 |
| DC Motor | 1 |
| Ultra sonic sensor | 1 |
| Buzzer (Passive) | 1 |
| Breadboard | 2 |
| Temperature/humid sensor | 1 |
| Mini-PIR module | 2 |
| Button | 1 |
| Switch | 1 |
| Set of wires | 1 |
| GPIO cable | 1 |
| DIP circuit | 1 |
| ESP32 board | 1 |
| LCD (dropped, not used) | 1 |
| Potentiometer (50k) | 1 |
| 1kΩ Resistor | 4 |
| 220Ω Resistor | 1 |
| NPN Transistor S8050 | 2 (one earlier one was broken) |
| Diode (1N4007) | 1 |


## GPIO Pin Map (BCM numbering) - single source of truth

| Function | Part | Signal | GPIO (BCM) | Physical pin |
|---|---|---|---|---|
| Fan | DHT11 | DATA (3.3V) | GPIO4 | 7 |
| Light | PIR 1 | OUT (5V) | GPIO17 | 11 |
| Light | LED | + (via 220Ω) | GPIO23 | 16 |
| Door | HC-SR04 | TRIG | GPIO25 | 22 |
| Door | HC-SR04 | ECHO (through 1kΩ/1kΩ divider) | GPIO24 | 18 |
| Door | Passive buzzer | S8050 base (via 1kΩ) | GPIO22 | 15 |
| Fan | DC motor | S8050 base (via 1kΩ) | GPIO18 | 12 |
| Water | Water sensor | S (sensor powered from 3.3V) | GPIO27 | 13 |
| Water | Red LED | + (via 220-330Ω) | GPIO26 | 37 |

## Breadboard layout (two boards joined side by side)

Both boards are full size, 63 columns. Board 1 carries the T-cobbler and the sensors. Board 2 carries the LEDs, resistors, the ECHO divider and the fan driver. A scaled drawing of both is on the wiring page (see the end of this file).

**T-cobbler (board 1, columns 1 to 20).** Physical pin n is in column ceil(n / 2). Odd pins reach the top half (rows a to e), even pins the bottom half (rows f to j). Pin 1 is drawn at the left end: check the labels printed on your T-cobbler for its orientation.

| Pin | Name | Column | Half | Goes to |
|---|---|---|---|---|
| 1 | 3.3V | 1 | top | DHT11 VCC (board 1, column 24) |
| 2 | 5V | 1 | bottom | bottom 5V rail |
| 6 | GND | 3 | bottom | bottom GND rail |
| 7 | GPIO4 | 4 | top | DHT11 DATA (column 25) |
| 9 | GND | 5 | top | top GND rail |
| 11 | GPIO17 | 6 | top | PIR OUT (column 30) |
| 12 | GPIO18 | 6 | bottom | fan resistor (board 2, column 29) |
| 13 | GPIO27 | 7 | top | water sensor S (column 36) |
| 15 | GPIO22 | 8 | top | buzzer driver (board 2, column 17) |
| 16 | GPIO23 | 8 | bottom | light LED resistor (board 2, column 11) |
| 17 | 3.3V | 9 | top | water sensor + (column 35) |
| 18 | GPIO24 | 9 | bottom | ECHO divider junction (board 2, column 6) |
| 22 | GPIO25 | 11 | bottom | HC-SR04 TRIG (column 25) |
| 37 | GPIO26 | 19 | top | water LED resistor (board 2, column 23) |

**Board 1 sensors**

| Sensor | Columns | Half | Pin order |
|---|---|---|---|
| DHT11 | 24 to 26 | top | VCC, DATA, GND |
| PIR | 29 to 31 | top | VCC, OUT, GND |
| Water sensor | 34 to 36 | top | -, +, S |
| HC-SR04 | 24 to 27 | bottom | VCC, TRIG, ECHO, GND |

Sensor GND and VCC go to the nearest rail: top rails for the top-half sensors, bottom rails for the HC-SR04. Pin order differs between modules, so read the labels printed on yours.

**Board 2 components (top half, rails at the top: GND first, then 5V)**

| Part | Columns | Notes |
|---|---|---|
| ECHO divider | 4 to 8 | ECHO in at column 4, 1k from 4 to 6 (junction), 1k from 6 to 8, column 8 to GND, column 6 to pin 18 |
| Light LED | 11 to 14 | pin 16 at column 11, 220 ohm from 11 to 13, LED anode 13, cathode 14 to GND |
| Water LED | 23 to 26 | pin 37 at column 23, 220-330 ohm from 23 to 25, LED anode 25, cathode 26 to GND |
| Fan driver | 29 to 33 | pin 12 at 29, 1k from 29 to 31 (B), E at 30 to GND, C at 32 to motor -, motor + and 5V at 33, diode across the motor with the stripe on the + side |
| Buzzer driver | 17 to 21 | pin 15 at 17, 1k from 17 to 19 (B), E at 18 to GND, C at 20 to buzzer -, buzzer + and 5V at 21 |

The buzzer and the fan each have their own S8050.

**Rail links**
- Board 1 top 5V to board 1 bottom 5V.
- Board 1 bottom GND to board 2 GND.
- Board 1 bottom 5V to board 2 5V.
- The ECHO wire runs from the HC-SR04 (board 1, column 26) to board 2, column 4.

Space: the T-cobbler takes 20 of the 63 columns on board 1 and the sensors about 16, which leaves about 26 columns free.

## Power
| From | To |
|---|---|
| Pi 3.3V (pin 1) | DHT11 VCC |
| Pi 3.3V (pin 17) | Water sensor + |
| Pi 5V (pin 2 / 4) | PIR 1 VCC, HC-SR04 VCC, motor +, buzzer + |
| Pi GND | DHT11, PIR, HC-SR04, LEDs (-), both S8050 emitters |

## S8050 motor
GPIO18 -- 1kΩ -- base; emitter -- GND; collector -- motor (-); 5V -- motor (+)
A diode (1N4007) goes across the motor, stripe towards 5V.

## S8050 buzzer
GPIO22 -- 1kΩ -- base; emitter -- GND; collector -- buzzer (-); 5V -- buzzer (+). The buzzer is passive, so it needs a tone (PWM), not steady power.
The S8050 pinout is E, B, C with the flat face towards you.

## Home Assistant controls
- The switches only send an MQTT message. The matching script must be running on the Pi, or nothing happens.
- **Light and fan:** a command from HA wins over the PIR and the temperature for 5 minutes (`MANUAL_HOLD_S`), then auto mode resumes.
- **Buzzer:** the switch rings the buzzer until it is switched off (`door_sensor.py`).
- **Water Level** is a text sensor (Normal / High), because a binary sensor can only show Wet / Dry.
- **Run everything:** `bash ~/IOT_Finals/run_all.sh` starts all four scripts, Ctrl+C stops them.
- **Test scripts:** `buzzer_test.py`, `led_test.py` and `ultrasonic_test.py` check one part each. Stop the main scripts first, since they hold the pins.

## Setup notes
- **DHT11 on the Pi 5:** the Adafruit library fails, so the kernel driver is used. Add `dtoverlay=dht11,gpiopin=4` to `/boot/firmware/config.txt` and reboot. `fan_control.py` reads `/sys/bus/iio/devices/iio:device*/`.
- **MQTT broker:** `MQTT_BROKER` in every script is the laptop's IP, which changes per network. Run `ipconfig` and update it.
- **Home Assistant:** entities are defined in `config/configuration.yaml` (MQTT). Restart HA after changing it.
- **Run a script on the Pi:** `python3 ~/IOT_Finals/<script>.py`
- **Upload from Windows:** `cd` into the folder and run `scp <file> teamnano@<Pi IP>:~/IOT_Finals/` (scp treats `C:` as a hostname).

## Wiring page
A scaled drawing of both boards and every single-feature diagram: https://claude.ai/artifact/HDc68QXtyAw4bNVkSajiid (private, ask the owner to share it).
