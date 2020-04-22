from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, PicklePersistence, run_async)
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
import telegram
import time
import logging
import json
import os
from main import start_parse, reset_db_, find_person
from functions import (start,
    info, help, help_admins,
    error, repeat_input,
    login_start, login_finish,
    show_history,
    return_menu, exit_in_menu,
    start_feedback, send_feedback, try_answer_to_feedback,
    reset_db,
    PHOTO, WAIT,
    markup, logger)

from private import REQUEST_KWARGS, password_bot, admins_id, TOKEN_bot


STATUS_PARSER = 'OFF'
STATUS_FINDER = "OFF"

def add_ids(update, context):
    if update.message.from_user.id in admins_id:
        update.message.reply_text("<b><u>Print ids. Example:</u></b>\n"
                                  "<code>[1, 2]</code>\n<b><u>or:</u></b>\n"
                                  "<code>[i for i in range(10, 20)]</code>\n\n"
                                  "<b>/exit - return to main menu</b>",
                                  parse_mode='HTML')
        return WAIT
    else:
        repeat_input(update, context)
        return ConversationHandler.END


# 450 :
@run_async
def put_ids(update, context):
    global STATUS_PARSER
    message = update.message.text
    if STATUS_PARSER == "ON":
        d = update.message.reply_text("Parser is busy.\nWait...")
        while STATUS_PARSER == "ON":
            context.bot.send_chat_action(chat_id=update.message.chat.id,
                                         action=telegram.ChatAction.TYPING,
                                         timeout=5)
            time.sleep(5)
    STATUS_PARSER = "ON"
    update.message.reply_text("*Parsing started*",
                              parse_mode=telegram.ParseMode.MARKDOWN
                              )
    start_parse(id_=eval(message))
    STATUS_PARSER = "OFF"
    update.message.reply_text("*Parsing finished*",
                              parse_mode=telegram.ParseMode.MARKDOWN
                              )
    return ConversationHandler.END


def show_status(update, context):
    global STATUS_PARSER
    if update.message.from_user.id in admins_id:
        update.message.reply_text(f'Parser is <b>{STATUS_PARSER}</b>',
                                  parse_mode='HTML')







@run_async
def download_photo(update, context):
    context.bot.send_chat_action(chat_id=update.message.chat.id,
                                 action=telegram.ChatAction.TYPING)
    global STATUS_FINDER
    # print("LOADING PHOTO")
    save_path = '../cache/images/'
    update.message.photo[0].get_file().\
        download(save_path + f'{update.message.from_user.id}.jpg')
    if STATUS_FINDER == "ON":
        update.message.reply_text("Please, wait...")
        while STATUS_FINDER == "ON":
            context.bot.send_chat_action(chat_id=update.message.chat.id,
                                         action=telegram.ChatAction.TYPING)
            time.sleep(0.5)
    STATUS_FINDER = "ON"
    update.message.reply_text("Success!\n*Wait results!*",
                              reply_markup=markup,
                              parse_mode=telegram.ParseMode.MARKDOWN)
    dists = find_person(save_path + f'{update.message.from_user.id}.jpg')
    STATUS_FINDER = "OFF"
    if dists:
        for i in dists:
            # print(i)
            context.bot.send_chat_action(chat_id=update.message.chat.id,
                                         action=telegram.ChatAction.UPLOAD_PHOTO)
            keyboard_finder = [[InlineKeyboardButton(text="Перейти на страницу",
                                                     url=f"https://vk.com/id{i[1]}")]]
            markup_finder = InlineKeyboardMarkup(keyboard_finder)
            update.message.reply_photo(i[2], caption=None,
                                       reply_markup=markup_finder)
    else:
        update.message.reply_text("Sorry, no results :(")





def main(proxy):
    # pp = PicklePersistence(filename='conversationbot')
    pp = False
    updater = Updater(TOKEN_bot,
                      persistence=pp,
                      use_context=True,
                      request_kwargs=REQUEST_KWARGS)
    dp = updater.dispatcher
    conv_handler_login = ConversationHandler(
        entry_points=[CommandHandler('login', login_start)],
        states={WAIT: [CommandHandler('exit', return_menu),
                       MessageHandler(Filters.all, login_finish)]},
        fallbacks=[CommandHandler('exit', return_menu)],
        allow_reentry=True, persistent=False,
        name="login_conversation")
    conv_handler_add_ids = ConversationHandler(
        entry_points=[CommandHandler('add_ids', add_ids)],
        states={WAIT: [CommandHandler('exit', return_menu),
                       MessageHandler(Filters.text, put_ids)]},
        fallbacks=[CommandHandler('exit', return_menu)],
        allow_reentry=False, persistent=False,
        name="add_ids_conversation")
    conv_handler_feedback = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex('^Feedback$'), start_feedback)],
        states={WAIT: [CommandHandler('exit', return_menu),
                       MessageHandler(Filters.text, send_feedback)]},
        fallbacks=[CommandHandler('exit', return_menu)],
        allow_reentry=False, persistent=False,
        name="add_ids_conversation")
    dp.add_handler(conv_handler_login)  # /login
    dp.add_handler(conv_handler_add_ids)  # /add_ids
    dp.add_handler(conv_handler_feedback)  # Feedback
    dp.add_handler(CommandHandler('start', start))  # /start
    dp.add_handler(CommandHandler('exit', exit_in_menu))  # /exit in main menu
    dp.add_handler(CommandHandler('reset_db', reset_db))  # /reset_db
    dp.add_handler(CommandHandler('show_status', show_status))  # /show_status
    dp.add_handler(CommandHandler('show_history', show_history))  # /show_history
    dp.add_handler(CommandHandler('help', help))  # /help
    dp.add_handler(MessageHandler(Filters.regex('^(Info)$'), info))  # Info
    dp.add_handler(MessageHandler(Filters.regex('^(Help)$'), help))  # Info
    dp.add_handler(MessageHandler(Filters.photo, download_photo))
    dp.add_handler(MessageHandler(Filters.text, try_answer_to_feedback))
    dp.add_handler(MessageHandler(Filters.all, repeat_input))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling(poll_interval=1,
                          timeout=5,)
    print("Start bot")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    # updater.idle()

"""
from threading import Thread
import requests


proxy = None


def check_proxy(proxy):
    while True:
        try:
            proxies = {
            "socks5": "socks5://47.244.76.246:1080",
            }
            print('test')
            r = requests.get("http://www.google.com/", proxies=proxies)
            # r = requests.get("http://api.telegram.org/", proxies=proxies)
            # r = requests.get("https://core.telegram.org/", proxies=proxies)
            print(r)
            time.sleep(2)
        except Exception as e:
            print(e)
            pass
    pass
"""

if __name__ == '__main__':
    main(None)
    """proxy = None
    bot_th = Thread(target=main, args=(proxy,))
    #for i in range(8):
    proxy_th = Thread(target=check_proxy, args=(proxy,))
    proxy_th.start()
    #bot_th.start()"""



