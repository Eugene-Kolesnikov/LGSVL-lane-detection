import cv2

class VideoLog:
    def __init__(self, title, filename, log, visualize=False):
        self.title = title
        self.filename = filename
        self.log = log
        self.visualize = visualize
        self.handler = None
    
    def _init_handler(self, shape):
        self.log.debug("Initializing a video writer")
        self.handler = cv2.VideoWriter(self.filename, cv2.VideoWriter_fourcc(*'mp4v'),
            10, (shape[1], shape[0]))

    def write(self, image):
        if self.handler is None:
            self._init_handler(image.shape)
        self.log.debug("Writing the frame to the video file")
        self.handler.write(image)
        if self.visualize:
            self.log.debug("Visualizing the frame")
            cv2.imshow(self.title, image)
            cv2.waitKey(1)
    
    def close(self):
        self.handler.release()
        