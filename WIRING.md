# Wiring checklist

Status (2026-10-21): stages 1-4 and 6 are wired. Stage 6 (ultrasonic) is not tested yet. Stage 5 (fan motor) and
stage 7 (water level) are postponed to the next lab visit, see TOMORROW.md. The LCD was dropped.

Pin numbers are the Pi's physical pins, with the BCM GPIO in brackets. The full pin map is in README.md.
The Pi is connected through the T-cobbler on board 1, so "Pin 7" means a jumper from the T-cobbler column of pin 7. The column of each pin and where every part sits on the two boards are in the "Breadboard layout" section of README.md.
Power the Pi off while wiring. Build the stages in order and test each one before the next.

Wire colours: red = 5V, orange = 3.3V, black = GND, anything else = signal.
Tick boxes: [x] done, [ ] still to do.

## Stage 1: Rails
- [x] Pi pin 2 (5V) -> 5V rail
- [x] Pi pin 6 (GND) -> GND rail
- [x] If using two breadboards: join their GND rails

## Stage 2: DHT11 (test: `fan_control.py` prints a temperature)
- [x] Pi pin 1 (3.3V) -> DHT11 VCC
- [x] GND rail -> DHT11 GND
- [x] Pi pin 7 (GPIO4) -> DHT11 DATA

## Stage 3: PIR + light LED (test: wave a hand, LED lights; `light_control.py`)
- [x] 5V rail -> PIR VCC
- [x] GND rail -> PIR GND
- [x] Pi pin 11 (GPIO17) -> PIR OUT
- [x] Pi pin 16 (GPIO23) -> 220 ohm -> LED long leg
- [x] LED short leg -> GND rail

## Stage 4: Door alarm LED (test: `door_sensor.py` startup blinks)
The buzzer circuit never worked, so the alarm is a red LED.
- [x] Pi pin 15 (GPIO22) -> 1k ohm -> red LED long leg
- [x] Red LED short leg -> GND rail

## Stage 5: Fan motor (test: warm the DHT11, motor starts)
- [ ] Pi pin 12 (GPIO18) -> 1k ohm -> S8050 base
- [ ] S8050 emitter -> GND rail
- [ ] S8050 collector -> motor (-)
- [ ] 5V rail -> motor (+)
- [ ] Diode across the motor, stripe towards 5V (1N4007), to absorb spikes

(Alternative to the transistor: a 5V relay for the fan, IN -> GPIO18, and set
`RELAY_ACTIVE_HIGH` in `fan_control.py` to match the module.)

## Stage 6: Ultrasonic HC-SR04 (test: `door_sensor.py` prints the baseline distance, not tested yet)
- [x] 5V rail -> HC-SR04 VCC
- [x] GND rail -> HC-SR04 GND
- [x] Pi pin 22 (GPIO25) -> HC-SR04 TRIG
- [x] HC-SR04 ECHO -> 1k ohm -> junction
- [x] Junction -> Pi pin 18 (GPIO24)
- [x] Junction -> 1k ohm -> GND rail (ECHO is 5V, this divider brings it to about 2.5V)

## Stage 7: Water level (test: `water_level.py`, dip the sensor, LED flickers)
- [ ] Pi pin 17 (3.3V) -> water sensor +  (3.3V, not 5V, so S stays safe for the Pi; pin 1 is used by the DHT11)
- [ ] GND rail -> water sensor -
- [ ] water sensor S -> Pi pin 13 (GPIO27)
- [ ] Pi pin 37 (GPIO26) -> 220-330 ohm -> LED long leg (resistor to be borrowed from the lab)
- [ ] LED short leg -> GND rail
