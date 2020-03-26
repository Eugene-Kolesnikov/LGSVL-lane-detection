from base_controller import BaseController
import cv2
import numpy as np
from video_log import VideoLog

class LaneDetector(BaseController):
    def __init__(self, log):
        self.OLD_LINES = []
        self.video = VideoLog("Lane Detector", "lanes.avi", log, visualize=True)
        super().__init__(log)
    
    def execute(self, sensors, old_controls):
        self.process_frame(sensors.get("Main Camera"))
        self.k += 1
        return {
            "throttle": 1.0 + (self.k * 0.01),
            "braking": 0.0,
            "steering": 0.0
        }

    def canny(self, image):
        # image = my_image_only_yellow_white_curve2(image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        canny = cv2.Canny(blur, 50, 150)
        return canny


    def region_of_interest(self, img, vertices):
        mask = np.zeros_like(img)
        if len(img.shape) > 2:
            channel_count = img.shape[2]
        else:
            channel_count = 1
        match_mask_color = (255,) * channel_count
        cv2.fillPoly(mask, vertices, match_mask_color)
        masked_image = cv2.bitwise_and(img, mask)
        return masked_image


    def crop(self, image):
        height, width = image.shape[0], image.shape[1]

        roi_vertices = [
            (0, height-170),
            # (2 * width // 5, height // 2),
            # (3 * width // 5, height // 2),
            (width // 2, height // 1.8),
            (width, height-170)
        ]

        cropped_image = self.region_of_interest(image,
                                        np.array([roi_vertices], np.int32))

        return cropped_image


    def display_lines(self, image, lines):
        line_image = np.zeros_like(image)
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line.reshape(4)
                try:
                    cv2.line(line_image, (x1, y1), (x2, y2), (0, 0, 255), 10)
                except Exception:
                    print(x1, y1, x2, y2)
        return line_image


    def conv(self, image):
        kernel = np.array([[1, 1, 1],
                           [1, 1, 1],
                           [1, 1, 1]])
        filtered = cv2.filter2D(src=image, kernel=kernel, ddepth=-1)
        return filtered


    def make_coordinates(self, image, line_parameters):
        slope, intercept = line_parameters
        y1 = image.shape[0]
        y2 = int(y1 * 3 / 5)
        x1 = int((y1 - intercept) / slope)
        x2 = int((y2 - intercept) / slope)
        return np.array([x1, y1, x2, y2])

    # Update for any number of lines
    def average_slope_intercept(self, image, lines):
        left_fit = []
        right_fit = []
        for line in lines:
            x1, y1, x2, y2 = line.reshape(4)
            parameters = np.polyfit((x1, x2), (y1, y2), 1)
            slope, intercept = parameters
            if slope < 0:
                left_fit.append((slope, intercept))
            else:
                right_fit.append((slope, intercept))
        left_fit_average = np.average(left_fit, axis=0)
        right_fit_average = np.average(right_fit, axis=0)
        left_line = self.make_coordinates(image, left_fit_average)
        right_line = self.make_coordinates(image, right_fit_average)
        return np.array([left_line, right_line])
    
    def process_frame(self, image):
        lane_image = np.copy(image)
        self.log.debug("Copied the image")
        canny_image = self.canny(lane_image)
        self.log.debug("Performed canny detection")
        cropped = self.crop(canny_image)
        self.log.debug("Cropped the image")
        # cropped = conv(cropped)
        lines = cv2.HoughLinesP(cropped, 2, np.pi/180, 100, np.array([]),
                                minLineLength=40, maxLineGap=5)
        self.log.debug("Computed lines")
        try:
            averaged_lines = self.average_slope_intercept(lane_image, lines)
            self.OLD_LINES = averaged_lines
        except Exception:
            averaged_lines = self.OLD_LINES
        averaged_lines = lines
        self.log.debug("Averaged the lines")
        line_image = self.display_lines(lane_image, averaged_lines)
        self.log.debug("Create a line image")
        # cropped = cv2.cvtColor(cropped, cv2.COLOR_GRAY2BGR)
        combo_image = cv2.addWeighted(lane_image, 0.8, line_image, 1, 1)
        self.log.debug("Combined the original image and the line image")

        self.video.write(combo_image)