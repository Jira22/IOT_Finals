# IoT Final Project
Home assistant project: Smart room

**Features:**
- Lights turn on when the room is dark
- The fan turns on when the room is at a certain temperature
- A screen that displays the room temperature and humidity
- Alert when the door is opened for too long

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
| LCD | 1 |
| Potentiometer (50k) | 1 |
| 1kΩ Resistor | 4 |
| 220Ω Resistor | 1 |
| NPN Transistor S8050 | 1 |


## Wiring diagram
| Wire from | Wire to |
| ----------- | ----------- |
| Pi 3.3V (physical pin 1) | DHT11 VCC |
| Pi GND (pin 6) | DHT11 GND |
| Pi GPIO4 (pin 7) | DHT11 DATA |
| Pi 5V (pin 2) | PIR 1 VCC |
| Pi GND (pin 9)  | PIR 1 GND |
| Pi GPIO17 (pin 11) | PIR 1 OUT |
| Pi 5V (pin 4)  | PIR 2 VCC |
| Pi GND (pin 14) | PIR 2 GND |
| Pi GPIO27 (pin 13) | PIR 2 OUT |
| Pi GPIO23 (pin 16) | 330Ω resistor → LED (+) |
| LED (−)  |  GND |
| Pi GPIO22 (pin 15) 1kΩ resistor | buzzer S8050 base |
| Pi GPIO18 (pin 12) 1kΩ resistor | motor S8050 base |

## LCD connection lines
| LCD pin |  Connect to |
| ----------- | ----------- |
| 1 VSS | GND |
| 2 VDD | 5V |
| 3 VO | 10kΩ potentiometer middle pin |
| 4 RS | GPIO5 (pin 29) |
| 5 RW | GND |
| 6 E | GPIO6 (pin 31) |
| 11 D4 | GPIO12 (pin 32) |
| 12 D5 | GPIO13 (pin 33) |
| 13 D6 | GPIO16 (pin 36) |
| 14 D7 | GPIO19 (pin 35) |
| 15 A | Backlight positive (current limiting as required) |
| 16 K | GND |

## S8050 Buzzer connection lines
Raspberry Pi GPIO22 ── 1kΩ ── S8050 Base

Raspberry Pi GND ──────────── S8050 Emitter

S8050 Collector ───────────── Buzzer (−)

5V supply (+) ─────────────── Buzzer (+)

## S8050 motor connection lines
Raspberry Pi GPIO18 ── 1kΩ ── S8050 Base

Raspberry Pi GND ──────────── S8050 Emitter

S8050 Collector ───────────── Motor (−)
