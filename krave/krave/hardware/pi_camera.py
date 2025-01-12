# import picamera2
from picamera import PiCamera, PiCameraMMALError


class CameraPi:
    def __init__(self, record_filename):
        try:
            self.camera_pi = PiCamera()
            # Your existing configuration
            print("Camera initialized successfully")
        except PiCameraMMALError as e:
            print(f"Camera initialization error: {e}")
            # Additional diagnostic information
            print(f"MMAL Status: {e.status}")
            self.camera_pi = None
        self.camera_pi.awb_mode = 'shade'
        self.camera_pi.color_effects = (128, 128)
        self.camera_pi.resolution = (1280, 720)
        self.camera_pi.framerate = 30
        self.camera_pi.zoom = (0.25, 0.25, 0.5, 0.5)
        self.camera_pi.preview_fullscreen = False
        self.camera_pi.preview_window = (0, 0, 512, 600)
        self.video_filename = record_filename
        self.camera_on = False
        self.recording = False  # Added flag for recording

    def on(self, record_video=False):
        self.camera_pi.start_preview()
        self.camera_on = True

        if record_video:
            self.start_recording()

    def off(self):
        if self.recording:
            self.stop_recording()

        self.camera_pi.stop_preview()
        self.camera_on = False

    def shutdown(self):
        if self.camera_on:
            self.off()
        self.camera_pi.close()

    def start_recording(self):
        self.camera_pi.start_recording(self.video_filename)
        self.recording = True

    def stop_recording(self):
        self.camera_pi.stop_recording()
        self.recording = False