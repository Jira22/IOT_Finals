import warnings
from time import sleep
from gpiozero import DistanceSensor

warnings.simplefilter("ignore")  # hide the PWMSoftwareFallback / NoEcho spam, we print our own

sensor = DistanceSensor(echo=24, trigger=25, max_distance=2)

print("Ctrl+C to stop")
try:
    while True:
        cm = sensor.distance * 100
        # distance saturates at max_distance when no echo comes back
        print("no echo" if cm >= 199 else f"{cm:.1f} cm")
        sleep(0.3)
except KeyboardInterrupt:
    sensor.close()
