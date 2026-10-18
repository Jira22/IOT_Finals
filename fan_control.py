#!/usr/bin/env python3
"""
Smart Home IoT - Temperature Controlled Fan
Hardware: Raspberry Pi + DHT11 temperature/humidity sensor + fan (via relay)

How it works
------------
The DHT11 is read every few seconds. When the temperature rises to
FAN_ON_TEMP_C or higher, the fan turns ON. It turns OFF again only when the
temperature drops to FAN_OFF_TEMP_C or lower. The gap between the two values
(hysteresis) stops the fan from rapidly switching on/off around one number.

Wiring (BCM numbering)
----------------------
DHT11 VCC  -> 3.3V (Pin 1)
DHT11 GND  -> GND  (Pin 9)
DHT11 DATA -> GPIO4 (Pin 7)
   (If you use the bare 4-pin DHT11, add a 10k ohm pull-up resistor between
    DATA and VCC. The 3-pin module version already has one built in.)

Fan relay module:
Relay VCC -> 5V   (Pin 4)
Relay GND -> GND  (Pin 14)
Relay IN  -> GPIO17 (Pin 11)
Fan is wired through the relay's COM and NO terminals.
NEVER connect a fan directly to a GPIO pin; the pin cannot supply enough
current. If you switch mains voltage, be careful or ask someone experienced.

Install (Raspberry Pi OS Bookworm, works on Pi 5):
    sudo apt install python3-libgpiod python3-gpiozero python3-lgpio
    pip install adafruit-circuitpython-dht --break-system-packages
  (or inside a venv created with:  python3 -m venv --system-site-packages venv)
Run:
    python3 fan_control.py
"""

import time
import board
import adafruit_dht
from gpiozero import OutputDevice

# ----------------------------- Settings ---------------------------------
DHT_PIN = board.D4          # GPIO4
FAN_PIN = 17                # GPIO17 -> relay IN

FAN_ON_TEMP_C = 30.0        # turn fan ON at or above this temperature
FAN_OFF_TEMP_C = 28.0       # turn fan OFF at or below this temperature
POLL_INTERVAL_S = 3         # DHT11 needs at least ~1-2 seconds between reads

# Many relay modules switch ON when the input pin goes LOW (active-low).
# If your fan runs when it should be off, flip this value.
RELAY_ACTIVE_HIGH = False

# --------------------------- Hardware setup ------------------------------
dht = adafruit_dht.DHT11(DHT_PIN)
fan = OutputDevice(FAN_PIN, active_high=RELAY_ACTIVE_HIGH, initial_value=False)


def read_dht(retries: int = 3):
    """Return (temperature_c, humidity) or (None, None) if all tries fail.
    The DHT11 often fails a read; this is normal, so we retry."""
    for _ in range(retries):
        try:
            return dht.temperature, dht.humidity
        except (RuntimeError, OverflowError, ValueError):
            time.sleep(2)  # checksum/timing error, try again
    return None, None


def on_fan_change(is_on: bool, temp: float) -> None:
    state = "ON" if is_on else "OFF"
    print(f"[{time.strftime('%H:%M:%S')}] Fan {state} (temp {temp:.1f} C)")
    # TODO: hook into the rest of your smart home system here
    # (MQTT publish, notification, logging, etc.)


def main() -> None:
    print(f"Fan ON at >= {FAN_ON_TEMP_C} C, OFF at <= {FAN_OFF_TEMP_C} C")
    print("Monitoring temperature... (Ctrl+C to stop)")

    while True:
        temp, humidity = read_dht()

        if temp is None:
            print("Sensor read failed, keeping fan state unchanged")
        else:
            print(f"Temp: {temp:.1f} C  Humidity: {humidity}%  "
                  f"Fan: {'ON' if fan.value else 'OFF'}")

            if temp >= FAN_ON_TEMP_C and not fan.value:
                fan.on()
                on_fan_change(True, temp)
            elif temp <= FAN_OFF_TEMP_C and fan.value:
                fan.off()
                on_fan_change(False, temp)

        time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        fan.off()
        fan.close()
        dht.exit()
