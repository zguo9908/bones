import cv2
import threading

class CameraViewer:
    def __init__(self, camera_index=0, record_filename='output_video.avi'):
        self.cap = cv2.VideoCapture(camera_index)
        self.cam_on = False
        self.record_video = False  # Added flag for recording

        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Disable auto exposure
        self.cap.set(cv2.CAP_PROP_EXPOSURE, 0.5)  # Set exposure value (0.5 is just an example)
        self.cap.set(cv2.CAP_PROP_AUTO_WB, 0.25)  # Disable auto white balance
        self.cap.set(cv2.CAP_PROP_WB_TEMPERATURE, 5000)  # Set white balance temperature (5000K is just an example)

        self.record_filename = record_filename
        self.video_writer = None

    def on(self, record_video=False):  # Modified to accept a flag for recording
        self.cam_on = True
        self.record_video = record_video  # Set the recording flag

        self.camera_thread = threading.Thread(target=self._display_camera_feed)
        self.camera_thread.start()

    def off(self):
        self.cam_on = False
        self.camera_thread.join()  # Wait for the camera thread to finish

        if self.video_writer:
            self.video_writer.release()

        self.cap.release()
        cv2.destroyAllWindows()

    def shutdown(self):
        self.off()
        self.cam_on = False

    def _display_camera_feed(self):
        # Define the codec and create a VideoWriter object if recording is enabled
        if self.record_video:
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # You can change the codec as needed
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.video_writer = cv2.VideoWriter(self.record_filename, fourcc, fps, (width, height))

        while self.cam_on:
            ret, frame = self.cap.read()

            if ret:
                cv2.imshow('Camera Feed', frame)

                if self.record_video:
                    self.video_writer.write(frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

if __name__ == "__main__":
    # Create an instance of CameraViewer with the default camera index (0)
    viewer = CameraViewer(record_filename='output_video.avi')

    try:
        # Start the camera viewer without recording
        viewer.on(record_video=False)
        # Perform other tasks...

        # Start the camera viewer with recording
        viewer.on(record_video=True)
        # Perform other tasks...

    except KeyboardInterrupt:
        pass
    finally:
        # Stop the viewer and release resources when done
        viewer.off()