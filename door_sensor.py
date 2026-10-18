#!/usr/bin/env python3
"""
Smart Home IoT - Door Open/Close Detector
Hardware: Raspberry Pi + HC-SR04 ultrasonic sensor + buzzer

How it works
------------
The ultrasonic sensor is mounted facing the door (or the gap where the door
swings). At start-up it measures the "door closed" distance as a baseline.
If the distance changes by more than THRESHOLD_CM for several readings in a
row, the door is considered OPEN. When the distance returns to the baseline,
the door is considered CLOSED. The buzzer sounds on each state change.

Wiring (BCM numbering)
----------------------
HC-SR04 VCC  -> 5V   (Pin 2)
HC-SR04 GND  -> GND  (Pin 6)
HC-SR04 TRIG -> GPIO23 (Pin 16)
HC-SR04 ECHO -> GPIO24 (Pin 18)  *** through a voltage divider ***
                  ECHO -> 1k ohm -> GPIO24 -> 2k ohm -> GND
                  (ECHO outputs 5V, Pi GPIO tolerates only 3.3V)
Buzzer (+)   -> GPIO18 (Pin 12)  (active buzzer; use a transistor if it is
Buzzer (-)   -> GND               high-current)

Install (Raspberry Pi OS, works on Pi 3/4/5/Zero):
    sudo apt install python3-gpiozero python3-lgpio
Run:
    python3 door_sensor.py
"""

import time
import statistics
from gpiozero import DistanceSensor, Buzzer

# ----------------------------- Settings ---------------------------------
TRIG_PIN = 23
ECHO_PIN = 24
BUZZER_PIN = 18

MAX_DISTANCE_M = 2.0     # sensor range limit in meters
THRESHOLD_CM = 10.0      # change from baseline that counts as "door moved"
CONFIRM_READINGS = 3     # consecutive readings needed to confirm a change
SAMPLES_PER_READING = 5  # readings are median-filtered to reduce noise
POLL_INTERVAL_S = 0.2    # delay between checks
CALIBRATION_TIME_S = 3   # time to measure the closed-door baseline

# Door-left-open alarm
DOOR_OPEN_ALARM_S = 30   # sound the alarm if the door stays open this long
ALARM_REPEAT_S = 2.0     # seconds between alarm bursts while it keeps ringing
ALARM_BEEPS = 5          # fast beeps per burst (different from open/close beeps)

# --------------------------- Hardware setup ------------------------------
sensor = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN, max_distance=MAX_DISTANCE_M)
buzzer = Buzzer(BUZZER_PIN)


def read_distance_cm() -> float:
    """Return a noise-filtered distance in cm (median of several samples)."""
    samples = []
    for _ in range(SAMPLES_PER_READING):
        samples.append(sensor.distance * 100)  # gpiozero returns meters
        time.sleep(0.03)
    return statistics.median(samples)


def beep(times: int = 1, on: float = 0.15, off: float = 0.1) -> None:
    for _ in range(times):
        buzzer.on()
        time.sleep(on)
        buzzer.off()
        time.sleep(off)


def calibrate() -> float:
    """Measure the baseline distance while the door is closed."""
    print(f"Calibrating for {CALIBRATION_TIME_S}s - keep the door CLOSED...")
    readings = []
    end = time.time() + CALIBRATION_TIME_S
    while time.time() < end:
        readings.append(read_distance_cm())
        time.sleep(0.1)
    baseline = statistics.median(readings)
    print(f"Baseline distance (door closed): {baseline:.1f} cm")
    return baseline


def on_door_open() -> None:
    print(f"[{time.strftime('%H:%M:%S')}] Door OPENED")
    beep(times=3)  # 3 beeps = opened
    # TODO: hook into the rest of your smart home system here
    # (MQTT publish, send notification, log to database, etc.)


def on_door_close() -> None:
    print(f"[{time.strftime('%H:%M:%S')}] Door CLOSED")
    beep(times=1, on=0.4)  # 1 long beep = closed
    # TODO: hook into the rest of your smart home system here


def on_door_alarm(open_for_s: float) -> None:
    """Called once when the door has been open longer than DOOR_OPEN_ALARM_S."""
    print(f"[{time.strftime('%H:%M:%S')}] ALARM: door open for {open_for_s:.0f}s")
    # TODO: hook into the rest of your smart home system here
    # (send a phone notification, MQTT message, etc.)


def main() -> None:
    baseline = calibrate()
    door_open = False
    change_count = 0
    open_since = None        # time the door was opened
    alarm_active = False     # True once the open-too-long alarm has started
    last_alarm_beep = 0.0

    print(f"Alarm if the door stays open for {DOOR_OPEN_ALARM_S}s")
    print("Monitoring door... (Ctrl+C to stop)")
    beep(times=2, on=0.05, off=0.05)  # ready signal

    while True:
        distance = read_distance_cm()
        deviates = abs(distance - baseline) > THRESHOLD_CM

        # A reading "disagrees" with the current state if the door appears
        # open while we think it is closed, or vice versa.
        if deviates != door_open:
            change_count += 1
        else:
            change_count = 0

        if change_count >= CONFIRM_READINGS:
            door_open = deviates
            change_count = 0
            if door_open:
                open_since = time.time()
                on_door_open()
            else:
                if alarm_active:
                    print("Door closed - alarm stopped")
                open_since = None
                alarm_active = False
                on_door_close()

        # Door-left-open alarm: keeps ringing until the door is closed
        if door_open and open_since is not None:
            open_for = time.time() - open_since
            if open_for >= DOOR_OPEN_ALARM_S:
                if not alarm_active:
                    alarm_active = True
                    on_door_alarm(open_for)
                if time.time() - last_alarm_beep >= ALARM_REPEAT_S:
                    beep(times=ALARM_BEEPS, on=0.1, off=0.1)
                    last_alarm_beep = time.time()

        time.sleep(POLL_INTERVAL_S)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        buzzer.off()
        sensor.close()
        buzzer.close()
