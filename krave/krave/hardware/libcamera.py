import cv2
import threading
import queue
import time
import os


class CameraViewer:
    def __init__(self, output_filename='output_video.avi', frame_width=320, frame_height=240, fps=15):
        # Camera setup
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise ValueError("Failed to open the camera.")

        # Print initial camera properties
        print(f"Default FPS: {self.cap.get(cv2.CAP_PROP_FPS)}")
        print(f"Source Code: {self.cap.get(cv2.CAP_PROP_FOURCC)}")
        print(f"Brightness: {self.cap.get(cv2.CAP_PROP_BRIGHTNESS)}")
        print(f"Contrast: {self.cap.get(cv2.CAP_PROP_CONTRAST)}")
        print(f"Saturation: {self.cap.get(cv2.CAP_PROP_SATURATION)}")
        print(f"Hue: {self.cap.get(cv2.CAP_PROP_HUE)}")
        print(f"Gain: {self.cap.get(cv2.CAP_PROP_GAIN)}")
        print(f"Exposure: {self.cap.get(cv2.CAP_PROP_EXPOSURE)}")

        # Set camera properties
        print("\nAttempting to set camera properties...")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)

        # Output file setup
        self.output_filename = output_filename
        self.record_video = False
        self.video_writer = None

        # Thread management
        self.cam_on = False
        self.frame_queue = queue.Queue(maxsize=10)

    def on(self, record_video=False):
        """Starts camera feed display and recording."""
        if self.record_video:
            print("Recording is already running.")
            return

        print("Starting camera feed and recording...")
        self.record_video = record_video
        self.cam_on = True

        if record_video:
            # Use MJPG codec instead of H264
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)

            print(f"Video writer properties:")
            print(f"Width: {frame_width}, Height: {frame_height}, FPS: {fps}")

            self.video_writer = cv2.VideoWriter(
                self.output_filename, fourcc, fps, (frame_width, frame_height)
            )

        # Start threads
        self.reader_thread = threading.Thread(target=self._frame_reader)
        self.processor_thread = threading.Thread(target=self._frame_processor)

        self.reader_thread.start()
        self.processor_thread.start()

    def _frame_reader(self):
        """Reads frames from the camera and puts them in a queue."""
        frame_count = 0
        while self.cam_on:
            ret, frame = self.cap.read()
            if ret:
                frame_count += 1
                if frame_count % 30 == 0:  # Print every 30 frames
                    print(f"Successfully read frame {frame_count}")
                if not self.frame_queue.full():
                    self.frame_queue.put(frame)
            else:
                print(f"Warning: Failed to read frame {frame_count + 1}")
                time.sleep(0.1)  # Wait before retrying
            time.sleep(0.01)

    def _frame_processor(self):
        """Processes frames: displays and records."""
        cv2.namedWindow('Camera Feed', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Camera Feed', 640, 480)

        frame_count = 0
        while self.cam_on:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                frame_count += 1

                # Add frame counter overlay
                cv2.putText(frame, f"Frame: {frame_count}",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 255, 0), 2)

                cv2.imshow('Camera Feed', frame)

                if self.record_video and self.video_writer:
                    self.video_writer.write(frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.off()
            else:
                time.sleep(0.01)

    def off(self):
        """Stops camera feed and recording."""
        print("Stopping camera feed and recording...")
        self.cam_on = False
        self.record_video = False

        # Wait for threads to finish
        if hasattr(self, 'reader_thread') and self.reader_thread.is_alive():
            self.reader_thread.join()
        if hasattr(self, 'processor_thread') and self.processor_thread.is_alive():
            self.processor_thread.join()

        # Release resources
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        self.cap.release()
        cv2.destroyAllWindows()
        print("Camera feed and recording stopped successfully.")

    def shutdown(self):
        """Safely shuts down the camera and threads."""
        print("Shutting down the camera viewer...")
        self.off()
        if self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        print("Shutdown complete.")

# import cv2
# import threading
#
# class CameraViewer:
#     def __init__(self, camera_index=0, record_filename='output_video.avi'):
#         self.cap = cv2.VideoCapture(camera_index)
#         if not self.cap.isOpened():
#             raise ValueError(f"Failed to open camera at index {camera_index}")
#
#         self.cam_on = False
#         self.record_video = False
#         self.record_filename = record_filename
#         self.video_writer = None
#
#         # Camera settings
#         self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Disable auto exposure
#         self.cap.set(cv2.CAP_PROP_EXPOSURE, 0.5)  # Set exposure value
#         self.cap.set(cv2.CAP_PROP_AUTO_WB, 0.25)  # Disable auto white balance
#         self.cap.set(cv2.CAP_PROP_WB_TEMPERATURE, 5000)  # Set white balance
#
#     def on(self, record_video=False):
#         self.cam_on = True
#         self.record_video = record_video
#
#         if self.record_video:
#             # Define the codec and create a VideoWriter object
#             fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec
#             fps = self.cap.get(cv2.CAP_PROP_FPS) or 30  # Default to 30 if FPS is 0
#             width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#             height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
#             self.video_writer = cv2.VideoWriter(self.record_filename, fourcc, fps, (width, height))
#
#         # Start the camera thread
#         self.camera_thread = threading.Thread(target=self._display_camera_feed, daemon=True)
#         self.camera_thread.start()
#
#     def off(self):
#         self.cam_on = False
#         if self.camera_thread:
#             self.camera_thread.join()
#
#         if self.video_writer:
#             self.video_writer.release()
#
#         self.cap.release()
#         cv2.destroyAllWindows()
#
#     def shutdown(self):
#         self.off()
#
#     def _display_camera_feed(self):
#         while self.cam_on:
#             ret, frame = self.cap.read()
#             if not ret:
#                 print("Failed to capture frame. Exiting...")
#                 break
#
#             cv2.imshow('Camera Feed', frame)
#
#             if self.record_video and self.video_writer:
#                 self.video_writer.write(frame)
#
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break
#
#         self.off()
#
#
# # import cv2
# # import threading
# #
# # class CameraViewer:
# #     def __init__(self, camera_index=0, record_filename='output_video.avi'):
# #         self.cap = cv2.VideoCapture(camera_index)
# #         self.cam_on = False
# #         self.record_video = False  # Added flag for recording
# #
# #         self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Disable auto exposure
# #         self.cap.set(cv2.CAP_PROP_EXPOSURE, 0.5)  # Set exposure value (0.5 is just an example)
# #         self.cap.set(cv2.CAP_PROP_AUTO_WB, 0.25)  # Disable auto white balance
# #         self.cap.set(cv2.CAP_PROP_WB_TEMPERATURE, 5000)  # Set white balance temperature (5000K is just an example)
# #
# #         self.record_filename = record_filename
# #         self.video_writer = None
# #
# #     def on(self, record_video=False):  # Modified to accept a flag for recording
# #         self.cam_on = True
# #         self.record_video = record_video  # Set the recording flag
# #         self.camera_thread = threading.Thread(target=self._display_camera_feed)
# #         self.camera_thread.start()
# #
# #     def off(self):
# #         self.cam_on = False
# #         self.camera_thread.join()  # Wait for the camera thread to finish
# #
# #         if self.video_writer:
# #             self.video_writer.release()
# #
# #         self.cap.release()
# #         cv2.destroyAllWindows()
# #
# #     def shutdown(self):
# #         self.off()
# #         self.cam_on = False
# #
# #     def _display_camera_feed(self):
# #         # Define the codec and create a VideoWriter object if recording is enabled
# #         if self.record_video:
# #             fourcc = cv2.VideoWriter_fourcc(*'XVID')  # You can change the codec as needed
# #             fps = self.cap.get(cv2.CAP_PROP_FPS)
# #             width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
# #             height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
# #             self.video_writer = cv2.VideoWriter(self.record_filename, fourcc, fps, (width, height))
# #         while self.cam_on:
# #             ret, frame = self.cap.read()
# #             if ret:
# #                 cv2.imshow('Camera Feed', frame)
# #                 if self.record_video:
# #                     self.video_writer.write(frame)
# #             if cv2.waitKey(1) & 0xFF == ord('q'):
# #                 break
# #
# # if __name__ == "__main__":
# #     # Create an instance of CameraViewer with the default camera index (0)
# #     viewer = CameraViewer(record_filename='output_video.avi')
# #
# #     try:
# #         # Start the camera viewer without recording
# #         viewer.on(record_video=False)
# #         # Perform other tasks...
# #
# #         # Start the camera viewer with recording
# #         viewer.on(record_video=True)
# #         # Perform other tasks...
# #
# #     except KeyboardInterrupt:
# #         pass
# #     finally:
# #         # Stop the viewer and release resources when done
# #         viewer.off()