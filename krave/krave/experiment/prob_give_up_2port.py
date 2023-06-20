import time
import random
import math
import numpy as np
from krave.experiment import states, timescapes, exp_utils

from krave import utils
from krave.hardware.auditory import Auditory
from krave.hardware.spout import Spout
from krave.hardware.visual import Visual
from krave.hardware.trigger import Trigger
from krave.output.data_writer import DataWriter
import pygame

class ChoiceTask:
    def __init__(self, mouse, exp_name, session_type, calibrate=False, record=False):

       # basic config
        self.mouse = mouse
        self.exp_name = exp_name
        self.exp_config = self.get_config()
        self.hardware_name = self.exp_config['hardware_setup']
        self.calibrate = calibrate
        self.record = record
        # initialize objects
        self.spout1 = Spout(self.mouse, self.exp_config, spout_name="1")
        self.spout2 = Spout(self.mouse, self.exp_config, spout_name="2")
        self.better_spout = None
        # self.visual = Visual(self.mouse, self.exp_config)
        self.auditory1 = Auditory(self.mouse, self.exp_config, audio_name = "1")
        self.auditory2 = Auditory(self.mouse, self.exp_config, audio_name = "2")
        self.data_writer = DataWriter(self.mouse, self.exp_name, self.exp_config)
        # self.camera_trigger = CameraTrigger(self.mouse, self.exp_config)

        # exp config
        self.time_limit = self.exp_config['time_limit']
        self.session_length = self.exp_config['session_length']  # number of blocks per session
        self.consumption_time = self.exp_config['consumption_time']
        self.punishment_time = self.exp_config['punishment_time']
        self.max_wait_time = self.exp_config['max_wait_time']
        self.mean_reward_time = self.exp_config['mean_reward_time']
        self.overall_reward_prob = self.exp_config['overall_reward_prob']
        self.reward_size = self.exp_config['reward_size']
        self.session_length_range = self.exp_config['session_length_range']
        self.total_trials_median = self.exp_config['total_trials_median']
        self.force_perc = self.exp_config['forced_trial_perc']
        self.time_bg_range = self.exp_config['time_bg_range']
        self.session_bg_time = self.exp_config[session_type]

        # other important experiment stuff
        self.curr_reward_prob = None
        self.trial_bg_list = None
        self.session_trial_list = None
        self.bin_num = None
        self.num_miss_trial = None
        self.consumption_start = None
        self.choice_trial_num = None
        self.force_trial_num = None
        self.trial_type = None
        self.s1l2 = None
        self.time_array = np.round(np.arange(0, self.max_wait_time, self.step_size),
                                   exp_utils.get_precision(self.step_size) + 1)
        self.session_start_time = None
        self.trial_start_time = None
        self.session_trial_num = 0
        self.time_bg = None  # average bg time of the block
        self.time_bg_drawn = None  # drawn bg time for exponential distribution
        self.random_draw = True
        self.state = "in_background"
        # self.force_perc = force_perc # percentage of forced trials, equally split for left vs right
        self.total_trial_num = None
        self.reward_cdf1 = None
        self.reward_cdf2 = None
        self.overall_reward_prob1 = None
        self.overall_reward_prob2 = None

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

    def get_session_structure(self):
        if random.random > 0.5: # trial type where spout 1 is s and spout 2 is l
            self.s1l2 = True
            self.reward_cdf1 = timescapes.exp_decreasing(self.time_array, 0, self.exp_config['timescapes']['s'][0])
            self.overall_reward_prob1 = self.exp_config['timescapes']['s'][1]
            self.reward_cdf2 = timescapes.exp_decreasing(self.time_array, 0, self.exp_config['timescapes']['l'][0])
            self.overall_reward_prob2 = self.exp_config['timescapes']['l'][1]
        else:
            self.s1l2 = False
            self.reward_cdf1 = timescapes.exp_decreasing(self.time_array, 0, self.exp_config['timescapes']['l'][0])
            self.overall_reward_prob1 = self.exp_config['timescapes']['l'][1]
            self.reward_cdf2 = timescapes.exp_decreasing(self.time_array, 0, self.exp_config['timescapes']['s'][0])
            self.overall_reward_prob2 = self.exp_config['timescapes']['s'][1]

        self.total_trial_num = random.randint(self.total_trials_median-self.session_length_range,
                                             self.total_trials_median+self.session_length_range)
        # self.force_trial_num = math.floor(self.total_trial_num * self.force_perc)
        # self.choice_trial_num = self.total_trial_num - self.force_trial_num
        self.session_trial_list = []
        self.trial_bg_list = []
        for i in range(self.total_trial_num):
            if self.force_perc > random.random():
                if random.random > 0.5:
                    self.session_trial_list[i] = 1
                else:
                    self.session_trial_list[i] = 2
            else:
                self.session_trial_list[i] = 0
            self.trial_bg_list[i] = random.random(self.session_bg_time-self.time_bg_range,
                                                  self.session_bg_time+self.time_bg_range)

    def start(self):
        """
        starts a session and initiates display to all black
        """
        self.get_session_structure()
        if self.auto_delivery:
            self.get_wait_time_optimal()
        self.session_start_time = time.time()
        self.running = True
        string = self.get_string_to_log('nan,nan,1,session')
        self.data_writer.log(string)
        # self.start_block()

    def start_trial(self):
        """Starts a trial within a block"""
        self.bin_num = 0  # bin of current time/reward probability
        self.session_trial_num += 1
        self.time_bg_drawn = self.trial_bg_list[self.session_trial_numm]

        if self.auto_delivery:
            self.time_wait_optimal = self.optimal_list[self.session_trial_num]
        self.trial_start_time = time.time()
        self.background_start_time = self.trial_start_time
        self.state = states.IN_BACKGROUND

        string = self.get_string_to_log('nan,nan,1,trial')
        self.data_writer.log(string)
        print(f"trial {self.session_trial_num} bg_time "
              f"{self.time_bg_drawn:.2f}s starts at "
              f"{self.trial_start_time - self.session_start_time:.2f} seconds")

        if self.auto_delivery:
            print(f'time_wait_optimal: {self.time_wait_optimal}')

    def get_wait_time_optimal(self):


    def log_lick(self, spout):
        """logs lick using data writer"""
        if self.wait_start_time is not None:
            print(f"lick {self.lick_counter} at {time.time() - self.wait_start_time:.2f} seconds of the wait"
                  f" and at {time.time() - self.trial_start_time:.2f} seconds of the trial")
        else:
            print(f"lick {self.lick_counter} at {time.time() - self.trial_start_time:.2f} seconds of the trial")
        self.lick_counter += 1
        # 1 means spout 1, 2 means spout 2
        string = self.get_string_to_log(f'{self.curr_reward_prob},{spout},1,lick')
        self.data_writer.log(string)

    def log_lick_ending(self, spout):
        """logs lick ending using data writer"""
        string = self.get_string_to_log(f'nan,{spout},0,lick')
        self.data_writer.log(string)

    def start_consumption(self,spout):
        if spout == 1:
            curr_spout = self.spout1
        else:
            curr_spout = self.spout2
        if self.trial_type == 0:
            self.auditory1.cue_off()
            self.auditory2.cue_off()
        elif self.trial_type ==1:
            self.auditory1.cue_off()
        elif self.trial_type == 2:
            self.auditory2.cue_off()
            
        curr_spout.water_on(self.reward_size)
        self.state = states.IN_CONSUMPTION
        self.consumption_start = time.time()
        string = self.get_string_to_log(f'nan,{spout},1,reward')
        self.data_writer.log(string)
        self.total_reward_count += 1
        self.num_miss_trial = 0  # resets miss trial count
        print(f'reward delivered on spout {spout}, {self.total_reward_count} total,'
              f' which is {self.total_reward_count * self.reward_size} ul')
        
    def start_wait(self):
        self.bin_num = 0
        print("starting to bin the cdf")
        self.state = states.IN_WAIT

        if self.trial_type == 1:
            self.auditory1.cue_on()
        elif self.trial_type == 2:
            self.auditory2.cue_on()
        elif self.trial_type == 0:
            self.auditory1.cue_on()
            self.auditory2.cue_on()

        string = self.get_string_to_log('nan,nan,1,audio')
        self.data_writer.log(string)
        self.wait_start_time = time.time()
        string = self.get_string_to_log('nan,nan,1,wait')
        self.data_writer.log(string)

    def start_background(self):
        """starts background time, logs using data writer, trial does not restart if repeated"""
        self.state = states.IN_BACKGROUND
        self.background_start_time = time.time()
        self.wait_start_time = float('-inf')
        string = self.get_string_to_log('nan,nan,1,background')
        self.data_writer.log(string)
        print('background time starts')


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

                lick_change_1 = self.spout1.lick_status_check()
                lick_change_2 = self.spout2.lick_status_check()

                if lick_change_1 == -1:
                    self.log_lick_ending(1)
                elif lick_change_1 == 1:
                    self.log_lick(1)

                    if not self.auto_delivery:
                        if self.state == states.IN_WAIT and (self.trial_type == 0 or self.trial_type == 1):
                            self.curr_reward_prob = self.reward_cdf1[self.bin_num] * self.overall_reward_prob1
                            print(f'current bin number is {self.bin_num}')
                            print(f"reward probability is {self.curr_reward_prob}")
                            if self.curr_reward_prob > random.random():
                                self.start_consumption(1)
                            else:
                                print('early lick fail the trial')
                                self.end_trial()
                        elif self.state == states.IN_WAIT and self.trial_type == 2:
                            print('lick to the wrong side in forced trial.')
                            self.end_trial()

                        elif self.state == states.IN_BACKGROUND:
                            print("still in back ground, restarting")
                            self.start_background()


                if lick_change_2 == -1:
                    self.log_lick_ending(2)
                elif lick_change_2 == 1:
                    self.log_lick(2)

                    if not self.auto_delivery:
                        if self.state == states.IN_WAIT and (self.trial_type == 0 or self.trial_type == 2):
                            self.curr_reward_prob = self.reward_cdf2[self.bin_num] * self.overall_reward_prob2
                            print(f'current bin number is {self.bin_num}')
                            print(f"reward probability is {self.curr_reward_prob}")
                            if self.curr_reward_prob > random.random():
                                self.start_consumption(2)
                            else:
                                print('early lick fail the trial')
                                self.end_trial()
                        elif self.state == states.IN_WAIT and self.trial_type == 1:
                            print('lick to the wrong side in forced trial.')
                            self.end_trial()

                        elif self.state == states.IN_BACKGROUND:
                            print("still in back ground, restarting")
                            self.start_background()


                if self.state == states.IN_BACKGROUND and time.time() > self.background_start_time + self.time_bg_drawn:
                    # bg time passed, wait time starts
                    self.start_wait()

                if self.state == states.IN_CONSUMPTION and time.time() > self.consumption_start + self.consumption_time:
                    # consumption time passed, trials ends
                    self.end_trial()

                if self.state == states.IN_WAIT:

                    if self.auto_delivery and time.time() > self.wait_start_time + self.time_wait_optimal:
                        if self.trial_type == 1 or self.better_spout == 1:
                            self.start_consumption(1)
                        elif self.trial_type == 2 or self.better_spout == 2:
                            self.start_consumption(2)

                    elif not self.auto_delivery and time.time() > self.wait_start_time + self.max_wait_time:
                        print('no lick, miss trial')
                        self.end_trial()

        finally:
            self.end()
