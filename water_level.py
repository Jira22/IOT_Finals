#!/usr/bin/env python3
import os
import time
import paho.mqtt.client as mqtt
from gpiozero import DigitalInputDevice, LED

# ----------------------------- Settings ---------------------------------
SENSOR_PIN = 27           # water sensor S pin, powered from 3.3V so it never exceeds 3.3V
LED_PIN = 26
FLICKER_S = 0.15
POLL_INTERVAL_S = 0.5

# MQTT Configuration: the laptop's IP, set with MQTT_BROKER=<ip> when starting, default below
MQTT_BROKER = os.environ.get("MQTT_BROKER", "192.168.99.90")
MQTT_PORT = 1883
TOPIC_AVAIL = "homeassistant/binary_sensor/water_level/availability"  # "offline" is sent by the broker if this script dies
TOPIC_WATER_STATE = "homeassistant/binary_sensor/water_level/state"

# --------------------------- Hardware setup ------------------------------
# shortcut: S is analog, used as a single on/off level; add an ADC for real level readings
sensor = DigitalInputDevice(SENSOR_PIN, pull_up=False)
led = LED(LED_PIN)

# --------------------------- MQTT setup ----------------------------------
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT Broker: {reason_code}")
    client.publish(TOPIC_AVAIL, "online", retain=True)
    client.publish(TOPIC_WATER_STATE, "High" if sensor.is_active else "Normal", retain=True)

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.will_set(TOPIC_AVAIL, "offline", retain=True)
mqtt_client.on_connect = on_connect

def set_water(high: bool) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] Water level {'HIGH' if high else 'normal'}")
    mqtt_client.publish(TOPIC_WATER_STATE, "High" if high else "Normal", retain=True)
    if high:
        led.blink(on_time=FLICKER_S, off_time=FLICKER_S)
    else:
        led.off()

def main() -> None:
    mqtt_client.connect_async(MQTT_BROKER, MQTT_PORT, 60)  # retries until the broker is up
    mqtt_client.loop_start()

    last = None
    print("Watching water level (Ctrl+C to stop)")
    while True:
        high = sensor.is_active
        if high != last:
            set_water(high)
            last = high
        time.sleep(POLL_INTERVAL_S)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        try:
            mqtt_client.publish(TOPIC_AVAIL, "offline", retain=True).wait_for_publish(2)
        except Exception:
            pass  # broker unreachable, nobody to tell
        mqtt_client.loop_stop()
        led.off()
        led.close()
        sensor.close()
