# testing the solenoid
# test deployment
import RPi.GPIO as GPIO
from time import sleep

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(23, GPIO.OUT)


while (True):
    GPIO.output(23,1)
    sleep(1)
    GPIO.output(23,0)
    sleep(1)

