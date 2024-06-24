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


if __name__ == '__main__':
    #PiTest("ZG002", "exp1").test_audio(1)
   # PiTest("ZG000","exp1").test_pi_camera_preview()
    PiTest("ZG014", "exp1").test_water(run_time = 30, open_time=0.2, cool_time=0.2, spout=3, test_vibration=True)
    # PiTest("ZG001", "exp1").test_two_spouts_with_audio(time_limit = 30)
    # PiTest("RZ002", "exp1").lick_validation(time_limit = 30)
    #PiTest("RZ001", "exp1").reset()
   #PiTest("ZG000",'exp1').test_two_lick_detections()
   #  PiTest("ZG000",'exp1').test_lick_recording()
   # PiTest("ZG000", 'exp1').test_trigger()
   # GiveUpTask("ZG040", "exp1", "no_block_shaping", "param_v2_cue_bg").run()





