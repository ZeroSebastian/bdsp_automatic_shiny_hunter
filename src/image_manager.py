
import cv2
from cv2 import *
import logging
from datetime import datetime, timedelta


class ImageManager:
    def __init__(self):
        # initialize the camera
        logging.info('initialize camera')
        self.cam = VideoCapture(0)  # 0 -> index of camera
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.recent_img = None
        self.time_when_recent_image = None

    def take_screenshot(self):
        self.cam.grab()
        # read until s is true
        s = False
        while not s:
            # update time
            self.time_when_recent_image = datetime.utcnow()
            s, self.recent_img = self.cam.read()
        return self.recent_img

    def get_recent_image(self):
        return self.recent_img

    def get_recent_image_time(self):
        return self.time_when_recent_image

    def check_pixel_in_recent_image(self, pos_x: int, pos_y: int, b: int, g: int, r: int, allowed_offset: int = 0) -> bool:
        upper_bound_b = b + allowed_offset
        if upper_bound_b > 255:
            upper_bound_b = 255
        lower_bound_b = b - allowed_offset
        if lower_bound_b < 0:
            lower_bound_b = 0

        upper_bound_g = g + allowed_offset
        if upper_bound_g > 255:
            upper_bound_g = 255
        lower_bound_g = g - allowed_offset
        if lower_bound_g < 0:
            lower_bound_g = 0

        upper_bound_r = r + allowed_offset
        if upper_bound_r > 255:
            upper_bound_r = 255
        lower_bound_r = r - allowed_offset
        if lower_bound_r < 0:
            lower_bound_r = 0
        bgr = self.recent_img[pos_y, pos_x]
        return (upper_bound_b >= bgr[0] >= lower_bound_b) and (upper_bound_g >= bgr[1] >= lower_bound_g) and (
                    upper_bound_r >= bgr[2] >= lower_bound_r)

        #return bgr[0] == b and bgr[1] == g and bgr[2] == r

    def check_pixel_in_image(self, pos_x: int, pos_y: int, b: int, g: int, r: int, allowed_offset: int = 0) -> bool:
        self.take_screenshot()
        return self.check_pixel_in_recent_image(pos_x, pos_y, b, g, r, allowed_offset)

    def re_initialize_camera(self):
        self.cam.open(0)