# does face tracking on video frames

import threading 
import numpy as np
import time
from mtcnn.mtcnn import MTCNN

class ftracker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
        self.detector = MTCNN(scale_factor=0.5, steps_threshold=[0.8,0.9,0.9])

        self.curr_frame = None
        self.faces = list()

        self.is_idle = threading.Event()
        self.is_idle.set()
        self.daemon = True
        

    def run(self):
        self.is_idle.clear()

        faces = self.detector.detect_faces(self.curr_frame)
        
        self.faces = list()
        for face in faces:
            x1, y1, width, height = face['box']
            x2, y2 = x1 + width, y1 + height
            
            self.faces.append([x1, y1, x2, y2])
        
        time.sleep(1)

        self.is_idle.set()



