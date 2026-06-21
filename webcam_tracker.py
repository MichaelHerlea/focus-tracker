import cv2

class WebcamTracker():
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.running = False

    def start(self):
        self.running = True
        self.get_frame()

    def stop(self):
        self.running = False

    def run(self):
        while self.running:
            self.get_frame()

    def get_frame(self):
        ret, frame = self.cap.read()
        if ret:
            return frame