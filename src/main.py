# -*- coding: utf-8 -*-
import time
import telebot
import logging
import json
from game_sequencer import GameSequencer

settings_file = 'settings.json'

stop = False

if __name__ == '__main__':
    # set up logger
    logging.basicConfig(format='%(asctime)s %(message)s')
    logging.getLogger().setLevel(logging.INFO)

    # repeat until keyboard interrupt ctrl+c is given
    try:
        # load iteration from settings.json
        logging.info('Loading settings')
        telegram_token_str = str()
        telegram_user_id = int()
        cnt = 0
        with open(settings_file) as json_file:
            data = json.load(json_file)
            cnt = data['iteration']
            telegram_token_str = data['telegram_token']
            telegram_user_id = data['telegram_user_id']
            logging.info(f'starting with iteration {cnt}')

        # create telegram bot
        logging.info('initialize telegram bot')
        bot = telebot.TeleBot(token=telegram_token_str)

        game_sequencer = GameSequencer()

        while not stop:
            logging.info(f'iteration: {cnt}')

            # game_sequencer.enter_game()
            while not game_sequencer.trigger_battle():
                # error detected
                logging.info('Game Error assumed')
                bot.send_message(telegram_user_id, f'Game error assumed, starting over!')

            game_sequencer.wait_and_check_shiny_battle(cnt)

            # send with bot
            logging.info('sending image')
            bot.send_photo(telegram_user_id, photo=game_sequencer.get_battle_img(), caption=f'Iteration: {cnt}',
                           disable_notification=True)

            # check for shiny
            if game_sequencer.is_shiny():
                logging.info('shiny found!')
                bot.send_message(telegram_user_id, f'Shiny found!')
                time.sleep(604800)

            game_sequencer.return_to_homescreen_and_exit_game()
            cnt += 1

    except KeyboardInterrupt:
        logging.info('Program will be closed')

    game_sequencer.disconnect_controller()
    # wait some time so that process can shut down properly
    time.sleep(5)
