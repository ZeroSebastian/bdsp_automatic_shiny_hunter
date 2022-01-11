# -*- coding: utf-8 -*-
import cv2
from cv2 import *
import logging
from datetime import datetime
from dataclasses import dataclass


@dataclass
class RGBSpecifier:
    r: int = 0
    g: int = 0
    b: int = 0
    allowed_offset: int = 0


@dataclass
class ImageCheckingSpecifier:
    pixel_pos_x: int = 0
    pixel_pos_y: int = 0
    rgb: RGBSpecifier = RGBSpecifier()
    condition: bool = True


class ImageManager:
    white_rgb: RGBSpecifier = RGBSpecifier(255, 255, 255)
    black_rgb: RGBSpecifier = RGBSpecifier(0, 0, 0)

    def __init__(self):
        """
        initializes capture device
        """
        # initialize the camera
        logging.info('initialize camera')
        self.cam = VideoCapture(0)  # 0 -> index of camera
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.recent_img = None
        self.time_when_recent_image = None

    def take_screenshot(self):
        """
        make a screenshot of the current frame
        :return: the screenshot
        """
        self.cam.grab()
        # read until s is true
        s = False
        while not s:
            # update time
            self.time_when_recent_image = datetime.utcnow()
            s, self.recent_img = self.cam.read()
        return self.recent_img

    def get_recent_image(self):
        """
        request recent image taken by image manager
        :return: recent image
        """
        return self.recent_img

    def get_recent_image_time(self):
        """
        access timepoint when recent image was taken
        :return: timepoint of recent image
        """
        return self.time_when_recent_image

    def check_pixel_in_recent_image(self, spec: ImageCheckingSpecifier):
        """
        check if the recent image meets a condition
        :param spec: condition that should be met
        :return: True if condition is fulfilled, otherwise false
        """
        return self.__check_pixel_in_recent_image_internal(spec.pixel_pos_x, spec.pixel_pos_y, spec.rgb.b, spec.rgb.g,
                                                           spec.rgb.r, spec.rgb.allowed_offset) == spec.condition

    def check_pixel_in_image(self, spec: ImageCheckingSpecifier):
        """
        same as check_pixel_in_recent_image but a new image is taken
        :param spec: condition that should be met
        :return: True if condition is fulfilled, otherwise false
        """
        self.take_screenshot()
        return self.check_pixel_in_recent_image(spec)

    def __check_pixel_in_recent_image_internal(self, pos_x: int, pos_y: int, b: int, g: int, r: int,
                                               allowed_offset: int = 0) -> bool:
        """
        checks pixel in recently taken image
        :param pos_x: x pos in image
        :param pos_y: y pos in image
        :param b: b value of pixel
        :param g: g value of pixel
        :param r: r value of pixel
        :param allowed_offset: allowed offset from the expected rgb values
        :return: true if rgb of pixel matches or is in allowed range, otherwise false
        """
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
