import time
import numpy as np
import sys
sys.path.insert(0, '/home/pi/Adafruit_MCP3008')
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
from scipy.signal import butter, lfilter, find_peaks
from krave import utils
import RPi.GPIO as GPIO
from sklearn.linear_model import LinearRegression

class SpoutPiezo:
    def __init__(self, mouse, hardware_config, spout_name):
        self.mouse = mouse
        self.hardware_config = hardware_config
        self.lick_pin = self.hardware_config['recording_spout'][spout_name][0]
        self.reward_pins = [hardware_config['recording_spout'][spout_name][1], hardware_config['spout_to_box']]
        print(self.reward_pins)
        self.test_opening_times = [0.01, 0.03, 0.05, 0.08, 0.1, 0.15]

        self.lick_status = 0
        self.lick_record = np.ones([3])
        self.duration = 0
        self.water_opened_time = None
        self.water_dispensing = False

        self.lick_active = False
        self.lick_start_time = None
        self.lick_end_time = None

        # Lick detection parameters
        self.sample_rate = 1000  # Replace with your desired sample rate
        self.filter_order = 2
        self.cutoff_freq = 20  # Replace with desired cutoff frequency
        self.threshold = 0.013 # Replace with desired threshold voltage
        self.min_lick_duration = 0.3  # Replace with desired minimum lick duration (in seconds)
        self.analog = -1

        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.lick_pin, GPIO.OUT)
        GPIO.output(self.lick_pin, GPIO.HIGH)
        GPIO.setup(self.reward_pins, GPIO.OUT, initial=GPIO.LOW)


        # Initialize SPI and MCP3008
        self.SPI_PORT = 0
        self.SPI_DEVICE = 0
        CLK = 11
        MISO = 9
        MOSI = 10
        CS = 13
        self.mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

        self.channel = 0

        # Initialize lick detection filter
        nyquist_freq = 0.5 * self.sample_rate
        normal_cutoff = self.cutoff_freq / nyquist_freq
        self.b, self.a = butter(self.filter_order, normal_cutoff, btype='high', analog=False)

    def lick_status_check(self):
        """Detect lick events and print their timestamps"""
        voltage = self.read_analog_input(self.channel)
        filtered_voltage = lfilter(self.b, self.a, [voltage])
       # print(filtered_voltage)
        current_time = time.time()
        self.analog = filtered_voltage
        if filtered_voltage > self.threshold:
            if not self.lick_active:
                self.lick_active = True
                self.lick_start_time = current_time
                print(f"Lick bout started at {self.lick_start_time:.3f} seconds")
                return 1
        else:
            if self.lick_active:
                if current_time - self.lick_start_time >= self.min_lick_duration:
                    self.lick_active = False
                    self.lick_end_time = current_time
                    print(f"Lick bout ended at {self.lick_end_time:.3f} seconds")
                    bout_duration = self.lick_end_time - self.lick_start_time
                    print(f"Lick bout duration: {bout_duration:.3f} seconds")
                    self.lick_start_time = None
                    self.lick_end_time = None
                    return -1

    def read_analog_input(self, channel):
        value = self.mcp.read_adc(channel)
        voltage = value / 1023.0 * 3.3  # Convert value to voltage (assuming 3.3V reference)
        if voltage > 5:
            print(f"Channel {channel} value: {value}, voltage: {voltage:.2f}V")
        return voltage

    def water_on(self, open_time):
        """turn on water, return time turned on"""
        for pin in self.reward_pins:
            GPIO.output(pin, GPIO.HIGH)
        self.duration = open_time
        self.water_dispensing = True
        self.water_opened_time = time.time()
        print(f'water delivered at {self.water_opened_time}')

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