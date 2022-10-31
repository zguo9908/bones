"""
Example script for recording video with raspberry pi camera and converting to .mp4 file format
ckw 5/13/22

Requires ffmpeg
sudo apt install -y ffmpeg
"""

from picamera import PiCamera
import time
from datetime import datetime
import subprocess

camera = PiCamera(resolution=(1280, 720), framerate=32)
camera.color_effects = (128,128)
# camera.iso = 600
time.sleep(2)
camera.exposure_mode = 'off'
camera.shutter_speed = 80000
camera.awb_mode = 'off'
camera.awb_gains = 2
now = datetime.now() # current date and time
video_filename = (now.strftime("%Y%m%d%H%M%S"))
camera.start_recording(video_filename + '.h264')
print('Video recording started')

time.sleep(60)

camera.stop_recording()
print('Video recording stopped')

# re-wraps the video
# -r 32 refers to the framerate of the input video (from picamera)
command = "ffmpeg -r 32 -i {fname}.h264 -vcodec copy {fname}.mp4".format(fname = video_filename)

# actually demux/remuxes the video (very slow)
# command = "ffmpeg -r 32 -i {fname}.h264 -r 32 {fname}.mp4".format(fname = video_filename)

subprocess.call(command, shell=True)
print('Video converted to mp4')