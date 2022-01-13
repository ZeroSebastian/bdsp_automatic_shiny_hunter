# -*- coding: utf-8 -*-
import time
import telebot
import logging
from game_sequencer import GameSequencer


class ShinyHunter:
    def __init__(self, telegram_bot, telegram_user_id):
        """
        Constructor - intitializes game_sequencer and assign default values
        """
        self.__game_sequencer = GameSequencer()
        self.__active_hunting = True
        self.__telegram_bot = telegram_bot
        self.__telegram_user_id = telegram_user_id
        self.__send_encounter_images = True

    def teardown(self):
        """
        closes the bluetooth connection gracefully
        """
        self.__game_sequencer.disconnect_controller()
        # wait some time so that process can shut down properly
        time.sleep(5)

    def hunt_standard_overworld_pokemon(self, start_reset_count):
        """
        shiny hunts a standard overworld pokemon eg. Giratina by soft resetting and simply
            starting a battle.
        just save in front of the pokemon
        :param start_reset_count: initial iteration count
        :return: True if shiny was found, false if function exited due to internal
            active flag
        """
        cnt = start_reset_count
        while self.__active_hunting:
            logging.info(f'iteration: {cnt}')
            # wait until the battle is started
            error_code = GameSequencer.ErrorCode.GAME_ERROR
            while error_code != GameSequencer.ErrorCode.SUCCESS:
                error_code = self.__game_sequencer.trigger_battle()
                # check for error
                if error_code == GameSequencer.ErrorCode.GAME_FROZEN:
                    logging.warning('Game frozen assumed')
                    self.__telegram_bot.send_message(self.__telegram_user_id, f'Game frozen assumed, trying to close game and start again!')
                    self.__game_sequencer.return_to_homescreen_and_exit_game()
                elif error_code == GameSequencer.ErrorCode.GAME_ERROR:
                    logging.warning('Game Error assumed')
                    self.__telegram_bot.send_message(self.__telegram_user_id, f'Game error assumed, starting over!')

            self.__game_sequencer.wait_and_check_shiny_battle(cnt)

            # send the encounter image if so defined
            if self.__send_encounter_images:
                logging.info('sending image')
                try:
                    self.__telegram_bot.send_photo(self.__telegram_user_id, photo=self.__game_sequencer.get_battle_img(),
                                                   caption=f'Iteration: {cnt}', disable_notification=True)
                except BaseException as error:
                    logging.error('An exception occurred: {}'.format(error))

            # check if the pokemon is shiny
            if self.__game_sequencer.is_shiny():
                logging.info('shiny found!')
                self.__telegram_bot.send_message(self.__telegram_user_id, f'Shiny found!')
                return True

            # exit the game
            self.__game_sequencer.return_to_homescreen_and_exit_game()
            cnt += 1
        # if active is disabled return here
        return False

    def set_active_hunting(self, active):
        """
        set internal active hunting flag
        :param active: new value for active_hunting
        """
        self.__active_hunting = active
