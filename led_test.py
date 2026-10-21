from time import sleep
from gpiozero import LED

LEDS = {"room light": LED(23), "water level": LED(26)}

for name, led in LEDS.items():
    print(f"{name}: blinking 3x")
    for _ in range(3):
        led.on()
        sleep(0.5)
        led.off()
        sleep(0.5)

print("both on for 2 s")
for led in LEDS.values():
    led.on()
sleep(2)

for led in LEDS.values():
    led.close()
print("done")
