#!/usr/bin/env python3
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

# MQTT Configuration (CHANGE TO YOUR LAPTOP'S IP ADDRESS)
MQTT_BROKER = "192.168.99.90" 
MQTT_PORT = 1883
TOPIC_LIGHT_STATE = "homeassistant/light/room_light/state"
TOPIC_LIGHT_SET = "homeassistant/light/room_light/set"
TOPIC_MOTION_STATE = "homeassistant/binary_sensor/motion/state"

# --------------------------- Hardware setup ------------------------------
pir = MotionSensor(PIR_PIN)
light = OutputDevice(LIGHT_PIN, active_high=RELAY_ACTIVE_HIGH, initial_value=False)

# Global tracker to remember if the light was overridden by Home Assistant
manual_override_time = 0.0

# --------------------------- MQTT setup ----------------------------------
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT Broker: {reason_code}")
    client.subscribe(TOPIC_LIGHT_SET)
    client.publish(TOPIC_LIGHT_STATE, "ON" if light.value else "OFF", retain=True)

def on_message(client, userdata, msg):
    global manual_override_time
    payload = msg.payload.decode().upper()
    print(f"Received command from HA: {payload}")
    
    if payload == "ON":
        if not light.value:
            light.on()
            client.publish(TOPIC_LIGHT_STATE, "ON", retain=True)
        manual_override_time = time.time()  # Keep it on like motion was detected
    elif payload == "OFF":
        if light.value:
            light.off()
            client.publish(TOPIC_LIGHT_STATE, "OFF", retain=True)

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def on_light_change(is_on: bool) -> None:
    state = "ON" if is_on else "OFF"
    print(f"[{time.strftime('%H:%M:%S')}] Light {state}")
    mqtt_client.publish(TOPIC_LIGHT_STATE, state, retain=True)

def main() -> None:
    global manual_override_time
    
    # Start MQTT background thread
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}. Running offline...")

    print(f"Warming up PIR sensor for {PIR_WARMUP_S}s (stay still)...")
    time.sleep(PIR_WARMUP_S)
    print("Ready. (Ctrl+C to stop)")

    last_motion = 0.0
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
            if light.value:
                last_motion = time.time()  

        # Check if it should turn off (either due to no motion, or manual HA override expiring)
        elif light.value:
            effective_last_interaction = max(last_motion, manual_override_time)
            if (time.time() - effective_last_interaction) >= LIGHT_TIMEOUT_S:
                light.off()
                on_light_change(False)

        time.sleep(POLL_INTERVAL_S)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        mqtt_client.loop_stop()
        light.off()
        light.close()
        pir.close()
