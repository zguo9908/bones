import time
import numpy as np
import sys

sys.path.insert(0, '/home/pi/Adafruit_MCP3008')
from Adafruit_GPIO import Platform

from Adafruit_MCP3008 import MCP3008
from scipy.signal import butter, lfilter, find_peaks
import RPi.GPIO as GPIO
from enum import Enum, auto


class ThresholdMethod(Enum):
    """
    Enum to define different threshold detection methods
    """
    STATIC = auto()  # Use a fixed threshold
    DYNAMIC_STD = auto()  # Dynamic threshold based on standard deviation
    ADAPTIVE = auto()  # Adaptive threshold that evolves with the signal
    PEAK_DETECTION = auto()  # Uses scipy's find_peaks method


class SpoutPiezo:
    def __init__(self, mouse, hardware_config, spout_name,
                 threshold_method=ThresholdMethod.DYNAMIC_STD,
                 static_threshold=0.1,
                 dynamic_threshold_multiplier=2,
                 baseline_window_size=500):
        self.mouse = mouse
        self.hardware_config = hardware_config
        self.lick_pin = self.hardware_config['recording_spout'][spout_name][0]
        self.reward_pins = [hardware_config['recording_spout'][spout_name][1], hardware_config['spout_to_box']]

        # Thresholding parameters
        self.threshold_method = threshold_method
        self.static_threshold = static_threshold
        self.dynamic_threshold_multiplier = dynamic_threshold_multiplier
        self.baseline_window_size = baseline_window_size

        # Lick detection parameters
        self.sample_rate = 1000
        self.filter_order = 2
        self.cutoff_freq = 20
        self.min_lick_duration = 0.2
        self.analog = -1

        # State tracking
        self.lick_status = 0
        self.lick_record = np.ones([3])
        self.duration = 0
        self.water_opened_time = None
        self.water_dispensing = False

        self.lick_active = False
        self.lick_start_time = None
        self.lick_end_time = None

        # Baseline and tracking for adaptive methods
        self.baseline_buffer = []
        self.adaptive_threshold = None
        self.previous_samples = []

        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.lick_pin, GPIO.OUT)
        GPIO.output(self.lick_pin, GPIO.HIGH)
        for pin in self.reward_pins:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

        # Initialize SPI and MCP3008
        self.SPI_PORT = 0
        self.SPI_DEVICE = 0
        CLK = 11
        MISO = 9
        MOSI = 10
        CS = 13
        self.mcp = MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
        self.channel = 0

        # Initialize lick detection filter
        nyquist_freq = 0.5 * self.sample_rate
        normal_cutoff = self.cutoff_freq / nyquist_freq
        self.b, self.a = butter(self.filter_order, normal_cutoff, btype='high', analog=False)

        # Initialize baseline for adaptive methods
        self._initialize_baseline()

    def _initialize_baseline(self):
        """
        Initialize baseline buffer with initial readings
        """
        self.baseline_buffer = []
        for _ in range(self.baseline_window_size):
            initial_voltage = self.read_analog_input(self.channel)
            self.baseline_buffer.append(initial_voltage)

    def _calculate_dynamic_threshold(self):
        """
        Calculate dynamic threshold based on standard deviation
        """
        baseline_mean = np.mean(self.baseline_buffer)
        baseline_std = np.std(self.baseline_buffer)
        return baseline_mean + (self.dynamic_threshold_multiplier * baseline_std)

    def _calculate_adaptive_threshold(self, filtered_voltage):
        """
        Adaptive threshold that evolves with the signal
        Uses exponential moving average
        """
        alpha = 0.1  # Smoothing factor

        if self.adaptive_threshold is None:
            self.adaptive_threshold = filtered_voltage

        # Update adaptive threshold
        self.adaptive_threshold = (alpha * filtered_voltage) + ((1 - alpha) * self.adaptive_threshold)

        return self.adaptive_threshold * 1.5  # Add some sensitivity

    def _update_baseline_buffer(self, new_value):
        """
        Update the baseline buffer, maintaining a fixed window size
        """
        if len(self.baseline_buffer) >= self.baseline_window_size:
            self.baseline_buffer.pop(0)
        self.baseline_buffer.append(new_value)

    def _detect_peaks(self, filtered_voltage):
        """
        Use scipy's find_peaks for more advanced peak detection
        """
        self.previous_samples.append(filtered_voltage)

        # Keep only last 100 samples to prevent memory growth
        if len(self.previous_samples) > 100:
            self.previous_samples.pop(0)

        # Only check for peaks if we have enough samples
        if len(self.previous_samples) > 10:
            peaks, _ = find_peaks(self.previous_samples, height=np.mean(self.previous_samples))
            return len(peaks) > 0

        return False

    def lick_status_check(self):
        """
        Detect lick events using selected thresholding method
        """
        # Read and filter voltage
        voltage = self.read_analog_input(self.channel)
        filtered_voltage = lfilter(self.b, self.a, [voltage])[0]
        current_time = time.time()
        self.analog = filtered_voltage

        # Determine threshold based on selected method
        lick_detected = False
        if self.threshold_method == ThresholdMethod.STATIC:
            lick_detected = filtered_voltage > self.static_threshold

        elif self.threshold_method == ThresholdMethod.DYNAMIC_STD:
            dynamic_threshold = self._calculate_dynamic_threshold()
            lick_detected = filtered_voltage > dynamic_threshold
            # Optionally print debug info
            # print(f"Dynamic Threshold: {dynamic_threshold:.3f}, Filtered Voltage: {filtered_voltage:.3f}")

        elif self.threshold_method == ThresholdMethod.ADAPTIVE:
            adaptive_threshold = self._calculate_adaptive_threshold(filtered_voltage)
            lick_detected = filtered_voltage > adaptive_threshold

        elif self.threshold_method == ThresholdMethod.PEAK_DETECTION:
            lick_detected = self._detect_peaks(filtered_voltage)

        # Lick detection logic
        if lick_detected:
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

        # Update baseline for methods that require it
        if self.threshold_method in [ThresholdMethod.DYNAMIC_STD]:
            self._update_baseline_buffer(voltage)

        return 0  # No lick detected

    # Remaining methods (water_on, water_off, give_reward, etc.) remain the same as in previous implementation
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

# import time
# import numpy as np
# import sys
# sys.path.insert(0, '/home/pi/Adafruit_MCP3008')
# from Adafruit_GPIO import Platform
#
# from Adafruit_MCP3008 import MCP3008
# # import Adafruit_GPIO as GPIO
# from scipy.signal import butter, lfilter, find_peaks
# import RPi.GPIO as GPIO
#
# class SpoutPiezo:
#     def __init__(self, mouse, hardware_config, spout_name):
#         self.mouse = mouse
#         self.hardware_config = hardware_config
#         self.lick_pin = self.hardware_config['recording_spout'][spout_name][0]
#         self.reward_pins = [hardware_config['recording_spout'][spout_name][1], hardware_config['spout_to_box']]
#         print(self.reward_pins)
#         self.test_opening_times = [0.01, 0.03, 0.05, 0.08, 0.1, 0.15]
#
#         self.lick_status = 0
#         self.lick_record = np.ones([3])
#         self.duration = 0
#         self.water_opened_time = None
#         self.water_dispensing = False
#
#         self.lick_active = False
#         self.lick_start_time = None
#         self.lick_end_time = None
#
#         # Lick detection parameters
#         self.sample_rate = 1000  # Replace with your desired sample rate
#         self.filter_order = 2
#         self.cutoff_freq = 20  # Replace with desired cutoff frequency
#         self.threshold = 0.1 # Replace with desired threshold voltage
#         self.min_lick_duration = 0.3  # Replace with desired minimum lick duration (in seconds)
#         self.analog = -1
#
#         # Set up GPIO
#         GPIO.setmode(GPIO.BCM)
#         GPIO.setup(self.lick_pin, GPIO.OUT)
#         GPIO.output(self.lick_pin, GPIO.HIGH)
#         for pin in self.reward_pins:  # GPIO.setup requires individual pins
#             GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
#
#
#         # Initialize SPI and MCP3008
#         self.SPI_PORT = 0
#         self.SPI_DEVICE = 0
#         CLK = 11
#         MISO = 9
#         MOSI = 10
#         CS = 13
#         # gpio = Platform.RPiGPIO()  # Explicitly specify platform
#         self.mcp = MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
#
#         # gpio = GPIO.RPiGPIOAdapter()
#         # self.mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI, gpio=gpio)
#         self.channel = 0
#
#         # Initialize lick detection filter
#         nyquist_freq = 0.5 * self.sample_rate
#         normal_cutoff = self.cutoff_freq / nyquist_freq
#         self.b, self.a = butter(self.filter_order, normal_cutoff, btype='high', analog=False)
#         # New attributes for dynamic threshold detection
#         self.baseline_window_size = 500  # Number of samples to use for baseline calculation
#         self.baseline_buffer = []
#         self.dynamic_threshold_multiplier = 3.0  # Number of standard deviations above mean to use as threshold
#
#         # Initialize baseline calculation
#         for _ in range(self.baseline_window_size):
#             initial_voltage = self.read_analog_input(self.channel)
#             self.baseline_buffer.append(initial_voltage)
#
#     def lick_status_check(self):
#         """Detect lick events and print their timestamps"""
#         voltage = self.read_analog_input(self.channel)
#         filtered_voltage = lfilter(self.b, self.a, [voltage])
#         print(filtered_voltage)
#         current_time = time.time()
#         self.analog = filtered_voltage
#         if filtered_voltage > self.threshold:
#             if not self.lick_active:
#                 self.lick_active = True
#                 self.lick_start_time = current_time
#                 print(f"Lick bout started at {self.lick_start_time:.3f} seconds")
#                 return 1
#         else:
#             if self.lick_active:
#                 if current_time - self.lick_start_time >= self.min_lick_duration:
#                     self.lick_active = False
#                     self.lick_end_time = current_time
#                     print(f"Lick bout ended at {self.lick_end_time:.3f} seconds")
#                     bout_duration = self.lick_end_time - self.lick_start_time
#                     print(f"Lick bout duration: {bout_duration:.3f} seconds")
#                     self.lick_start_time = None
#                     self.lick_end_time = None
#                     return -1
#
#     def read_analog_input(self, channel):
#         value = self.mcp.read_adc(channel)
#         voltage = value / 1023.0 * 3.3  # Convert value to voltage (assuming 3.3V reference)
#         if voltage > 5:
#             print(f"Channel {channel} value: {value}, voltage: {voltage:.2f}V")
#         return voltage
#
#     def water_on(self, open_time):
#         """turn on water, return time turned on"""
#         for pin in self.reward_pins:
#             GPIO.output(pin, GPIO.HIGH)
#         self.duration = open_time
#         self.water_dispensing = True
#         self.water_opened_time = time.time()
#         print(f'water delivered at {self.water_opened_time}')
#
#     def water_off(self):
#         """turn off water, and return time turned off"""
#         for pin in self.reward_pins:
#             GPIO.output(pin, GPIO.LOW)
#         self.water_dispensing = False
#
#     def give_reward(self, reward_duration):
#         self.water_on(reward_duration)
#         time.sleep(reward_duration)
#         self.water_off()
#
#     def water_cleanup(self):
#         if self.water_dispensing and self.water_opened_time + self.duration < time.time():
#             duration = time.time() - self.water_opened_time
#             self.water_off()
#             return duration
#
#     def shutdown(self):
#         self.water_off()
#         GPIO.cleanup()
#         print("GPIO cleaned up")
#         return time.time()