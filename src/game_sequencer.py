import cv2
from cv2 import *
import nxbt
import time
import copy
from image_manager import ImageManager
import logging
from datetime import datetime, timedelta


class GameSequencer:
    def __init__(self):
        self.appeared_image = None
        self.game_loaded_img = None
        self.screen_white_img = None
        self.shiny_found = False
        # set up ImageManager
        self.image_manager = ImageManager()
        logging.info("Initialize nxbt")
        # Start the NXBT service
        self.nx = nxbt.Nxbt()
        # create controller and connect to nintendo switch
        self.controller_index = self.nx.create_controller(
            nxbt.PRO_CONTROLLER,
            reconnect_address=self.nx.get_switch_addresses())
        logging.info("Successfully created a controller")
        self.nx.wait_for_connection(self.controller_index)
        logging.info("Connected")

        # just press b two times to activate controller
        self.nx.press_buttons(self.controller_index, [nxbt.Buttons.B])
        self.nx.press_buttons(self.controller_index, [nxbt.Buttons.B])

    def enter_game(self):
        logging.info('entering game')
        self.nx.press_buttons(self.controller_index, [nxbt.Buttons.A])
        time.sleep(1)
        logging.info('confirming user')
        self.nx.press_buttons(self.controller_index, [nxbt.Buttons.A])
        # wait for game to boot up
        time.sleep(26)
        logging.info('skipping intro')
        self.nx.press_buttons(self.controller_index, [nxbt.Buttons.A])
        time.sleep(2)
        # title screen
        logging.info('wait for title screen')
        while self.image_manager.check_pixel_in_image(360, 300, 0, 0, 0):
            pass
        time.sleep(1)
        logging.info('entering title screen')
        self.nx.press_buttons(self.controller_index, [nxbt.Buttons.A])
        logging.info('wait for screen to get black')
        while not self.image_manager.check_pixel_in_image(360, 300, 0, 0, 0):
            pass

        # wait for the game to load
        logging.info('wait for game to load')
        while self.image_manager.check_pixel_in_image(55, 400, 0, 0, 0):
            pass
        logging.info('game has loaded')
        time.sleep(2.5)

    def trigger_battle(self):
        # trigger battle scene
        logging.info('spamming A until battle starts')

        # press 'A' until the msg box appears
        while not self.image_manager.check_pixel_in_image(240, 400, 255, 255, 255):
            # click pokemon
            self.nx.press_buttons(self.controller_index, [nxbt.Buttons.A])
            time.sleep(1)

        logging.info('Clicked battle start')
        self.game_loaded_img = copy.deepcopy(self.image_manager.get_recent_image())

        # confirm msg box
        self.nx.press_buttons(self.controller_index, [nxbt.Buttons.A])
        time.sleep(2)

        # wait until the screen goes all white
        logging.info('wait until screen is all white')
        timepoint_start = datetime.utcnow()
        while not self.image_manager.check_pixel_in_image(360, 240, 255, 255, 255):
            # check for timeout
            if (datetime.utcnow() - timepoint_start).seconds > 20:
                # assume that the game had the error message
                # dump error msg
                imwrite(f'./error_msg_dbg.jpg', self.image_manager.get_recent_image())
                return False

        self.screen_white_img = copy.deepcopy(self.image_manager.get_recent_image())
        return True

    def wait_and_check_shiny_battle(self, iteration: int):
        # wait until the battle is started
        # logging.info('wait until white fades away')
        # while self.image_manager.check_pixel_in_image(10, 400, 255, 255, 255, 10):
        #    pass

        # wait until the text box "xyz appeared" is on the screen
        logging.info('wait until pokemon appears')
        while not self.image_manager.check_pixel_in_image(55, 400, 255, 255,
                                                          255) or self.image_manager.check_pixel_in_recent_image(
                10, 400, 255, 255, 255, 10):
            pass

        self.appeared_image = copy.deepcopy(self.image_manager.get_recent_image())
        logging.info('pokemon appeared!')

        # wait relative time
        timepoint_when_image = self.image_manager.get_recent_image_time()
        timepoint_check = (timepoint_when_image + timedelta(seconds=3.3))
        time.sleep((timepoint_check - timepoint_when_image).seconds)

        # take screenshot
        logging.info('taking image')
        img = self.image_manager.take_screenshot()
        imwrite(f'./encounters/encounter_giratina_{iteration}.jpg', img)
        # check for shiny
        rgb = img[440, 370]
        logging.info(f'rgb: {rgb}')
        self.shiny_found = rgb[0] != 255 or rgb[1] != 255 or rgb[2] != 255

        # if shiny found store the images
        if True:
            imwrite(f'./game_loaded_dbg.jpg', self.game_loaded_img)
            imwrite(f'./screen_white_dbg_dbg.jpg', self.screen_white_img)
            imwrite(f'./appeared_dbg.jpg', self.appeared_image)

    def return_to_homescreen_and_exit_game(self):
        while not self.image_manager.check_pixel_in_image(370, 40, 42, 42, 42):
            logging.info('wait until home screen is seen')
            self.nx.press_buttons(self.controller_index, [nxbt.Buttons.HOME])
            time.sleep(1.5)

        logging.info('on homescreen')

        # close game
        while not self.image_manager.check_pixel_in_image(370, 40, 29, 22, 9):
            logging.info('press X to enter game close dialog')
            self.nx.press_buttons(self.controller_index, [nxbt.Buttons.X])
            time.sleep(1.5)
        logging.info('game close dialog was reached')

        while not self.image_manager.check_pixel_in_image(370, 40, 42, 42, 42):
            logging.info('press A to close game')
            self.nx.press_buttons(self.controller_index, [nxbt.Buttons.A])
            time.sleep(1.5)
        logging.info('game was closed')

    def get_battle_img(self) -> str:
        return cv2.imencode('.jpg', self.appeared_image)[1].tobytes()

    def is_shiny(self) -> bool:
        return self.shiny_found

    def disconnect_controller(self):
        # close connection
        self.nx.remove_controller(self.controller_index)
        logging.info('connection closed')

    def re_init(self):
        logging.info('begin re initialize')
        self.image_manager.re_initialize_camera()
        self.nx.remove_controller(self.controller_index)
        time.sleep(1)
        # create controller and connect to nintendo switch
        self.controller_index = self.nx.create_controller(
            nxbt.PRO_CONTROLLER,
            reconnect_address=self.nx.get_switch_addresses())
        logging.info("Successfully created a controller")
        self.nx.wait_for_connection(self.controller_index)
        logging.info("Connected")

        # just press b two times to activate controller
        self.nx.press_buttons(self.controller_index, [nxbt.Buttons.B])
        self.nx.press_buttons(self.controller_index, [nxbt.Buttons.B])
        logging.info('re initialize finished')
