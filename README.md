# IoT Final Project
Home assistant project: Smart room

**Features:**
- Light turns on when a person walks past the PIR sensor
- The fan turns on when the room is at a certain temperature
- Red LED blinks when the door is open for too long
- A light flickers when the water level is too high (water sensor)

## Status (2026-10-21)
| Feature | Script | State |
|---|---|---|
| Temperature and humidity to HA | `fan_control.py` | working |
| Movement turns on the light (10 s) | `light_control.py` | working |
| Door open too long: red LED blinks | `door_sensor.py` | wired, not tested |
| Fan turns on above 30 C | `fan_control.py` | motor circuit postponed |
| Water level: LED flickers | `water_level.py` | postponed (needs a resistor) |
| LCD | none | dropped |

See TOMORROW.md for the next lab session and WIRING.md for the wire-by-wire checklist.

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
| NPN Transistor S8050 | 1 |


## GPIO Pin Map (BCM numbering) - single source of truth

| Function | Part | Signal | GPIO (BCM) | Physical pin |
|---|---|---|---|---|
| Fan | DHT11 | DATA (3.3V) | GPIO4 | 7 |
| Light | PIR 1 | OUT (5V) | GPIO17 | 11 |
| Light | LED | + (via 220Ω) | GPIO23 | 16 |
| Door | HC-SR04 | TRIG | GPIO25 | 22 |
| Door | HC-SR04 | ECHO (through 1kΩ/1kΩ divider) | GPIO24 | 18 |
| Door | Red alarm LED | + (via 1kΩ) | GPIO22 | 15 |
| Fan | DC motor | S8050 base (via 1kΩ) | GPIO18 | 12 |
| Water | Water sensor | S (sensor powered from 3.3V) | GPIO27 | 13 |
| Water | Red LED | + (via 220-330Ω) | GPIO26 | 37 |

## Power
| From | To |
|---|---|
| Pi 3.3V (pin 1) | DHT11 VCC |
| Pi 3.3V (pin 17) | Water sensor + |
| Pi 5V (pin 2 / 4) | PIR 1 VCC, HC-SR04 VCC, motor + |
| Pi GND | DHT11, PIR, HC-SR04, LEDs (-), S8050 emitter |

## S8050 motor
GPIO18 -- 1kΩ -- base; emitter -- GND; collector -- motor (-); 5V -- motor (+)
A diode (1N4007) goes across the motor, stripe towards 5V. A 5V relay is the fallback.
(Only 1 S8050 was borrowed, and it is used for the motor.)

## Setup notes
- **DHT11 on the Pi 5:** the Adafruit library fails, so the kernel driver is used. Add `dtoverlay=dht11,gpiopin=4` to `/boot/firmware/config.txt` and reboot. `fan_control.py` reads `/sys/bus/iio/devices/iio:device*/`.
- **MQTT broker:** `MQTT_BROKER` in every script is the laptop's IP, which changes per network. Run `ipconfig` and update it.
- **Home Assistant:** entities are defined in `config/configuration.yaml` (MQTT). Restart HA after changing it.
- **Run a script on the Pi:** `python3 ~/IOT_Finals/<script>.py`
- **Upload from Windows:** `cd` into the folder and run `scp <file> teamnano@<Pi IP>:~/IOT_Finals/` (scp treats `C:` as a hostname).
