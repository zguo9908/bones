import os
import socket

from krave.experiment.hardware_test import PiTest
from krave.experiment.prob_give_up_1port import GiveUpTask
#!/usr/bin/env python3


#param_v1: s = 1, l = 3
#param_v2: s = 1.2, l = 3.3
#param_v3: s = 2, l = 3.8

def main(mouse, exp_name, hardware_config_name):
    pass

use_piezo = False

if __name__ == '__main__':
    #PiTest("ZG002", "exp1", use_piezo).test_audio(1)
  #  PiTest("ZG000","exp1", use_piezo).test_pi_camera_preview()
    PiTest("ZG014", "exp1", use_piezo).test_water(run_time = 30, open_time=0.1, cool_time=0.2)
    # PiTest("RZ002", "exp1", use_piezo).lick_validation(time_limit = 30)
    #PiTest("RZ001", "exp1", use_piezo).reset()
    #PiTest("ZG000",'exp1', use_piezo).test_two_lick_detections()
  #  PiTest("ZG000",'exp1', use_piezo).test_lick_recording()
   # PiTest("ZG000", 'exp1',use_piezo).test_trigger()
    #GiveUpTask("ZG047", "exp1", "no_block_regular", "param_v2_cue_bg", use_piezo=False).run()





