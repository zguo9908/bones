import cv2
import libcamera
import threading

class CameraViewer:
    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        self.cam_on = False

        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Disable auto exposure
        self.cap.set(cv2.CAP_PROP_EXPOSURE, 0.5)  # Set exposure value (0.5 is just an example)
        self.cap.set(cv2.CAP_PROP_AUTO_WB, 0.25)  # Disable auto white balance
        self.cap.set(cv2.CAP_PROP_WB_TEMPERATURE, 5000)  # Set white balance temperature (5000K is just an example)
    def on(self):
        self.cam_on = True
        self.camera_thread = threading.Thread(target=self._display_camera_feed)
        self.camera_thread.start()

    def off(self):
        self.cam_on = False
        self.camera_thread.join()  # Wait for the camera thread to finish
        self.cap.release()
        cv2.destroyAllWindows()

    def shutdown(self):
        self.off()
        self.cam_on = False

    def _display_camera_feed(self):
        while self.cam_on:
            ret, frame = self.cap.read()
            cv2.imshow('Camera Feed', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break


if __name__ == "__main__":
    # Create an instance of CameraViewer with the default camera index (0)
    viewer = CameraViewer()

    try:
        # Start the camera viewer
        viewer.start_viewer()
    except KeyboardInterrupt:
        pass
    finally:
        # Stop the viewer and release resources when done
        viewer.stop_viewer()