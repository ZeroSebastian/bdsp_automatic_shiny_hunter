# -*- coding: utf-8 -*-
import copy
import threading
import time
import logging
import telebot
from game_sequencer import GameSequencer
from dataclasses import dataclass


class ShinyHunter:
    @dataclass
    class StatusUpdate:
        iteration: int
        image: str

    def __init__(self, telegram_token, telegram_user_id):
        """
        Constructor - intitializes game_sequencer and assign default values
        """
        self.__game_sequencer = GameSequencer()
        self.__telegram_user_id = telegram_user_id
        self.__send_encounter_images = False
        self.__polling_thread_stop = threading.Event()
        self.__battle_image_lock = threading.Lock()
        self.__stop_cmd_received = False
        self.__recent_status = None
        self.__iteration = 0
        logging.info('initialize telegram bot')
        self.__telegram_bot = telebot.TeleBot(token=telegram_token)
        logging.info('setting up polling thread')
        self.__polling_thread = threading.Thread(target=self.__telegram_polling_thread)
        self.__polling_thread.start()  # Start the execution

    def teardown(self):
        """
        closes the bluetooth connection gracefully
        """
        self.__game_sequencer.disconnect_controller()

        # also close telebot
        logging.info('shutting down telegram bot wrapper')
        self.__telegram_bot.send_message(self.__telegram_user_id, text='Shutting down, goodbye!')
        self.__polling_thread_stop.set()
        logging.info('waiting for thread to join')
        self.__polling_thread.join()
        logging.info('thread ended')

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
        self.__iteration = start_reset_count
        while not self.__stop_cmd_received:
            logging.info(f'iteration: {self.__iteration}')
            # wait until the battle is started
            error_code = GameSequencer.ErrorCode.GAME_ERROR
            while error_code != GameSequencer.ErrorCode.SUCCESS:
                error_code = self.__game_sequencer.trigger_battle()
                # check for error
                if error_code == GameSequencer.ErrorCode.GAME_FROZEN:
                    logging.warning('Game frozen assumed')
                    self.__telegram_bot.send_message(self.__telegram_user_id,
                                                     text='Game frozen assumed, trying to close game and start again!')

                    self.__game_sequencer.return_to_homescreen_and_exit_game()
                elif error_code == GameSequencer.ErrorCode.GAME_ERROR:
                    logging.warning('Game Error assumed')
                    self.__telegram_bot.send_message(self.__telegram_user_id, text='Game error assumed, starting over!')

            self.__game_sequencer.wait_and_check_shiny_battle(self.__iteration)
            # set the encounter image
            self.__battle_image_lock.acquire()
            self.__recent_status = ShinyHunter.StatusUpdate(self.__iteration,
                                                            copy.deepcopy(self.__game_sequencer.get_battle_img()))
            self.__battle_image_lock.release()

            # send the encounter image if so defined
            if self.__send_encounter_images:
                logging.info('sending image')
                self.__telegram_bot.send_photo(self.__telegram_user_id, photo=self.__game_sequencer.get_battle_img(),
                                               caption=f'Iteration: {self.__iteration}', )

            # check if the pokemon is shiny
            if self.__game_sequencer.is_shiny():
                logging.info('shiny found!')
                self.__telegram_bot.send_photo(self.__telegram_user_id, photo=self.__game_sequencer.get_battle_img(),
                                               caption='Shiny found!', )
                return True

            # exit the game
            self.__game_sequencer.return_to_homescreen_and_exit_game()
            self.__iteration += 1

        # if active is disabled return here
        return False

    def __telegram_polling_thread(self):
        logging.info('polling thread started')
        # send a message that the bot has started
        self.__telegram_bot.send_message(self.__telegram_user_id, 'ShinyHunter has started!')
        updates_offset = 0
        # poll and send messages if there are pending messages to be sent
        while not self.__polling_thread_stop.is_set():
            try:
                updates = self.__telegram_bot.get_updates(updates_offset + 1)

                # check if new message was sent
                for update in updates:
                    if update.update_id > updates_offset:
                        updates_offset = update.update_id

                    if update.message:
                        msg_txt = update.message.text
                        logging.info(f'received message {msg_txt}')

                        # check which message was sent
                        if msg_txt == '/status':
                            logging.info('send recent status update')
                            self.__battle_image_lock.acquire()
                            if self.__recent_status is not None:
                                self.__telegram_bot.send_photo(self.__telegram_user_id,
                                                               photo=self.__recent_status.image,
                                                               caption=f'Iteration: {self.__recent_status.iteration}')
                                self.__recent_status = None
                            else:
                                self.__telegram_bot.send_message(self.__telegram_user_id, text='Nothing new to send!')
                            self.__battle_image_lock.release()
                        elif msg_txt == '/enable_updates':
                            self.__telegram_bot.send_message(self.__telegram_user_id,
                                                             text='Update notifications are enabled!')
                            self.__send_encounter_images = True
                        elif msg_txt == '/disable_updates':
                            self.__telegram_bot.send_message(self.__telegram_user_id,
                                                             text='Update notifications are disabled!')
                            self.__send_encounter_images = False
                        elif msg_txt == '/stop':
                            self.__stop_cmd_received = True
                            self.__telegram_bot.send_message(self.__telegram_user_id,
                                                             text='Hunting will end after current iteration')
            # just handle network exception in a simple way that would lead to a crash otherwise
            except Exception as e:
                logging.error(f'Exception occurred in TelebotWrapper.run: {e}!')
