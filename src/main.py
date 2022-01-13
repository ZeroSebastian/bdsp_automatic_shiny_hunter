# -*- coding: utf-8 -*-
import time
import telebot
import logging
import json
import argparse
from shiny_hunter import ShinyHunter

# define parser
parser = argparse.ArgumentParser(description='Shiny hunting bot for Pokemon BDSP.')
parser.add_argument('command', default=False, choices=[
                        'hunt_standard_overworld', 'hunt_starter'
                    ],
                    help="""Specifies the shiny hunting command to run:
                    hunt_standard_overworld - Hunts a standard overworld Pokemon e.g.
                    Giratina. Just save right before the Pokemon and quit the game 
                    before you start with this mode.\n\n\n\n
                    hunt_starter - not implemented yet""")
args = parser.parse_args()

settings_file = 'settings.json'

if __name__ == '__main__':
    # set up logger
    logging.basicConfig(format='%(asctime)s %(message)s')
    logging.getLogger().setLevel(logging.INFO)
    shiny_hunter = None

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

        shiny_hunter = ShinyHunter(bot, telegram_user_id)
        # hunt depending on command line input
        if args.command == 'hunt_standard_overworld':
            shiny_hunter.hunt_standard_overworld_pokemon(cnt)
        elif args.command == 'hunt_starter':
            # TODO: shiny hunt the starter
            logging.warning('This feature is not implemented yet')
        else:
            print('invalid arguments')

    except KeyboardInterrupt:
        logging.info('Program will be closed')

    except BaseException as error:
        logging.error('An exception occurred: {}'.format(error))

    # tear down shiny hunter if it was initialized
    if shiny_hunter is not None:
        shiny_hunter.teardown()
