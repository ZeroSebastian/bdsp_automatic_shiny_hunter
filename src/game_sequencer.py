# -*- coding: utf-8 -*-
import cv2
from cv2 import *
import nxbt
import time
import copy
from image_manager import ImageManager, RGBSpecifier, ImageCheckingSpecifier
import logging
from datetime import datetime, timedelta
from enum import Enum


class GameSequencer:

    class ErrorCode(Enum):
        SUCCESS = 0
        GAME_FROZEN = 1
        GAME_ERROR = 2

    def __init__(self):
        """
        Constructor - intitializes ImageManager and sets up BT connection
        """
        self.__appeared_image = None
        self.__game_loaded_img = None
        self.__screen_white_img = None
        self.__shiny_found = False
        # set up ImageManager
        self.__image_manager = ImageManager()
        logging.info("Initialize nxbt")
        # Start the NXBT service
        self.__nx = nxbt.Nxbt()
        # create controller and connect to nintendo switch
        self.__controller_index = self.__nx.create_controller(
            nxbt.PRO_CONTROLLER,
            reconnect_address=self.__nx.get_switch_addresses())
        logging.info("Successfully created a controller")
        self.__nx.wait_for_connection(self.__controller_index)
        logging.info("Connected")

        # just press b two times to activate controller
        self.__nx.press_buttons(self.__controller_index, [nxbt.Buttons.B])
        self.__nx.press_buttons(self.__controller_index, [nxbt.Buttons.B])

    def trigger_battle(self):
        """
        presses button A until the pokemon is spoken to
        :return: ErrorCode
        """
        # trigger battle scene
        logging.info('spamming A until battle starts')

        # press 'A' until the msg box appears
        pokemon_spoken_to_text_box_checker = ImageCheckingSpecifier(240, 400, ImageManager.white_rgb, False)
        if not self.__execute_command_until_and([nxbt.Buttons.A], pokemon_spoken_to_text_box_checker, 1, 120):
            # assume that the game had the error message
            imwrite(f'./error_frozen_dbg.jpg', self.__image_manager.get_recent_image())
            return GameSequencer.ErrorCode.GAME_FROZEN

        logging.info('Clicked battle start')
        self.__game_loaded_img = copy.deepcopy(self.__image_manager.get_recent_image())

        # wait until the screen goes all white
        logging.info('wait until screen is all white')
        screen_white_checker = ImageCheckingSpecifier(360, 240, ImageManager.white_rgb, False)
        if not self.__execute_command_until_and([nxbt.Buttons.A], screen_white_checker, 1, 20):
            # assume that the game had the error message
            imwrite(f'./game_error_dbg.jpg', self.__image_manager.get_recent_image())
            return GameSequencer.ErrorCode.GAME_ERROR

        self.__screen_white_img = copy.deepcopy(self.__image_manager.get_recent_image())
        return GameSequencer.ErrorCode.SUCCESS

    def wait_and_check_shiny_battle(self, iteration: int):
        """
        waits for the pokemon to appear and checks if it is a shiny one
        :param iteration: current iteration the whole process is in
        """
        # wait until the text box "xyz appeared" is on the screen
        logging.info('wait until pokemon appears')
        pokemon_appeared_checker = (ImageCheckingSpecifier(55, 400, ImageManager.white_rgb, False),
                                    ImageCheckingSpecifier(10, 400, RGBSpecifier(255, 255, 255, 10), True))
        while self.__image_manager.check_pixel_in_image(pokemon_appeared_checker[0]) or\
                self.__image_manager.check_pixel_in_recent_image(pokemon_appeared_checker[1]):
            pass

        self.__appeared_image = copy.deepcopy(self.__image_manager.get_recent_image())
        logging.info('pokemon appeared!')

        # wait relative time
        timepoint_when_image = self.__image_manager.get_recent_image_time()
        timepoint_check = (timepoint_when_image + timedelta(seconds=3.1))
        time.sleep((timepoint_check - timepoint_when_image).seconds)

        # take screenshot
        logging.info('taking image')
        img = self.__image_manager.take_screenshot()
        imwrite(f'./encounters/encounter_{iteration}.jpg', img)
        # check for shiny
        battle_box_checker = ImageCheckingSpecifier(370, 440, ImageManager.white_rgb, False)
        rgb = img[440, 370]
        logging.info(f'rgb: {rgb}')
        self.__shiny_found = self.__image_manager.check_pixel_in_recent_image(battle_box_checker) or \
                             rgb[0] != 255 or rgb[1] != 255 or rgb[2] != 255

        # if shiny found store the images
        if self.__shiny_found:
            logging.info(f'recent img returns: {self.__image_manager.check_pixel_in_recent_image(battle_box_checker)}')
            imwrite(f'./game_loaded_dbg.jpg', self.__game_loaded_img)
            imwrite(f'./screen_white_dbg_dbg.jpg', self.__screen_white_img)
            imwrite(f'./appeared_dbg.jpg', self.__appeared_image)
            self.__nx.press_buttons(self.__controller_index, [nxbt.Buttons.CAPTURE], down=2.0)

    def return_to_homescreen_and_exit_game(self):
        """
        returns to home screen and closes game
        """
        logging.info('press HOME to leave game')
        homescreen_reached_checker = ImageCheckingSpecifier(370, 40, RGBSpecifier(42, 42, 42, 0), False)
        self.__execute_command_until_and([nxbt.Buttons.HOME], homescreen_reached_checker, 1.5, 0)

        # close game
        logging.info('press X to enter game close dialog')
        close_dialog_checker = ImageCheckingSpecifier(370, 40, RGBSpecifier(9, 22, 29, 0), False)
        self.__execute_command_until_and([nxbt.Buttons.X], close_dialog_checker, 1.5, 0)

        logging.info('press A to close game')
        self.__execute_command_until_and([nxbt.Buttons.A], homescreen_reached_checker, 1.5, 0)
        logging.info('game was closed')

    def get_battle_img(self) -> str:
        """
        get the image that was taken when the pokemon appeared
        :return: image when the pokemon appeared as bytes .jpg
        """
        return cv2.imencode('.jpg', self.__appeared_image)[1].tobytes()

    def is_shiny(self) -> bool:
        """
        Check if recent encounter was shiny
        :return: self.shiny_found
        """
        return self.__shiny_found

    def disconnect_controller(self):
        """
        Closes the Bluetooth connection
        """
        # close connection
        self.__nx.remove_controller(self.__controller_index)
        logging.info('connection closed')

    def __execute_command_until_and(self, button_cmd, check_condition: ImageCheckingSpecifier, retry_delay,
                                    timeout_sec: int):
        """
        execute a command until the specified condition is met or a timeout occured
        :param button_cmd: command that should be sent to nintendo switch
        :param check_condition: condition in image that should be checked
        :param retry_delay: delay between each controller inputs
        :param timeout_sec: if timeout seconds passes (has to be >0) a timeout is detected
        :return: True if condition was met, False if timeout occured
        """
        start = datetime.utcnow()
        while self.__image_manager.check_pixel_in_image(check_condition):
            # Check for timeout
            if (timeout_sec != 0) and ((datetime.utcnow() - start).seconds >= timeout_sec):
                # make screen record when a timeout happens
                self.__nx.press_buttons(self.__controller_index, [nxbt.Buttons.CAPTURE], down=2.0)
                time.sleep(5)
                # just for linebreak at end
                print('')
                logging.warning('timeout reached')
                return False
            print('.', end='')
            self.__nx.press_buttons(self.__controller_index, button_cmd)
            time.sleep(retry_delay)
        # just for linebreak at end
        print('')
        return True
