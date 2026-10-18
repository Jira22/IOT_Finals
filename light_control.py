#!/usr/bin/env python3
"""
Smart Home IoT - Automatic Light (PIR motion + darkness)
Hardware: Raspberry Pi + PIR motion sensor + light sensor module (LDR) + relay

How it works
------------
A PIR sensor only detects MOTION, not darkness. So a light sensor (LDR
module) is used together with it:

  - Motion detected AND room is dark  -> light turns ON
  - No motion for LIGHT_TIMEOUT_S     -> light turns OFF

Once the light is on, the room becomes bright, so the code does NOT use
darkness to decide when to turn off. It only uses the no-motion timer.
Any motion while the light is on restarts that timer.

Wiring (BCM numbering)
----------------------
PIR sensor (e.g. HC-SR501):
    VCC -> 5V    (Pin 2)
    GND -> GND   (Pin 6)
    OUT -> GPIO27 (Pin 13)   (output is 3.3V, safe for the Pi)

LDR module with digital output (e.g. LM393 photoresistor module):
    VCC -> 3.3V  (Pin 17)
    GND -> GND   (Pin 20)
    DO  -> GPIO22 (Pin 15)
    (turn the small blue potentiometer on the module to set how dark
     "dark" is)

Light relay module:
    VCC -> 5V    (Pin 4)
    GND -> GND   (Pin 14)
    IN  -> GPIO5 (Pin 29)
    Light is wired through the relay's COM and NO terminals.
    NEVER connect a light or lamp directly to a GPIO pin. If you switch
    mains voltage, be careful or ask someone experienced.

Install (Raspberry Pi OS Bookworm, works on Pi 5):
    sudo apt install python3-gpiozero python3-lgpio
Run:
    python3 light_control.py
"""

import time
from gpiozero import MotionSensor, DigitalInputDevice, OutputDevice

# ----------------------------- Settings ---------------------------------
PIR_PIN = 27
LDR_PIN = 22
LIGHT_PIN = 5

LIGHT_TIMEOUT_S = 30      # turn light off after this many seconds without motion
POLL_INTERVAL_S = 0.5
PIR_WARMUP_S = 30         # PIR sensors need time to settle after power-up

# Most LM393 LDR modules output HIGH when it is dark. If your light turns on
# in bright rooms and not in dark ones, flip this value.
DARK_WHEN_HIGH = True

# Many relay modules switch ON when the input pin goes LOW (active-low).
# If your light is on when it should be off, flip this value.
RELAY_ACTIVE_HIGH = False

# --------------------------- Hardware setup ------------------------------
pir = MotionSensor(PIR_PIN)
ldr = DigitalInputDevice(LDR_PIN)
light = OutputDevice(LIGHT_PIN, active_high=RELAY_ACTIVE_HIGH, initial_value=False)


def is_dark() -> bool:
    return bool(ldr.value) == DARK_WHEN_HIGH


def on_light_change(is_on: bool) -> None:
    state = "ON" if is_on else "OFF"
    print(f"[{time.strftime('%H:%M:%S')}] Light {state}")
    # TODO: hook into the rest of your smart home system here
    # (MQTT publish, notification, logging, etc.)


def main() -> None:
    print(f"Warming up PIR sensor for {PIR_WARMUP_S}s (stay still)...")
    time.sleep(PIR_WARMUP_S)
    print(f"Ready. Light ON when motion + dark, OFF after {LIGHT_TIMEOUT_S}s "
          "without motion. (Ctrl+C to stop)")

    last_motion = 0.0

    while True:
        motion = pir.motion_detected

        if motion:
            # Turn on only if it is dark; if already on, keep it on.
            if not light.value and is_dark():
                light.on()
                on_light_change(True)
            if light.value:
                last_motion = time.time()  # restart the off-timer

        elif light.value and (time.time() - last_motion) >= LIGHT_TIMEOUT_S:
            light.off()
            on_light_change(False)

        time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        light.off()
        light.close()
        pir.close()
        ldr.close()
