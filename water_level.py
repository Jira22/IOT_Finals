#!/usr/bin/env python3
import time
import paho.mqtt.client as mqtt
from gpiozero import DigitalInputDevice, LED

# ----------------------------- Settings ---------------------------------
SENSOR_PIN = 27           # water sensor S pin, powered from 3.3V so it never exceeds 3.3V
LED_PIN = 26
FLICKER_S = 0.15
POLL_INTERVAL_S = 0.5

# MQTT Configuration (CHANGE TO YOUR LAPTOP'S IP ADDRESS)
MQTT_BROKER = "192.168.99.90"
MQTT_PORT = 1883
TOPIC_WATER_STATE = "homeassistant/binary_sensor/water_level/state"

# --------------------------- Hardware setup ------------------------------
# shortcut: S is analog, used as a single on/off level; add an ADC for real level readings
sensor = DigitalInputDevice(SENSOR_PIN, pull_up=False)
led = LED(LED_PIN)

# --------------------------- MQTT setup ----------------------------------
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT Broker: {reason_code}")
    client.publish(TOPIC_WATER_STATE, "High" if sensor.is_active else "Normal", retain=True)

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect

def set_water(high: bool) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] Water level {'HIGH' if high else 'normal'}")
    mqtt_client.publish(TOPIC_WATER_STATE, "High" if high else "Normal", retain=True)
    if high:
        led.blink(on_time=FLICKER_S, off_time=FLICKER_S)
    else:
        led.off()

def main() -> None:
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"MQTT connection failed: {e}")

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
        mqtt_client.loop_stop()
        led.off()
        led.close()
        sensor.close()
