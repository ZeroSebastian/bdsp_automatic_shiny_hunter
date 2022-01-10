import time
import telebot
import logging
import json
from game_sequencer import GameSequencer

token_str = 'TODO'
user_id = 696969 # TODO
settings_file = 'settings.json'

bot = telebot.TeleBot(token=token_str)
stop = False


@bot.message_handler(commands=['stop'])
def command_stop(message):
    bot.reply_to(message, "Bot is stopping now")
    global stop
    stop = True


if __name__ == '__main__':
    # set up logger
    logging.basicConfig(format='%(asctime)s %(message)s')
    logging.getLogger().setLevel(logging.INFO)
    # create telegram bot
    logging.info('initialize telegram bot')
    # bot.get_updates(offset=-1)

    game_sequencer = GameSequencer()

    # repeat until keyboard interrupt ctrl+c is given
    try:
        cnt = 677
        while not stop:
            logging.info(f'iteration: {cnt}')

            # if cnt can be divided by 100 re initialize the camera and controller -> there is some kind of bug
            #if cnt % 100 == 0:
            #    game_sequencer.re_init()

            # game_sequencer.enter_game()
            while not game_sequencer.trigger_battle():
                # error detected
                logging.info('Game Error assumed')
                bot.send_message(user_id, f'Game error assumed, starting over!')

            game_sequencer.wait_and_check_shiny_battle(cnt)

            # send with bot
            logging.info('sending image')
            bot.send_photo(user_id, photo=game_sequencer.get_battle_img(), caption=f'Iteration: {cnt}',
                           disable_notification=True)

            # check for shiny
            if game_sequencer.is_shiny():
                logging.info('shiny found!')
                bot.send_message(user_id, f'Shiny found!')
                time.sleep(604800)

            game_sequencer.return_to_homescreen_and_exit_game()
            cnt += 1
            # bot.process_new_updates(bot.get_updates())

    except KeyboardInterrupt:
        logging.info('Program will be closed')

    game_sequencer.disconnect_controller()
    # wait some time so that process can shut down properly
    time.sleep(5)
