#!/usr/bin/env python3
import glob
import time
import paho.mqtt.client as mqtt
from gpiozero import OutputDevice

# ----------------------------- Settings ---------------------------------
FAN_PIN = 18                

FAN_ON_TEMP_C = 30.0        
FAN_OFF_TEMP_C = 28.0       
POLL_INTERVAL_S = 3
MANUAL_HOLD_S = 300         # a command from HA wins over the temperature for this long
RELAY_ACTIVE_HIGH = True   # S8050 transistor, not an active-low relay

# MQTT Configuration (CHANGE TO YOUR LAPTOP'S IP ADDRESS)
MQTT_BROKER = "192.168.99.90"
MQTT_PORT = 1883
TOPIC_TEMP_STATE = "homeassistant/sensor/temperature/state"
TOPIC_HUMIDITY_STATE = "homeassistant/sensor/humidity/state"
TOPIC_FAN_STATE = "homeassistant/switch/room_fan/state"
TOPIC_FAN_SET = "homeassistant/switch/room_fan/set"

# --------------------------- Hardware setup ------------------------------
# DHT11 is read by the kernel driver: add 'dtoverlay=dht11,gpiopin=4' to /boot/firmware/config.txt
# (the Adafruit library fails on the Pi 5)
IIO_DIR = glob.glob('/sys/bus/iio/devices/iio:device*')[0]
fan = OutputDevice(FAN_PIN, active_high=RELAY_ACTIVE_HIGH, initial_value=False)

manual_hold_until = 0.0

# --------------------------- MQTT setup ----------------------------------
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT Broker: {reason_code}")
    client.subscribe(TOPIC_FAN_SET)
    # clear any stale retained state left by an earlier run
    client.publish(TOPIC_FAN_STATE, "ON" if fan.value else "OFF", retain=True)

def on_message(client, userdata, msg):
    global manual_hold_until
    payload = msg.payload.decode().upper()
    print(f"Received Fan command from HA: {payload}")

    if payload in ("ON", "OFF"):
        fan.on() if payload == "ON" else fan.off()
        manual_hold_until = time.time() + MANUAL_HOLD_S  # auto temperature control is paused meanwhile
        client.publish(TOPIC_FAN_STATE, payload, retain=True)

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
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
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"MQTT connection failed: {e}")

    print(f"Fan Auto-ON at >= {FAN_ON_TEMP_C} C, OFF at <= {FAN_OFF_TEMP_C} C")
    
    while True:
        temp, humidity = read_dht()

        if temp is None:
            print("Sensor read failed, keeping fan state unchanged")
        else:
            print(f"Temp: {temp:.1f} C  Humidity: {humidity:.0f}%  Fan: {'ON' if fan.value else 'OFF'}")
            
            # Send live stats data to Home Assistant dashboard
            mqtt_client.publish(TOPIC_TEMP_STATE, str(temp), retain=True)
            mqtt_client.publish(TOPIC_HUMIDITY_STATE, str(humidity), retain=True)

            if time.time() >= manual_hold_until:
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
        mqtt_client.loop_stop()
        fan.off()
        fan.close()
