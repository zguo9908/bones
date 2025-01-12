import time

from krave import utils
import RPi.GPIO as GPIO
import numpy as np
# import sklearn


class Spout:
    def __init__(self, mouse, hardware_config, spout_name):
        self.mouse = mouse

        self.hardware_config = hardware_config
        self.lick_pin = self.hardware_config['spouts'][spout_name][0]
        self.reward_pins = [hardware_config['spouts'][spout_name][1], hardware_config['spout_to_box']]
        print(self.reward_pins)
        # print(self.lick_pin)
        # print(self.water_pin)
        self.test_opening_times = [0.01, 0.03, 0.05, 0.08, 0.1, 0.15]

        self.lick_status = 0
        self.lick_record = np.ones([3])
        self.duration = 0
        self.water_opened_time = None
        self.water_dispensing = False

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.lick_pin, GPIO.IN)
        # GPIO.setup(self.water_pin, GPIO.OUT)
        GPIO.setup(self.reward_pins, GPIO.OUT, initial=GPIO.LOW)

    def lick_status_check(self):
        """register change only when current status is different than all three
        previous status"""
        self.lick_record = np.roll(self.lick_record, 1)
        self.lick_record[0] = GPIO.input(self.lick_pin)
        # print(self.lick_record[0])
        change_bool = np.all(self.lick_record != self.lick_status)
        change = 0 if not change_bool else 1 if self.lick_status == 0 else -1
        self.lick_status += change
        return change

    def water_on(self, open_time):
        """turn on water, return time turned on"""
        for pin in self.reward_pins:
            GPIO.output(pin, GPIO.HIGH)
        self.duration = open_time
        self.water_dispensing = True
        self.water_opened_time = time.time()

    def water_off(self):
        """turn off water, and return time turned off"""
        for pin in self.reward_pins:
            GPIO.output(pin, GPIO.LOW)
        self.water_dispensing = False

    def give_reward(self, reward_duration):
        self.water_on(reward_duration)
        time.sleep(reward_duration)
        self.water_off()

    def water_cleanup(self):
        if self.water_dispensing and self.water_opened_time + self.duration < time.time():
            duration = time.time() - self.water_opened_time
            self.water_off()
            return duration

    def shutdown(self):
        self.water_off()
        GPIO.cleanup()
        print("GPIO cleaned up")
        return time.time()

    def calibrate(self):
        iteration = 100
        for t in self.water_opened_time:
             print(f'water opening for {self.water_opened_time[t]} s')
             for _ in range(iteration):
                    self.water_on()
                    time.sleep(t)
                    self.water_off()
                    time.sleep(0.2)
             input("Press Enter to continue...")

