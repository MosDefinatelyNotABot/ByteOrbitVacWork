# just displays camera stream and periodically extracts frames as nd array
# crop to face for each frame and send nd array to server

# client side 
import numpy as np
import time
import cv2 
from mtcnn.mtcnn import MTCNN

vid = cv2.VideoCapture(0)
detector = MTCNN(scale_factor=0.1, steps_threshold=[0.8, 0.9, 0.9])

frame_counter = 0

prev_frame_time = 0
new_frame_time = 0

x1, y1, x2, y2 = 0,0,0,0

while(True):
    # infinite loop

    # init frame matrix
    frame = np.zeros((1080, 1920, 3), dtype="uint8")
    _, frame = vid.read(frame)        # read frame from video stream    
    
    # frame = cv2.resize(frame, (int(frame.shape[1]*resize), int(frame.shape[0]*resize)))

    if frame_counter % 6 == 0:

        faces = detector.detect_faces(frame)

        for face in faces:
            x1, y1, width, height = face['box']
            x2, y2 = x1 + width, y1 + height

    
    new_frame_time = time.time()
    fps = 1/(new_frame_time-prev_frame_time)
    prev_frame_time = new_frame_time
    fps = str(int(fps))

    cv2.putText(frame, f"{fps} frames/sec", (5,15), fontFace=1, fontScale=1, color=(0,255,0))
    cv2.rectangle(frame, (x1,y1), (x2, y2), (255, 0, 0), 2)
    cv2.imshow('Fverify', frame)   # display frame

    

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    frame_counter += 1

vid.release()

cv2.destroyAllWindows()