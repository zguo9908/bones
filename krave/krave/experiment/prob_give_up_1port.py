import statistics
import time
import random
import math
import numpy as np
from krave.experiment import states
from krave import utils
from krave.hardware.auditory import Auditory
from krave.hardware.spout import Spout
from krave.hardware.trigger import Trigger
from krave.output.data_writer import DataWriter
from krave.experiment import timescapes
from krave.experiment import exp_utils
import tkinter as tk
import tkinter.font as font
from threading import Thread
# ONE PORT VERSION OF THE GIVE-UP TASK IN A HEAD FIXED SET UP.
# EQUAL TO THE FORCED TRIALS.
stop = False
stopped = False


class Block:
    def __init__(self,mean_reward_time,overall_reward_prob, time_array):
        self.mean_reward_time = mean_reward_time
        self.overall_reward_prob = overall_reward_prob
        self.n_of_trials = None
        self.trial_bg_times = None
        self.reward_pdf, self.reward_cdf = timescapes.exp_decreasing(time_array, 0, mean_reward_time)


class GiveUpTask:
    def __init__(self, mouse, exp_name, training, calibrate=False, record=False, forward = True):

        self.total_trial_num = None
        self.mouse = mouse
        self.exp_name = exp_name
        self.exp_config = self.get_config()
        self.hardware_name = self.exp_config['hardware_setup']
        self.training = training
        self.calibrate = calibrate
        self.record = record

        # hardwares
        self.spout = Spout(self.mouse, self.exp_config, spout_name="2")
        self.auditory = Auditory(self.mouse, self.exp_config, audio_name = "1", trial_type='s')
        # print(self.spout.water_pin)
        self.data_writer = DataWriter(self.mouse, self.exp_name, self.training, self.exp_config, forward)
        # self.camera_trigger = CameraTrigger(self.mouse, self.exp_config)

        # timescape information
        self.mean_reward_time_s = self.exp_config['exp_blocks']['s'][0]
        self.mean_reward_time_l = self.exp_config['exp_blocks']['l'][0]

        self.overall_reward_prob_s = self.exp_config['exp_blocks']['s'][1]
        self.overall_reward_prob_l = self.exp_config['exp_blocks']['l'][1]

        self.curr_mean_reward_time = None
        self.curr_overall_reward_prob = None

        self.reward_size = self.exp_config['reward_size']
        self.step_size = self.exp_config['step_size']

        # task type
        if self.training == 'shaping':
            self.auto_delivery = True
            self.sometimes_not_rewarded = False
        elif self.training == 'regular':
            self.auto_delivery = False
            self.sometimes_not_rewarded = True
        else:
            raise Exception('Training type invalid')

        # session structure
        self.blocks = self.exp_config['exp_blocks']
        self.time_limit = self.exp_config['time_limit']
        self.max_reward_count = self.exp_config['max_reward_count']
        self.total_blocks = self.exp_config['total_blocks']  # total number of blocks per session
        self.total_trials_median = self.exp_config['total_trials_median']  # median number of trials per session
        self.block_length_range = self.exp_config['block_length_range']
        self.curr_reward_prob = None
        self.session_dict = dict.fromkeys(range(self.total_blocks))
        self.optimal_dict = dict.fromkeys(range(self.total_blocks))
        self.total_trial_num = None
        self.trial_list = None
        self.optimal_list = None
        self.block_len = None
        self.block_list = []

        # trial structure variables
        self.time_bg_range = self.exp_config['time_bg_range']
        self.consumption_time = self.exp_config['consumption_time']
        self.punishment_time = self.exp_config['punishment_time']
        self.max_wait_time = self.exp_config['max_wait_time']


        self.time_array = np.round(np.arange(0, self.max_wait_time, self.step_size),
                                   exp_utils.get_precision(self.step_size) + 1)
        # session variables

        # times
        self.session_start_time = None
        self.block_start_time = None
        self.trial_start_time = float('-inf')
        # self.cue_start_time = None
        self.wait_start_time = float('-inf')
        self.consumption_start = None
        self.background_start_time = None
        self.punishment_start = None
        self.bin_num = None

        # where we are
        self.block_num = -1
        self.block_trial_num = -1
        self.session_trial_num = -1
        self.curr_block = None

        self.time_bg = None  # average bg time of the block
        self.time_bg_drawn = None  # drawn bg time from uniform distribution
        self.time_wait_optimal = None
        self.state = states.IN_BACKGROUND
        self.lick_counter = 0
        self.total_reward_count = 0


    def get_config(self):
        """Get experiment config from json"""
        return utils.get_config('krave.experiment', f'config/{self.exp_name}.json')

    def get_string_to_log(self, event):
        return f'{time.time()-self.trial_start_time},{time.time()-self.wait_start_time},' \
               f'{self.block_num},{self.session_trial_num},{self.block_trial_num},{self.state},{self.time_bg},' \
               f'{self.curr_mean_reward_time},{self.curr_overall_reward_prob}, {self.total_reward_count},' + event

    def log_lick(self):
        """logs lick using data writer"""
        if self.wait_start_time is not None:
            print(f"lick {self.lick_counter} at {time.time() - self.wait_start_time:.2f} seconds of the wait"
                  f" and at {time.time() - self.trial_start_time:.2f} seconds of the trial")
        else:
            print(f"lick {self.lick_counter} at {time.time() - self.trial_start_time:.2f} seconds of the trial")
        self.lick_counter += 1
        string = self.get_string_to_log(f'{self.curr_reward_prob},1,lick')
        self.data_writer.log(string)

    def log_lick_ending(self):
        """logs lick ending using data writer"""
        string = self.get_string_to_log('nan,0,lick')
        self.data_writer.log(string)

    def get_block(self,block_stats):
        if block_stats[0] == self.mean_reward_time_s:
            block = Block(self.mean_reward_time_s, self.overall_reward_prob_s, self.time_array)
            self.curr_mean_reward_time = self.mean_reward_time_s
            self.curr_overall_reward_prob = self.overall_reward_prob_s
            print("short block created")
        else:
            block = Block(self.mean_reward_time_l, self.overall_reward_prob_l, self.time_array)
            self.curr_mean_reward_time = self.mean_reward_time_l
            self.curr_overall_reward_prob = self.overall_reward_prob_l
            print('long block created')
        print(block.mean_reward_time)
        return block

    def get_wait_time_optimal(self):
        """
        makes a dictionary with block num as key and a list of optimal wait time for each trial as values
        runs for shaping tasks when reward delivery is not lick triggered
        this function is a bit slow, so must be run before session starts
        """
        print('Calculating optimal wait times')
        count = 0  # used
        total_list = []  # used to check if there are none values in the dict
        # if not self.random_draw:
        for blk in self.session_dict:
            optimal_list = []
            for trl in self.session_dict[blk]:
                optimal_list.append(utils.calculate_time_wait_optimal(trl))
            count += len(optimal_list)
            total_list.append(optimal_list)
            self.optimal_dict[blk] = optimal_list
        # else:
        #     self.time_bg = self.session_dict[1][1]
        #     optimal_time = utils.calculate_time_wait_optimal(self.time_bg)
        #     for blk in self.session_dict:
        #         optimal_list = [optimal_time]*len(self.session_dict[blk])
        #         count += len(optimal_list)
        #         total_list.append(optimal_list)
        #         self.optimal_dict[blk] = optimal_list

        if count != self.total_trial_num:
            raise Exception(f'Missing {self.total_trial_num - count} optimal values!')
        if None in total_list:
            raise ValueError('None values in optimal_dict')

    def get_session_structure(self):
        """
        determines the session structure based on the number of blocks and type of blocks
        :return: length of each block, and bg time of each block
        """
        trials_per_block = self.total_trials_median // self.total_blocks
        trials_per_block_min = trials_per_block - self.block_length_range
        trials_per_block_max = trials_per_block + self.block_length_range
        block_lengths = []

        # make two block types alternate
        for i in range(self.total_blocks):
            block_lengths.append(random.randint(trials_per_block_min, trials_per_block_max))
        self.total_trial_num = sum(block_lengths)
        print(self.total_trial_num)

        block_stats_list = []
        block_types = list(self.blocks.values())
        first_block_stats = random.choice(block_types)
        first_block = self.get_block(first_block_stats)
        # first_block.n_of_trials = block_lengths[i]

        for i in range(self.total_blocks):
            if i % 2 == 0:
                self.block_list.append(first_block)
                block_stats_list.append(first_block_stats)
                print(f'{first_block.mean_reward_time} is first block so are all even blocks')
            else:
                if first_block_stats == block_types[0]:
                    print("first block is short so odd block is long")
                    print(block_types[1])
                    self.block_list.append(self.get_block(block_types[1]))
                    block_stats_list.append(block_types[1])

                else:
                    print("first block is long so odd block is short")
                    print(block_types[0])
                    self.block_list.append(self.get_block(block_types[0]))
                    block_stats_list.append(block_types[0])

            self.block_list[i].n_of_trials = block_lengths[i]
            print(block_stats_list)
        count = 0


        # l is block length, t is block trial stats
        for i, (l, t) in enumerate(zip(block_lengths, block_stats_list)):
            # low and high background time, t[-1] is background time
            low = t[-1] - self.time_bg_range
            high = t[-1] + self.time_bg_range
            # if self.random_draw:
            drawn_times = np.random.uniform(low, high, l).tolist()
            drawn_times = [round(item, 1) for item in drawn_times]
            self.session_dict[i] = drawn_times
            count += len(drawn_times)
            print(self.session_dict[i])
            # else:
            #     self.session_dict[i] = [t[-1]] *l
            #     print(self.session_dict[i])
            #     count += len(self.session_dict[i])


        # print(self.session_dict)
        if count != self.total_trial_num:
            raise Exception('Missing time_bg!')

        print(f'length of each block: {block_lengths}')
        # print(f'bg time of each block: {self.block_list}')
        print(f'{self.total_trial_num} trials total')


    def start_trial(self):
        """Starts a trial within a block"""
        self.bin_num = 0  # bin of current time/reward probability
        self.block_trial_num += 1
        self.session_trial_num += 1
        # print(self.block_trial_num)
        # print(len(self.trial_list))
        # print(self.block_len)
        self.time_bg_drawn = self.trial_list[self.block_trial_num]

        if self.auto_delivery:
            self.time_wait_optimal = self.optimal_list[self.block_trial_num]
        self.trial_start_time = time.time()
        self.background_start_time = self.trial_start_time
        self.state = states.IN_BACKGROUND

        string = self.get_string_to_log('nan,1,trial')
        self.data_writer.log(string)
        print(f"block {self.block_num} trial {self.block_trial_num, self.session_trial_num} bg_time "
              f"{self.time_bg_drawn:.2f}s starts at {self.trial_start_time - self.session_start_time:.2f} seconds")
        if self.auto_delivery:
            print(f'time_wait_optimal: {self.time_wait_optimal}')

    def end_trial(self):
        """ends a trial"""
        self.state = states.TRIAL_ENDS
        string = self.get_string_to_log('nan,0,trial')
        self.data_writer.log(string)


    def start_consumption(self):
        self.auditory.cue_off()
        self.spout.water_on(self.reward_size)
        self.state = states.IN_CONSUMPTION
        self.consumption_start = time.time()
        string = self.get_string_to_log('nan,1,reward')
        self.data_writer.log(string)
        self.total_reward_count += 1
        print(f'reward delivered, {self.total_reward_count} total,'
              f' which is {self.total_reward_count * self.reward_size} ul')

    def start_wait(self):
        self.bin_num = 0
        print("starting to bin the cdf")
        self.state = states.IN_WAIT
        self.auditory.cue_on()
        string = self.get_string_to_log('nan,1,audio')
        self.data_writer.log(string)
        self.wait_start_time = time.time()
        string = self.get_string_to_log('nan,1,wait')
        self.data_writer.log(string)

    def start_background(self):
        """starts background time, logs using data writer, trial does not restart if repeated"""
        self.state = states.IN_BACKGROUND
        self.background_start_time = time.time()
        self.wait_start_time = float('-inf')
        string = self.get_string_to_log('nan,1,background')
        self.data_writer.log(string)
        print('background time starts')

    def start(self):
        """
        starts a session and initiates display to all black
        """
        self.get_session_structure()
        if self.auto_delivery:
            self.get_wait_time_optimal()
        self.session_start_time = time.time()
        string = self.get_string_to_log('nan,1,session')
        self.data_writer.log(string)
        self.start_block()

    def end(self):
        """
        end a session and shuts all systems
        """
        # print(f'performance for this session is {self.total_reward_count/self.total_trial_num}%2f')
        string = self.get_string_to_log('nan,0,session')
        self.data_writer.log(string)
        global stopped
        if stopped:
            self.data_writer.log(self.get_string_to_log('nan,0,end_via_button'))
        else:
            self.data_writer.log(self.get_string_to_log('nan,0,ran_to_end'))

        self.auditory.shutdown()
        # self.spout.shutdown()
        self.data_writer.end()

    def start_block(self):
        """
        starts a block within a session
        determines number of trials in the block and avg bg time
        starts the first trial of the block
        """
        self.curr_block = self.block_list[self.block_num]
        print(f'{self.curr_block.mean_reward_time} as current mean reward time')
        self.block_num += 1
        self.block_trial_num = -1  # to make sure correct indexing because start_trial is called in this function
        self.block_start_time = time.time()
        self.trial_list = self.session_dict[self.block_num]
        #     # maybe, don't need these
        self.curr_mean_reward_time = self.curr_block.mean_reward_time
        if self.curr_mean_reward_time == 3:
            self.auditory.set_frequency('l')
        else:
            self.auditory.set_frequency('s')
        if self.sometimes_not_rewarded:
             self.curr_overall_reward_prob = self.curr_block.overall_reward_prob
        else:
            self.curr_overall_reward_prob = 1

        if self.auto_delivery:
            self.optimal_list = self.optimal_dict[self.block_num]
        self.block_len = len(self.trial_list)
        print(self.trial_list)
        self.time_bg = statistics.fmean(self.trial_list)

        string = self.get_string_to_log('nan,1,block')
        self.data_writer.log(string)
        print(f"block {self.block_num} with bg_time {self.time_bg:.2f} sec; mean reward time {self.curr_mean_reward_time:.2f}"
              f" and overall reward prob {self.curr_overall_reward_prob} "        
              f"starts at {self.block_start_time - self.session_start_time:.2f} seconds")
        self.start_trial()


    def run(self):
        """
        regular behavior session
        """
        print(f"trial type {self.training} ; optimal delivery {self.auto_delivery}")
        self.start()
        # cue_start = None
        global stop
        global stopped

        # t1 = Thread(target=StopButton)
        # t1.start()
        try:
            if self.calibrate:
                self.spout.calibrate()
            while self.session_start_time + self.time_limit > time.time():
                self.spout.water_cleanup()
                self.auditory.cue_cleanup()
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

                if  self.bin_num > len(self.curr_block.reward_cdf)-1:
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


    def start_punishment(self):
        """starts punishment time, logs using data writer, trial does not restart"""
        self.state = states.IN_PUNISHMENT
        self.punishment_start = time.time()

        string = self.get_string_to_log('nan,1,punishment')
        self.data_writer.log(string)
        print('early lick, punishment')

    def end_punishment(self):
        """ends punishment time, logs using data writer, enters bg time"""
        self.state = states.IN_BACKGROUND
        self.trial_start_time = time.time()

        string = self.get_string_to_log('nan,0,punishment')
        self.data_writer.log(string)
        print('start background time')

class StopButton:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("300x200")
        self.root.title('Google Upload')
        my_font = font.Font(size=16)
        self.text = tk.StringVar(value='Stop After Current Upload')
        self.button = tk.Button(
            master=self.root,
            textvariable=self.text,
            font=my_font,
            width=40,
            height=12,
            bg="white",
            fg="black",
            command=self.stop)
        self.button.pack()
        self._job = self.root.after(1000, self.check_continue)
        self.root.mainloop()

    def stop(self):
        global stop
        stop = True
        self.text.set('stopping...')

    def check_continue(self):
        global stopped
        if stopped:
            if self._job is not None:
                self.root.after_cancel(self._job)
                self._job = None
            self.root.destroy()
        else:
            self._job = self.root.after(1000, self.check_continue)
