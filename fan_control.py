#!/usr/bin/env python3
import time
import board
import adafruit_dht
import paho.mqtt.client as mqtt
from gpiozero import OutputDevice

# ----------------------------- Settings ---------------------------------
DHT_PIN = board.D4          
FAN_PIN = 17                

FAN_ON_TEMP_C = 30.0        
FAN_OFF_TEMP_C = 28.0       
POLL_INTERVAL_S = 3         
RELAY_ACTIVE_HIGH = False

# MQTT Configuration (CHANGE TO YOUR LAPTOP'S IP ADDRESS)
MQTT_BROKER = "192.168.99.90"
MQTT_PORT = 1883
TOPIC_TEMP_STATE = "homeassistant/sensor/temperature/state"
TOPIC_FAN_STATE = "homeassistant/switch/room_fan/state"
TOPIC_FAN_SET = "homeassistant/switch/room_fan/set"

# --------------------------- Hardware setup ------------------------------
dht = adafruit_dht.DHT11(DHT_PIN)
fan = OutputDevice(FAN_PIN, active_high=RELAY_ACTIVE_HIGH, initial_value=False)

# Global manual control flag
manual_override = False

# --------------------------- MQTT setup ----------------------------------
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with code {rc}")
    client.subscribe(TOPIC_FAN_SET)

def on_message(client, userdata, msg):
    global manual_override
    payload = msg.payload.decode().upper()
    print(f"Received Fan command from HA: {payload}")
    
    if payload == "ON":
        manual_override = True
        if not fan.value:
            fan.on()
            client.publish(TOPIC_FAN_STATE, "ON", retain=True)
    elif payload == "OFF":
        manual_override = False
        if fan.value:
            fan.off()
            client.publish(TOPIC_FAN_STATE, "OFF", retain=True)

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def read_dht(retries: int = 3):
    for _ in range(retries):
        try:
            return dht.temperature, dht.humidity
        except (RuntimeError, OverflowError, ValueError):
            time.sleep(2)  
    return None, None

def on_fan_change(is_on: bool, temp: float) -> None:
    state = "ON" if is_on else "OFF"
    print(f"[{time.strftime('%H:%M:%S')}] Fan {state} (temp {temp:.1f} C)")
    mqtt_client.publish(TOPIC_FAN_STATE, state, retain=True)

def main() -> None:
    global manual_override
    
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
            print(f"Temp: {temp:.1f} C  Humidity: {humidity}%  Fan: {'ON' if fan.value else 'OFF'}")
            
            # Send live stats data to Home Assistant dashboard
            mqtt_client.publish(TOPIC_TEMP_STATE, str(temp), retain=True)

            # Auto control loop ONLY executes if Home Assistant hasn't issued a manual override override command
            if not manual_override:
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
        dht.exit()
