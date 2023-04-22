import time
import random
import math
import numpy as np

from krave import utils
from krave.hardware.auditory import Auditory
from krave.hardware.spout import Spout
from krave.hardware.visual import Visual
from krave.hardware.trigger import CameraTrigger
from krave.output.data_writer import DataWriter
import pygame

class Task:
    def __init__(self, mouse, exp_name, force_perc, calibrate=False, record=False):

        self.mouse = mouse
        self.exp_name = exp_name
        self.exp_config = self.get_config()
        self.hardware_name = self.exp_config['hardware_setup']
        self.calibrate = calibrate
        self.record = record

        self.spout1 = Spout(self.mouse, self.exp_config, spout_name="1")
        self.spout2 = Spout(self.mouse, self.exp_config, spout_name="2")
        # self.visual = Visual(self.mouse, self.exp_config)
        self.auditory1 = Auditory(self.mouse, self.exp_config, audio_name = "1")
        self.auditory2 = Auditory(self.mouse, self.exp_config, audio_name = "2")

        self.data_writer = DataWriter(self.mouse, self.exp_name, self.exp_config)
        # self.camera_trigger = CameraTrigger(self.mouse, self.exp_config)

        self.time_limit = self.exp_config['time_limit']
        self.session_length = self.exp_config['session_length']  # number of blocks per session
        self.consumption_time = self.exp_config['consumption_time']
        self.punishment_time = self.exp_config['punishment_time']
        self.max_wait_time = self.exp_config['max_wait_time']
        self.mean_reward_time = self.exp_config['mean_reward_time']
        self.overall_reward_prob = self.exp_config['overall_reward_prob']
        self.reward_size = self.exp_config['reward_size']

        self.session_start_time = None
        self.trial_start_time = None
        self.session_trial_num = 0
        self.time_bg = None  # average bg time of the block
        self.time_bg_drawn = None  # drawn bg time for exponential distribution
        self.random_draw = True
        self.state = "in_background"
        self.force_perc = force_perc # percentage of forced trials, equally split for left vs right


    def get_session_structure(self):
