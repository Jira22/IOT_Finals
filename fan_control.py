#!/usr/bin/env python3
import glob
import os
import time
import paho.mqtt.client as mqtt
from gpiozero import OutputDevice

# ----------------------------- Settings ---------------------------------
FAN_PIN = 18                

FAN_ON_TEMP_C = 30.0        # defaults, HA sliders override them
FAN_OFF_TEMP_C = 28.0
MIN_GAP_C = 1.0             # on must stay this far above off, or the fan chatters
POLL_INTERVAL_S = 3
MANUAL_HOLD_S = 300         # a command from HA wins over the temperature for this long
RELAY_ACTIVE_HIGH = True   # S8050 transistor, not an active-low relay

# MQTT Configuration: the laptop's IP, set with MQTT_BROKER=<ip> when starting, default below
MQTT_BROKER = os.environ.get("MQTT_BROKER", "192.168.99.90")
MQTT_PORT = 1883
TOPIC_AVAIL = "homeassistant/switch/room_fan/availability"  # "offline" is sent by the broker if this script dies
TOPIC_TEMP_STATE = "homeassistant/sensor/temperature/state"
TOPIC_HUMIDITY_STATE = "homeassistant/sensor/humidity/state"
TOPIC_FAN_STATE = "homeassistant/switch/room_fan/state"
TOPIC_FAN_SET = "homeassistant/switch/room_fan/set"
TOPIC_LIMIT_SET = {"on": "homeassistant/number/fan_on_temp/set", "off": "homeassistant/number/fan_off_temp/set"}
TOPIC_LIMIT_STATE = {"on": "homeassistant/number/fan_on_temp/state", "off": "homeassistant/number/fan_off_temp/state"}

# --------------------------- Hardware setup ------------------------------
# DHT11 is read by the kernel driver: add 'dtoverlay=dht11,gpiopin=4' to /boot/firmware/config.txt
# (the Adafruit library fails on the Pi 5)
IIO_DIR = glob.glob('/sys/bus/iio/devices/iio:device*')[0]
fan = OutputDevice(FAN_PIN, active_high=RELAY_ACTIVE_HIGH, initial_value=False)

manual_hold_until = 0.0
limits = {"on": FAN_ON_TEMP_C, "off": FAN_OFF_TEMP_C}

# --------------------------- MQTT setup ----------------------------------
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT Broker: {reason_code}")
    client.publish(TOPIC_AVAIL, "online", retain=True)
    client.subscribe([(TOPIC_FAN_SET, 0)] + [(t, 0) for t in TOPIC_LIMIT_SET.values()])
    for key, topic in TOPIC_LIMIT_STATE.items():
        client.publish(topic, str(limits[key]), retain=True)
    # clear any stale retained state left by an earlier run
    client.publish(TOPIC_FAN_STATE, "ON" if fan.value else "OFF", retain=True)

def set_limit(key: str, raw: str) -> None:
    global manual_hold_until
    try:
        value = float(raw)
    except ValueError:
        return
    new = {**limits, key: value}
    if new["on"] - new["off"] >= MIN_GAP_C:
        limits.update(new)
        manual_hold_until = 0.0  # changing a threshold means "go back to auto"
        print(f"Fan limits: ON at >= {limits['on']} C, OFF at <= {limits['off']} C")
    else:
        print(f"Ignored {key} limit {value}: ON must be at least {MIN_GAP_C} C above OFF")
    # echo the accepted value, or the old one if it was rejected, so the HA slider snaps back
    mqtt_client.publish(TOPIC_LIMIT_STATE[key], str(limits[key]), retain=True)

def on_message(client, userdata, msg):
    global manual_hold_until
    for key, topic in TOPIC_LIMIT_SET.items():
        if msg.topic == topic:
            set_limit(key, msg.payload.decode())
            return
    payload = msg.payload.decode().upper()
    print(f"Received Fan command from HA: {payload}")

    if payload in ("ON", "OFF"):
        fan.on() if payload == "ON" else fan.off()
        manual_hold_until = time.time() + MANUAL_HOLD_S  # auto temperature control is paused meanwhile
        client.publish(TOPIC_FAN_STATE, payload, retain=True)

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.will_set(TOPIC_AVAIL, "offline", retain=True)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def read_dht(retries: int = 3):
    for _ in range(retries):
        try:
            with open(f"{IIO_DIR}/in_temp_input") as f:
                temp = int(f.read()) / 1000
            with open(f"{IIO_DIR}/in_humidityrelative_input") as f:
                humidity = int(f.read()) / 1000
            return temp, humidity
        except (OSError, ValueError):  # DHT11 reads fail now and then (EIO)
            time.sleep(2)
    return None, None

def on_fan_change(is_on: bool, temp: float) -> None:
    state = "ON" if is_on else "OFF"
    print(f"[{time.strftime('%H:%M:%S')}] Fan {state} (temp {temp:.1f} C)")
    mqtt_client.publish(TOPIC_FAN_STATE, state, retain=True)

def main() -> None:
    mqtt_client.connect_async(MQTT_BROKER, MQTT_PORT, 60)  # retries until the broker is up
    mqtt_client.loop_start()

    print(f"Fan Auto-ON at >= {limits['on']} C, OFF at <= {limits['off']} C")

    while True:
        temp, humidity = read_dht()

        if temp is None:
            print("Sensor read failed, keeping fan state unchanged")
        else:
            print(f"Temp: {temp:.1f} C  Humidity: {humidity:.0f}%  Fan: {'ON' if fan.value else 'OFF'}")
            
            # Send live stats data to Home Assistant dashboard
            mqtt_client.publish(TOPIC_TEMP_STATE, str(temp), retain=True)
            mqtt_client.publish(TOPIC_HUMIDITY_STATE, str(humidity), retain=True)

            if time.time() < manual_hold_until:
                print(f"  (manual hold, auto paused for {manual_hold_until - time.time():.0f} s more)")
            else:
                if temp >= limits["on"] and not fan.value:
                    fan.on()
                    on_fan_change(True, temp)
                elif temp <= limits["off"] and fan.value:
                    fan.off()
                    on_fan_change(False, temp)

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
        fan.off()
        fan.close()
