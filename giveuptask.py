def runGiveUpTask_try(animalID, itiDuration, totalDuration, rewardLength, date_time, stimulusDistribution, timeout):
    import numpy as np
    from csv import writer
    import RPi.GPIO as GPIO
    import os
    import time
    import warnings
    import datetime
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # navigate to the folder that will contain the csv file
    filepath = '/home/pi/Data/' + animalID
    if not os.path.exists(filepath):
        print('Something''s wrong there''s no Data folder for this animal.')
        return
    else:
        os.chdir(filepath)
