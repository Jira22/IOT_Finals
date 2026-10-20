#!/usr/bin/env python3
import time
import statistics
import threading
import paho.mqtt.client as mqtt
from gpiozero import DistanceSensor, PWMOutputDevice

# ----------------------------- Settings ---------------------------------
TRIG_PIN = 25
ECHO_PIN = 24
BUZZER_PIN = 22   # red alarm LED (was a buzzer)

MAX_DISTANCE_M = 2.0     
THRESHOLD_CM = 10.0      
CONFIRM_READINGS = 3     
SAMPLES_PER_READING = 5  
POLL_INTERVAL_S = 0.2    
CALIBRATION_TIME_S = 3   

TONE_READY_HZ = 2500
TONE_OPEN_HZ = 2000
TONE_CLOSE_HZ = 1500
TONE_ALARM_HZ = 3000

DOOR_OPEN_ALARM_S = 30   
ALARM_REPEAT_S = 2.0     
ALARM_BEEPS = 5          

# MQTT Configuration (CHANGE TO YOUR LAPTOP'S IP ADDRESS)
MQTT_BROKER = "192.168.99.90"
MQTT_PORT = 1883
TOPIC_DOOR_STATE = "homeassistant/binary_sensor/door/state"
TOPIC_BUZZER_STATE = "homeassistant/switch/buzzer/state"
TOPIC_BUZZER_SET = "homeassistant/switch/buzzer/set"

# --------------------------- Hardware setup ------------------------------
sensor = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN, max_distance=MAX_DISTANCE_M)
buzzer = PWMOutputDevice(BUZZER_PIN, frequency=TONE_OPEN_HZ, initial_value=0)

# Lock to avoid background thread beep collisions with main threat warnings
buzzer_lock = threading.Lock()

def beep(times: int = 1, on: float = 0.15, off: float = 0.1, freq: int = TONE_OPEN_HZ) -> None:
    with buzzer_lock:
        buzzer.frequency = freq
        for _ in range(times):
            buzzer.value = 1   # alarm is an LED now: full on, no tone
            time.sleep(on)
            buzzer.value = 0     
            time.sleep(off)

# --------------------------- MQTT setup ----------------------------------
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT Broker: {reason_code}")
    client.subscribe(TOPIC_BUZZER_SET)
    client.publish(TOPIC_BUZZER_STATE, "OFF", retain=True)

def on_message(client, userdata, msg):
    payload = msg.payload.decode().upper()
    print(f"Received Buzzer override command from HA: {payload}")
    
    if payload == "ON":
        client.publish(TOPIC_BUZZER_STATE, "ON", retain=True)
        # Use a non-blocking thread so beep loops don't lock your incoming message streams
        threading.Thread(target=trigger_remote_alarm).start()

def trigger_remote_alarm():
    beep(times=3, on=0.1, off=0.1, freq=TONE_ALARM_HZ)
    mqtt_client.publish(TOPIC_BUZZER_STATE, "OFF", retain=True)

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def read_distance_cm() -> float:
    samples = []
    for _ in range(SAMPLES_PER_READING):
        samples.append(sensor.distance * 100)  
        time.sleep(0.03)
    return statistics.median(samples)

def calibrate() -> float:
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
    mqtt_client.publish(TOPIC_DOOR_STATE, "ON", retain=True)
    beep(times=3, freq=TONE_OPEN_HZ)  

def on_door_close() -> None:
    print(f"[{time.strftime('%H:%M:%S')}] Door CLOSED")
    mqtt_client.publish(TOPIC_DOOR_STATE, "OFF", retain=True)
    beep(times=1, on=0.4, freq=TONE_CLOSE_HZ)  

def on_door_alarm(open_for_s: float) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] ALARM: door open for {open_for_s:.0f}s")

def main() -> None:
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"MQTT Connection failed: {e}")

    baseline = calibrate()
    door_open = False
    change_count = 0
    open_since = None        
    alarm_active = False     
    last_alarm_beep = 0.0

    # Ensure baseline state is synchronized to Home Assistant on startup
    mqtt_client.publish(TOPIC_DOOR_STATE, "OFF", retain=True)

    print(f"Alarm if the door stays open for {DOOR_OPEN_ALARM_S}s")
    beep(times=2, on=0.05, off=0.05, freq=TONE_READY_HZ)  

    while True:
        distance = read_distance_cm()
        deviates = abs(distance - baseline) > THRESHOLD_CM

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

        if door_open and open_since is not None:
            open_for = time.time() - open_since
            if open_for >= DOOR_OPEN_ALARM_S:
                if not alarm_active:
                    alarm_active = True
                    on_door_alarm(open_for)
                if time.time() - last_alarm_beep >= ALARM_REPEAT_S:
                    beep(times=ALARM_BEEPS, on=0.1, off=0.1, freq=TONE_ALARM_HZ)
                    last_alarm_beep = time.time()

        time.sleep(POLL_INTERVAL_S)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        mqtt_client.loop_stop()
        buzzer.off()
        sensor.close()
        buzzer.close()
