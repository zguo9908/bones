from krave import utils

import RPi.GPIO as GPIO
import time


class LED:

    def __init__(self, mouse, exp_config):
        self.mouse = mouse
        self.exp_config = exp_config
        self.hardware_config_name = self.exp_config['hardware_setup']
        self.hardware_config = utils.get_config('krave.hardware', 'hardware.json')[self.hardware_config_name]
        self.blue_pin = self.hardware_config['led']['blue'][0]
        self.green_pin = self.hardware_config['led']['green'][0]
        self.current_led = None
        self.last_led = None

        self.color = None
        self.cue_displaying = False
        GPIO.setup(self.blue_pin, GPIO.OUT)
        GPIO.setup(self.green_pin, GPIO.OUT)

        self.cue_on_time = None

    def cue_on(self):
        GPIO.output(self.current_led, GPIO.HIGH)
        GPIO.output(self.last_led,GPIO.LOW)
        print(f"light color is {self.color}")
        self.cue_displaying = True
        self.cue_on_time = time.time()
        # self.cue_displaying = True

    def set_color(self, trial_type):
        self.color = self.exp_config['led_cue'][trial_type][0]
        if self.color == 'blue':
            self.current_led = self.blue_pin
            self.last_led = self.green_pin
        elif self.color == 'green':
            self.current_led = self.green_pin
            self.last_led = self.blue_pin

    def cue_off(self):
        GPIO.output(self.current_led, GPIO.LOW)
        self.cue_displaying = False

    def cue_cleanup(self):
        if self.cue_displaying and self.cue_on_time + self.cue_duration < time.time():
            self.cue_off()
            self.cue_displaying = False

    def shutdown(self):
        self.cue_off()
        GPIO.cleanup()
        return time.time()


