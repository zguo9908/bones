import time
import random
import math
import numpy as np
from krave.experiment import states

from krave import utils
from krave.hardware.auditory import Auditory
from krave.hardware.spout import Spout
from krave.hardware.visual import Visual
from krave.hardware.trigger import CameraTrigger
from krave.output.data_writer import DataWriter
import pygame

class Task:
    def __init__(self, mouse, exp_name, force_perc, calibrate=False, record=False):

        self.choice_trial_num = None
        self.force_trial_num = None
        self.trial_type = None
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
        self.session_length_range = self.exp_config['session_length_range']

        self.session_start_time = None
        self.trial_start_time = None
        self.session_trial_num = 0
        self.time_bg = None  # average bg time of the block
        self.time_bg_drawn = None  # drawn bg time for exponential distribution
        self.random_draw = True
        self.state = "in_background"
        self.force_perc = force_perc # percentage of forced trials, equally split for left vs right
        self.total_trial_num = None

    def get_session_structure(self):

        self.total_trial_num = random.randint(self.total_trials_median - self.session_length_range,
                                              self.total_trials_median + self.session_length_range)
        self.force_trial_num = math.floor(self.total_trial_num * self.force_perc)
        self.choice_trial_num = self.total_trial_num - self.force_trial_num
    #     a session would start with forced trials and

    def get_string_to_log(self, event):
        return f'{time.time() - self.trial_start_time},{time.time() - self.wait_start_time}, {self.trial_type}' \
               f'{self.session_trial_num},{self.state},{self.time_bg},{self.curr_spout}' \
               f'{self.total_reward_count},' + event


    def log_lick(self):
        """logs lick using data writer"""
        if self.wait_start_time is not None:
            print(f"lick {self.lick_counter} at {time.time() - self.wait_start_time:.2f} seconds of the wait"
                  f" and at {time.time() - self.trial_start_time:.2f} seconds of the trial")
        else:
            print(f"lick {self.lick_counter} at {time.time() - self.trial_start_time:.2f} seconds of the trial")
        self.lick_counter += 1
        # 1 means spout 1, 2 means spout 2
        string = self.get_string_to_log(f'{self.curr_reward_prob},1,lick')
        self.data_writer.log(string)

    def run(self):
        """
        regular behavior session
        """
        print(f"trial type {self.training} ; optimal delivery {self.auto_delivery}")
        self.start()

        try:
            if self.calibrate:
                self.spout.calibrate()
            while self.session_start_time + self.time_limit > time.time():
                self.spout1.water_cleanup()
                self.spout2.water_cleanup()
                self.auditory1.cue_cleanup()
                self.auditory2.cue_cleanup()

                if self.record:
                    self.camera_trigger.square_wave(self.data_writer)

                if self.state == states.IN_WAIT:
                    if (time.time() - self.wait_start_time) // self.step_size > self.bin_num:
                        self.bin_num += 1

                lick_change = self.spout.lick_status_check()
                if lick_change == -1:
                    self.log_lick_ending()
                elif lick_change == 1:
                    self.log_lick()

                    if not self.auto_delivery:
                        # prob_not_rewarded = 1 - self.curr_block.reward_cdf[self.bin_num]
                        # prob_rewarded_at_t = self.curr_block.reward_pdf[self.bin_num]
                        # self.curr_reward_prob = (prob_rewarded_at_t / prob_not_rewarded) * self.overall_reward_prob
                        if self.state == states.IN_WAIT:
                            self.curr_reward_prob = self.curr_block.reward_cdf[self.bin_num]
                            print(f'current bin number is {self.bin_num}')
                            print(f"reward probability is {self.curr_reward_prob}")
                            if self.curr_reward_prob > random.random():
                                self.start_consumption()
                            else:
                                print('early lick fail the trial')
                                self.end_trial()
                        elif self.state == states.IN_BACKGROUND:
                            print("still in back ground, restarting")
                            self.start_background()

                        # else:
                        #     # lick is decision to leave
                        #     print("licked before ")
                        #     self.end_trial()

                if self.state == states.IN_BACKGROUND and time.time() > self.background_start_time + self.time_bg_drawn:
                    # bg time passed, wait time starts
                    self.start_wait()

                if self.state == states.IN_CONSUMPTION and time.time() > self.consumption_start + self.consumption_time:
                    # consumption time passed, trials ends
                    self.end_trial()

                if self.state == states.IN_WAIT:
                    if self.auto_delivery and time.time() > self.wait_start_time + self.time_wait_optimal:
                        self.start_consumption()
                    elif not self.auto_delivery and time.time() > self.wait_start_time + self.max_wait_time:
                        print('no lick, miss trial')
                        self.end_trial()

                if self.state == states.IN_PUNISHMENT and time.time() > self.punishment_start + self.punishment_time:
                    # punishment ends -> bg time
                    self.end_punishment()

                if self.bin_num > len(self.curr_block.reward_cdf) - 1:
                    print("exceeds max bin numbers in the trial, starting next one")
                    self.end_trial()

                # session ends if total num of trials is reached, or if reward received is larger than 1.5 ml
                if self.state == states.TRIAL_ENDS:
                    self.auditory.cue_off()
                    if self.session_trial_num + 1 == self.total_trial_num:
                        print('total_trial_num reached')
                        break
                    elif self.total_reward_count >= self.max_reward_count:
                        print('max reward count reached')
                        break
                    elif self.block_trial_num + 1 == self.block_len:
                        print("starting next block")
                        self.start_block()
                    else:
                        self.start_trial()
                # if stop:
                #     stopped = True
                #     print('stopped via stop button')
                #     break
        finally:
            self.end()
