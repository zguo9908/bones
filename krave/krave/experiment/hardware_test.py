import socket
import time

from krave import utils
# from krave.hardware.auditory import Auditory
from krave.hardware.auditory import Auditory
from krave.hardware.basler_camera import CameraBasler
from krave.hardware.spout_piezo import SpoutPiezo

hostname = socket.gethostname()
# Check if the hostname contains "ziyipi1" or "ziyipi3"
if "ziyipi1" in hostname:
    # Code for Raspberry Pi with hostname "ziyipi1"
    print("Running on ziyipi1")
    hostname = "ziyipi1"
    from krave.hardware.pi_camera import CameraPi
elif "ziyipi3" in hostname:
    # Code for Raspberry Pi with hostname "ziyipi3"
    print("Running on ziyipi3")
    hostname = "ziyipi3"
    from krave.hardware.libcamera import CameraViewer
elif "ziyipi5" in hostname:
    # Code for Raspberry Pi with hostname "ziyipi3"
    print("Running on ziyipi5")
    hostname = "ziyipi5"
    from krave.hardware.pi_camera import CameraPi
else:
    # Code for other Raspberry Pis or devices
    print("Running on an unknown device")


from krave.hardware.led import LED
from krave.hardware.spout import Spout
from krave.hardware.spout_ir import Spout_IR
from krave.output.data_writer import DataWriter
import numpy as np
import numpy.core.multiarray
import RPi.GPIO as GPIO
import pygame


def reward_function(t):
    return .1


class PiTest:
    def __init__(self,  mouse, exp_name,):
        # self.canvas = canvas
        self.mouse = mouse
        self.exp_name = exp_name
        self.exp_config = self.get_config()
        self.hardware_name = self.exp_config['hardware_setup']
        self.hardware_config = utils.get_config('krave.hardware', 'hardware.json')[self.hardware_name]

        self.cue_duration = self.exp_config["auditory_display_duration"]

        self.spout1 = Spout(self.mouse, self.hardware_config, spout_name="1")
        self.spout2 = Spout(self.mouse, self.hardware_config, spout_name="2")
        # self.ir_spout = Spout_IR(self.mouse, self.hardware_config, spout_name="1")

        # self.LED = LED(self.mouse, self.exp_config)
        self.auditory1 = Auditory(self.mouse, self.exp_config, self.hardware_config, audio_name = "1",trial_type='s')
        self.auditory2 = Auditory(self.mouse, self.exp_config, self.hardware_config, audio_name = "2",trial_type='l')
        self.data_writer = DataWriter(self.mouse, self.exp_name, "test", "test",self.exp_config, False)

        if hostname == "ziyipi3":
            self.camera = CameraViewer('test_video.h264')
        elif hostname == "ziyipi1":
            self.camera = CameraPi('test_video.h264')
        elif hostname == "ziyipi5":
            self.camera = CameraPi('test_video.h264')
            self.trigger = CameraBasler(self.hardware_config, self.data_writer)
            self.recording_spout = SpoutPiezo(self.mouse, self.hardware_config, spout_name="1")

        self.running = False
        self.testing_auditory = None
        self.start_time = time.time()
        self.status = 'nan,nan,nan,nan,nan,'


    def get_config(self):
        """Get experiment config from json"""
        return utils.get_config('krave.experiment', f'config/{self.exp_name}.json')

    def test_pi_camera_preview(self):
        self.camera.on(record_video=True)
        time.sleep(20)
        self.camera.shutdown()
        # self.end()

    def test_lick(self, spout):
        if spout == 1:
            testing_spout = self.spout1
        elif spout == 2:
            testing_spout = self.spout2
        else:
            print("no more than 2 spouts assembled")
        print(testing_spout.lick_pin)
        print(testing_spout.water_pin)

        try:
            time_limit = 60
            start = time.time()
            lick_counter = 0
            while start + time_limit > time.time():
                lick_change = testing_spout.lick_status_check()
                if lick_change == 1:
                    print(f"start lick {lick_counter}")
                    lick_counter += 1
                elif lick_change == -1:
                    print(f"end lick {lick_counter} at {time.time()}")
        finally:
            testing_spout.shutdown()

    def test_lick_recording(self):
        print(f'lick pin is {self.recording_spout.lick_pin}')
        print(f'water pin is {self.recording_spout.water_pin}')

        try:
            time_limit = 60
            start = time.time()
            lick_counter = 0
            while start + time_limit > time.time():
                lick_change = self.recording_spout.lick_status_check()
                if lick_change == 1:
                    print(f"start lick {lick_counter} at {time.time()}")
                    lick_counter += 1
                elif lick_change == -1:
                    print(f"end lick {lick_counter} at {time.time()}")
        finally:
            self.recording_spout.shutdown()

    def test_two_lick_detections(self):
        # will be testing this on rig 3
        print(f'lick pin for ir spout is {self.ir_spout.ir_lick_pin}')
        print(f'lick pin for capacitivate spout is {self.spout1.lick_pin}')
        print(f'water pin is {self.ir_spout.water_pin}')

        try:
            time_limit = 60
            start = time.time()
            ir_lick_counter = 0
            cap_lick_counter = 0
            ir_lick_start_time = []
            cap_lick_start_time = []

            ir_lick_end_time = []
            cap_lick_end_time = []
            while start + time_limit > time.time():
                ir_lick_change = self.ir_spout.lick_status_check()
                cap_lick_change = self.spout1.lick_status_check()
                if ir_lick_change == 1:
                    print(f"ir start lick {ir_lick_counter} at {time.time()}")
                    ir_lick_counter += 1
                    ir_lick_start_time.append(time.time())
                elif ir_lick_change == -1:
                    print(f"end lick {ir_lick_counter} at {time.time()}")
                    ir_lick_end_time.append(time.time())
                elif cap_lick_change == 1:
                    print(f"cap start lick {cap_lick_counter} at {time.time()}")
                    cap_lick_counter += 1
                    cap_lick_start_time.append(time.time())
                elif cap_lick_change == -1:
                    print(f"end lick {cap_lick_counter} at {time.time()}")
                    cap_lick_end_time.append(time.time())
        finally:
            print(f'start time difference of two spouts {ir_lick_start_time - cap_lick_start_time}')
            print(f'end time difference of two spouts {ir_lick_end_time - cap_lick_end_time}')

            self.ir_spout.shutdown()

    def test_visual_cue(self):
        start = time.time()
        time_limit = 20
        while start + time_limit > time.time():
            self.visual.screen.fill((0, 0, 0))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.visual.cue_on()
                        print("space is pressed")
                    if event.key == pygame.K_ESCAPE:
                        self.visual.shutdown()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE:
                        self.visual.cue_off()
                        print("space is released")
            # if self.visual.cue_displaying:
            #     self.visual.cue_on()
            pygame.display.update()
        self.visual.shutdown()
        print("TIME IS UP")

#-------------deprecated LED function------------------need other pins
    # def test_LED(self):
    #     time_limit = 30
    #     start = time.time()
    #     while start + time_limit > time.time():
    #
    #         self.LED.set_color("l")
    #         time.sleep(5)
    #         self.LED.cue_on()
    #         time.sleep(5)
    #         self.LED.set_color("s")
    #         time.sleep(5)
    #         self.LED.cue_on()
    #     self.LED.shutdown()


    def test_audio(self, auditory):
        if auditory == 1:
            testing_auditory = self.auditory1
        elif auditory == 2:
            testing_auditory = self.auditory2
        else:
            print("no more than 2 auditory ports assembled")
        time_limit = 30
        start = time.time()
        pygame.init()
        while start + time_limit > time.time():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        testing_auditory.cue_on()
                        print("space is pressed")
                    if event.key == pygame.K_ESCAPE:
                        testing_auditory.shutdown()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE:
                        testing_auditory.cue_off()
                        print("space is released")
        testing_auditory.shutdown()

    def test_visual_tk(self):
        self.running = True
        while self.running:
            self.visual.visual_control_with_after()


    def test_water(self, run_time, open_time, cool_time, spout):
        if spout == 1:
            testing_spout = self.spout1
        elif spout == 2:
            testing_spout = self.spout2
        else:
            print("no more than 2 spouts assembled")

        try:
            for i in range(run_time):
                testing_spout.water_on(.1)
                time.sleep(open_time)
                print('drop delivered')
                testing_spout.water_off()
                time.sleep(cool_time)
        finally:
            testing_spout.shutdown()
            self.running = False

    def test_trigger(self, time_limit=200):
        """tests square wave"""
        while self.start_time + time_limit > time.time():
            self.trigger.square_wave(self.status)
        self.end()

    def test_two_spouts_with_audio(self, time_limit):
        start_time = time.time()
        while time.time() - start_time <= time_limit:
            lick1 = self.spout1.lick_status_check()
            lick2 = self.spout2.lick_status_check()

            if lick1 == 1:
                print(f"start lick spout 1")
                self.auditory1.cue_on()
            elif lick1 == -1:
                print(f"stop lick spout 1")
                self.auditory1.cue_off()
            elif lick2 == 1:
                print(f"start lick spout 2")
                self.auditory2.cue_on()
            elif lick2 == -1:
                print(f"stop lick spout 2")
                self.auditory2.cue_off()


    def test_visual_with_lick(self):
        # self.visual.initialize()
        time_limit = 30
        start = time.time()
        lick_counter = 0
        try:
            while start + time_limit > time.time():
                self.running = True
                self.visual.screen.fill((0, 0, 0))
                lick_change = self.spout.lick_status_check()
                if lick_change == 1:
                    print(f"start lick {lick_counter}")
                    self.visual.cue_on()
                    self.spout.water_on(.01)
                elif lick_change == -1:
                    self.visual.cue_off()
                    print(f"end lick {lick_counter} at {time.time()}")
                    lick_counter += 1
                    self.spout.water_off()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                if self.visual.cue_displaying:
                    self.visual.cue_on()
                pygame.display.update()
        finally:
            GPIO.cleanup()
            print("GPIO cleaned up")
            self.visual.shutdown()

    def lick_validation(self, n_licks=15, time_limit=500, spout =1):
        if spout == 1:
            testing_spout = self.spout1
        elif spout == 2:
            testing_spout = self.spout2
        else:
            print("no more than 2 spouts assembled")

        start_time = time.time()
        lick_counter = 0
        lick_display_counter = 0
        reward_counter = 0
        try:
            while start_time + time_limit > time.time():
                self.trigger.square_wave(self.data_writer)
                testing_spout.water_cleanup()
                self.running = True
                lick_change = testing_spout.lick_status_check()
                if lick_change == 1:
                    lick_counter += 1
                    lick_display_counter += 1
                    string = f'{reward_counter},{time.time()-start_time},{lick_change},lick'
                    self.data_writer.log(string)
                    print(f"start lick {lick_display_counter}")
                elif lick_change == -1:
                    string = f'{reward_counter},{time.time() - start_time},{lick_change},lick'
                    self.data_writer.log(string)
                    print(f"end lick {lick_display_counter} at {time.time()-start_time:.2f} seconds")
                if lick_counter >= n_licks:
                    lick_counter = 0
                    testing_spout.water_on(.1)
                    reward_counter += 1
        finally:
            testing_spout.shutdown()
            self.data_writer.end()  # sends file to pc and deletes from pi
            self.running = False

    def reset(self):
        self.spout.shutdown()


