#!/usr/bin/env python3
import os
import time
import paho.mqtt.client as mqtt
from gpiozero import MotionSensor, OutputDevice

# ----------------------------- Settings ---------------------------------
PIR_PIN = 17
LIGHT_PIN = 23

LIGHT_TIMEOUT_S = 10      
POLL_INTERVAL_S = 0.5
PIR_WARMUP_S = 10
RELAY_ACTIVE_HIGH = True   # LED driven directly

# MQTT Configuration: the laptop's IP, set with MQTT_BROKER=<ip> when starting, default below
MQTT_BROKER = os.environ.get("MQTT_BROKER", "192.168.99.90")
MQTT_PORT = 1883
TOPIC_AVAIL = "homeassistant/light/room_light/availability"  # "offline" is sent by the broker if this script dies
TOPIC_LIGHT_STATE = "homeassistant/light/room_light/state"
TOPIC_LIGHT_SET = "homeassistant/light/room_light/set"
TOPIC_MOTION_STATE = "homeassistant/binary_sensor/motion/state"

# --------------------------- Hardware setup ------------------------------
pir = MotionSensor(PIR_PIN)
light = OutputDevice(LIGHT_PIN, active_high=RELAY_ACTIVE_HIGH, initial_value=False)

last_motion = 0.0  # also set by an HA "ON", so the normal timeout then turns the light off

# --------------------------- MQTT setup ----------------------------------
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT Broker: {reason_code}")
    client.publish(TOPIC_AVAIL, "online", retain=True)
    client.subscribe(TOPIC_LIGHT_SET)
    client.publish(TOPIC_LIGHT_STATE, "ON" if light.value else "OFF", retain=True)

def on_message(client, userdata, msg):
    global last_motion
    payload = msg.payload.decode().upper()
    print(f"Received command from HA: {payload}")

    if payload in ("ON", "OFF"):
        light.on() if payload == "ON" else light.off()
        last_motion = time.time()
        client.publish(TOPIC_LIGHT_STATE, payload, retain=True)

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.will_set(TOPIC_AVAIL, "offline", retain=True)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def on_light_change(is_on: bool) -> None:
    state = "ON" if is_on else "OFF"
    print(f"[{time.strftime('%H:%M:%S')}] Light {state}")
    mqtt_client.publish(TOPIC_LIGHT_STATE, state, retain=True)

def main() -> None:
    # Start MQTT background thread
    mqtt_client.connect_async(MQTT_BROKER, MQTT_PORT, 60)  # retries until the broker is up
    mqtt_client.loop_start()

    print(f"Warming up PIR sensor for {PIR_WARMUP_S}s (stay still)...")
    time.sleep(PIR_WARMUP_S)
    print("Ready. (Ctrl+C to stop)")

    global last_motion
    last_reported_motion = False

    while True:
        motion = pir.motion_detected

        # Send motion events to Home Assistant dashboard instantly
        if motion != last_reported_motion:
            mqtt_client.publish(TOPIC_MOTION_STATE, "ON" if motion else "OFF", retain=True)
            last_reported_motion = motion

        if motion:
            if not light.value:
                light.on()
                on_light_change(True)
            last_motion = time.time()
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
        try:
            mqtt_client.publish(TOPIC_AVAIL, "offline", retain=True).wait_for_publish(2)
        except Exception:
            pass  # broker unreachable, nobody to tell
        mqtt_client.loop_stop()
        light.off()
        light.close()
        pir.close()
