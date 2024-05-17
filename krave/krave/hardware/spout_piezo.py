import time
import numpy as np
import spidev
from scipy.signal import butter, lfilter, find_peaks
from krave import utils
import RPi.GPIO as GPIO
from sklearn.linear_model import LinearRegression

class SpoutPiezo:
    def __init__(self, mouse, hardware_config, spout_name):
        self.mouse = mouse
        self.hardware_config = hardware_config
        self.lick_pin = self.hardware_config['recording_spout'][spout_name][0]
        self.water_pin = self.hardware_config['recording_spout'][spout_name][1]
        self.test_opening_times = [0.01, 0.03, 0.05, 0.08, 0.1, 0.15]

        self.lick_status = 0
        self.lick_record = np.ones([3])
        self.duration = 0
        self.water_opened_time = None
        self.water_dispensing = False

        # Lick detection parameters
        self.sample_rate = 1000  # Replace with your desired sample rate
        self.filter_order = 2
        self.cutoff_freq = 20  # Replace with desired cutoff frequency
        self.threshold = 0.1  # Replace with desired threshold voltage
        self.min_lick_duration = 0.1  # Replace with desired minimum lick duration (in seconds)

        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.lick_pin, GPIO.IN)
        GPIO.setup(self.water_pin, GPIO.OUT)
        GPIO.output(self.water_pin, GPIO.LOW)

        self.spi = spidev.SpiDev()
        self.channel = 0
        self.spi.open(0, 0)  # Use SPI bus 0, device 0
        self.spi.max_speed_hz = 250000  # Set SPI clock speed to 500kHz

        # Initialize lick detection filter
        nyquist_freq = 0.5 * self.sample_rate
        normal_cutoff = self.cutoff_freq / nyquist_freq
        self.b, self.a = butter(self.filter_order, normal_cutoff, btype='high', analog=False)

    # def lick_status_check(self):
    #     """register change only when current status is different than all three
    #     previous status"""
    #     self.lick_record = np.roll(self.lick_record, 1)
    #     self.lick_record[0] = GPIO.input(self.lick_pin)
    #     change_bool = np.all(self.lick_record != self.lick_status)
    #     change = 0 if not change_bool else 1 if self.lick_status == 0 else -1
    #     self.lick_status += change
    #     return change

    # def lick_status_check(self):
    #     """Register change only when the current analog reading is different from the previous status"""
    #     analog_reading = self.read_analog_input(self.channel)
    #     lick_threshold = 0.5  # Adjust this threshold based on your specific setup
    #
    #     current_status = 1 if analog_reading > lick_threshold else 0
    #     change = current_status - self.lick_status
    #     self.lick_status = current_status
    #     return change

    def lick_status_check(self):
        """Detect lick events and print their timestamps"""
        voltage = self.read_analog_input(self.channel)
        if voltage > 0:
            print(f'current voltage: {voltage}')
        filtered_voltage = lfilter(self.b, self.a, [voltage])

        # Detect peaks above threshold
        peaks, _ = find_peaks(filtered_voltage, height=self.threshold)

        # Process detected peaks and find lick times
        for peak_idx in peaks:
            lick_time = peak_idx / self.sample_rate
            print(f"Lick detected at {lick_time} seconds")

    def read_analog_input(self, channel):
        adc = self.spi.xfer2([1, (8 + channel) << 4, 0])
        print("Raw ADC value:", adc)  # Print the raw ADC value
        data = ((adc[1] & 3) << 8) + adc[2]
        print("Calculated voltage:", data * 3.3 / 1023)  # Print the calculated voltage
        return data

    def water_on(self, open_time):
        """turn on water, return time turned on"""
        GPIO.output(self.water_pin, GPIO.HIGH)
        self.duration = open_time
        self.water_dispensing = True
        self.water_opened_time = time.time()

    def water_off(self):
        """turn off water, and return time turned off"""
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
