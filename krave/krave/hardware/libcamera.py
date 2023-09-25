import cv2
import libcamera
import threading

class CameraViewer:
    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        self.cam_on = False

    def on(self):
        self.cam_on = True
        while True:
            ret, frame = self.cap.read()
            cv2.imshow('Camera Feed', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def off(self):
        self.cam_on = False
        self.cap.release()
        cv2.destroyAllWindows()

    def shutdown(self):
        if self.cam_on:
            self.off()


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