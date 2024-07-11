# python class that controls the camera window

import cv2
import threading
import numpy as np
import time
import datetime
import ftracking

class camera_window():
    def __init__(self) -> None:
        self.video_stream = cv2.VideoCapture(0)
        self.is_on = threading.Event()

        # for fps counting
        self.new_frame_time = time.time()
        self.prev_frame_time = self.new_frame_time

        # for face tracking
        self.tracker = ftracking.ftracker()
        self.frame_count = 0

    def getfps(self) -> int:
        # calculates fps
        self.new_frame_time = time.time()
        fps = 1/(self.new_frame_time-self.prev_frame_time)
        self.prev_frame_time = self.new_frame_time

        return int(fps)

    def turn_camera_on(self):
        # sets video loop running
        self.is_on.set()
        self.video_loop()

    def onClose(self):
        # closes camera video stream
        self.video_stream.release()
        cv2.destroyAllWindows()
        self.is_on.clear()

    def draw_BBoxes(self, frame: np.ndarray):

        for i, face in enumerate(self.tracker.faces):
            # draw a box
            cv2.rectangle(frame, (face[0], face[1]), (face[2], face[3]), (255,0,0), 1,1,0)
            
            # add tag to face
            cv2.putText(frame, f"person {i}" , (face[0]+5, face[1]-15), 1,1,(255,0 ,0))

    def video_loop(self):
        while self.is_on.is_set():
            # while the camera is on

            _, frame = self.video_stream.read()

            fps = self.getfps()
            curr_time = datetime.datetime.now()

            if self.tracker.is_idle.is_set() and self.frame_count%30 == 0:
                # the tracker thread is idle
                self.tracker.curr_frame = frame
                self.tracker.run()

            self.draw_BBoxes(frame)

            cv2.putText(frame, f"{curr_time.strftime("%Y-%m-%d %H:%M:%S")}", (5,15), fontFace=1, fontScale=1, color=(0,255,0))
            cv2.putText(frame, f"{fps} frames/sec", (5,30), fontFace=1, fontScale=1, color=(0,255,0))

            cv2.imshow("camera", frame)

            self.frame_count += 1

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.onClose
                break






