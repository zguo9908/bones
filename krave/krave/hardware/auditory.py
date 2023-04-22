from krave import utils
import board
import pulseio
import RPi.GPIO as GPIO
import time


class Auditory:

    def __init__(self, mouse, exp_config, audio_name, trial_type):
        self.mouse = mouse
        self.exp_config = exp_config
        self.trial_type = trial_type
        self.hardware_config_name = self.exp_config['hardware_setup']
        print(f'creating audio cue for trial type {trial_type}')
        self.hardware_config = utils.get_config('krave.hardware', 'hardware.json')[self.hardware_config_name]
        self.audio_pin = self.hardware_config['audio'][audio_name][0]
        # print(self.audio_pin)
        self.audio_f = self.exp_config['auditory_cue_frequency'][trial_type][0]
        self.cue_duration = self.exp_config['auditory_display_duration']
        self.buzz_on = False
        self.cue_displaying = False
        GPIO.setup(self.audio_pin, GPIO.OUT)
        self.cue_on_time = None
        self.buzzer = GPIO.PWM(self.audio_pin, int(self.audio_f))

    def cue_on(self):
        GPIO.output(self.audio_pin, GPIO.HIGH)
        self.buzzer.start(50)  # Set dutycycle
        self.buzz_on = True
        self.cue_on_time = time.time()
        # self.cue_displaying = True

    def set_frequency(self, trial_type):
        self.buzzer.ChangeFrequency(self.exp_config['auditory_cue_frequency'][trial_type][0])

    def cue_off(self):
        GPIO.output(self.audio_pin, GPIO.LOW)
        self.buzzer.stop()
        self.buzz_on = False

    def cue_cleanup(self):
        if self.cue_displaying and self.cue_on_time + self.cue_duration < time.time():
            self.cue_off()
            self.cue_displaying = False

    def shutdown(self):
        self.cue_off()
        GPIO.cleanup()
        return time.time()







#
# from pyaudio import PyAudio # sudo apt-get install python{,3}-pyaudio
#
# try:
#     from itertools import izip
# except ImportError: # Python 3
#     izip = zip
#     xrange = range



    # def sine_tone(frequency, duration, volume=1, sample_rate=22050):
    #     n_samples = int(sample_rate * duration)
    #     restframes = n_samples % sample_rate
    #
    #     p = PyAudio()
    #     stream = p.open(format=p.get_format_from_width(1),  # 8bit
    #                     channels=1,  # mono
    #                     rate=sample_rate,
    #                     output=True)
    #     s = lambda t: volume * math.sin(2 * math.pi * frequency * t / sample_rate)
    #     samples = (int(s(t) * 0x7f + 0x80) for t in xrange(n_samples))
    #     for buf in izip(*[samples] * sample_rate):  # write several samples at a time
    #         stream.write(bytes(bytearray(buf)))
    #
    #     # fill remainder of frameset with silence
    #     stream.write(b'\x80' * restframes)
    #
    #     stream.stop_stream()
    #     stream.close()
    #     p.terminate()