import time
from krave import utils
import RPi.GPIO as GPIO
import numpy as np
from sklearn.linear_model import LinearRegression


class Spout_IR:
    def __init__(self, mouse, exp_config, spout_name):
        self.mouse = mouse
        self.exp_config = exp_config
        self.hardware_config_name = self.exp_config['hardware_setup']
        self.hardware_config = utils.get_config('krave.hardware', 'hardware.json')[self.hardware_config_name]

        self.ir_lick_pin = self.hardware_config['ir_spout'][spout_name][0]
        self.water_pin = self.hardware_config['ir_spout'][spout_name][1]
        print(self.ir_lick_pin)
        # print(self.water_pin)

        self.lick_status = 0
        self.lick_record = np.ones([3])
        self.duration = 0
        self.water_opened_time = None
        self.water_dispensing = False

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.ir_lick_pin, GPIO.IN)
        GPIO.setup(self.water_pin, GPIO.OUT)
        GPIO.output(self.water_pin, GPIO.LOW)

    def lick_status_check(self):
        print(f'current lick input {GPIO.input(self.ir_lick_pin)}')
        change = GPIO.input(self.ir_lick_pin) - self.lick_status
        self.lick_status += change
        print(f'current lick status {self.lick_status}')
        if change == 1:
            self.lick_start_time = time.time()
        elif change == -1:
            print(f'lick time: {time.time() - self.lick_start_time:.3f}')
        return change

    def water_on(self, open_time):
        """turn on water, return time turned on"""
        GPIO.output(self.water_pin, GPIO.HIGH)
        self.duration = open_time
        self.water_dispensing = True
        self.water_opened_time = time.time()

    def water_off(self):
        """turn off water, and return time turned off"""
        # print(self.water_pin)
        # GPIO.setmode(GPIO.BCM)
        # GPIO.setup(self.water_pin, GPIO.OUT)
        GPIO.output(self.water_pin, GPIO.LOW)
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

    def calibrate_old(self):
        self.total_open_times = []
        self.water_weights = []
        try:
            print('calibrating port')
            repeats = 1  # repeating the same weight
            iteration = 100  # number of times opened of solenoid
            for t in self.calibration_times:
                for r in range(repeats):
                    total_open_time = 0
                    for _ in range(iteration):
                        self.water_on(t)
                        time.sleep(t)
                        total_open_time += t
                        self.water_off()
                        time.sleep(0.2)
                    self.total_open_times.append(total_open_time)
                    water_weight = input(f'open time {t} iter {r} water weight: ')
                    self.water_weights.append(float(water_weight))
                    input("Press Enter to continue...")
        finally:
            self.shutdown()
            print(f'total open times {self.total_open_times}')
            print(f'water weights {self.water_weights}')

            self.total_open_times = np.asarray(self.total_open_times).reshape(-1, 1)
            self.water_weights = np.asarray(self.water_weights)
            model = LinearRegression(fit_intercept=False).fit(self.total_open_times, self.water_weights)
            self.slope = model.coef_[0]
            print('slope: ', self.slope)
            print('REMEMBER TO ENTER TO SPOUT INITIATION!!!')

    def calculate_duration(self, reward_size_ul):
        weight_g = reward_size_ul * 0.001
        duration = weight_g / self.slope
        print('sol_open_time: ', duration)
        return duration
