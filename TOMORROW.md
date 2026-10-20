# Next lab visit

## Bring / get from the lab
- [ ] 1 resistor, 220-330 ohm, for the water LED (1k also works but is dim)
- [ ] A few spare 1k resistors (all four are in use: door LED, fan transistor, 2 for the ultrasonic divider)
- [ ] 1N4007 diode for the fan motor (or the 5V relay module instead)
- [ ] Water sensor (red board, from the teacher's list), if not already borrowed
- [ ] Multimeter

## Layout checks (two boards, T-cobbler on board 1)
- [ ] Board 1 has the T-cobbler at columns 1 to 20; check the printed labels to see which end is pin 1
- [ ] Count the columns on your boards (the plan assumes 63 each) and that the T-cobbler body leaves rows a to c and h to j free
- [ ] The sensors, LEDs and fan driver follow the column tables in README.md ("Breadboard layout")
- [ ] The three rail links are in (board 1 top 5V to bottom 5V, bottom GND to board 2, bottom 5V to board 2)
- [ ] The ECHO wire goes from the HC-SR04 to the divider on board 2

## Before powering the Pi
- [ ] Run `ipconfig` on the laptop and note its IPv4 address
- [ ] Put it in `MQTT_BROKER` in `fan_control.py`, `light_control.py`, `door_sensor.py` and `water_level.py`
- [ ] Check no rail shorts: 5V rail to GND rail must not beep on continuity
- [ ] Docker is running (HA and Mosquitto), then `docker restart homeassistant` so HA loads the water and humidity sensors

## 1. Upload the scripts
```powershell
cd C:\Users\wasin\IoT_proj\IOT_Finals; scp *.py teamnano@<Pi IP>:~/IOT_Finals/
```
- [ ] On the Pi, `wc -c ~/IOT_Finals/fan_control.py` prints the same size as on the laptop

## 2. Ultrasonic sensor (already wired)
- [ ] Quick test: prints a distance that changes when you move your hand
  ```bash
  python3 -c "
  from gpiozero import DistanceSensor
  import time
  s = DistanceSensor(echo=24, trigger=25, max_distance=2)
  for _ in range(10):
      print(round(s.distance*100,1), 'cm')
      time.sleep(0.5)
  "
  ```
- [ ] Mount it facing the door, with the door closed
- [ ] `python3 ~/IOT_Finals/door_sensor.py`: baseline prints, the red LED on GPIO22 blinks on open and close
- [ ] Door open for 30 s: the LED blinks repeatedly. HA `Door` card changes state

## 3. Fan motor (stage 5 in WIRING.md)
- [ ] Wire it: S8050 plus 1k plus diode, or the 5V relay
- [ ] Base strip reads about 0.7 V with `pinctrl set 18 op dh` (it read 3 V last time, so check the emitter to GND and the base strip)
- [ ] `pinctrl set 18 op dh` spins the motor, `dl` stops it, the transistor stays only warm
- [ ] If it still fails: use the relay and set `RELAY_ACTIVE_HIGH` in `fan_control.py` to match
- [ ] `fan_control.py`: the fan starts above 30 C (hold the DHT11 to test), stops below 28 C

## 4. Water level (stage 7 in WIRING.md)
- [ ] Before the script: measure the sensor's S pin while dipping it. It should rise above about 1.8 V
- [ ] If it never gets that high: use the ESP32 plan instead
- [ ] Wire + to pin 17, - to GND, S to pin 13, LED with the new resistor on pin 37
- [ ] `python3 ~/IOT_Finals/water_level.py`: dip the sensor, the LED flickers, HA `Water Level High` turns on

## 5. Home Assistant
- [ ] Temperature, humidity, motion, door and light show real values on the Smart Room dashboard
- [ ] Add `Water Level High` (`binary_sensor.water_level_high`) to the dashboard
- [ ] In the dashboard YAML the buzzer entity is `switch.buzzer_alarm`; the buzzer was replaced by an LED, so remove that card or leave it
- [ ] Switch the light and the fan manually from HA

## 6. Finish
- [ ] Run all four scripts together once (one terminal each)
- [ ] Ask the group before committing/pushing the repo changes (pin map, scripts, docs) to GitHub
