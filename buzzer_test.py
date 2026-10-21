from time import sleep
from gpiozero import PWMOutputDevice

BUZZER_PIN = 22   # S8050 base via 1k; passive buzzer needs a tone, not steady power

buzzer = PWMOutputDevice(BUZZER_PIN, initial_value=0)

for hz in (500, 1000, 2000, 3000):
    print(f"{hz} Hz")
    buzzer.frequency = hz
    buzzer.value = 0.5
    sleep(1)
    buzzer.value = 0
    sleep(0.5)

buzzer.close()
print("done")
