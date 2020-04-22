from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ConversationHandler, run_async)
import telegram
import time
import logging
import json
import os
from main import start_parse, reset_db_, find_person
from private import password_bot, admins_id, TOKEN_bot


# Enable logging
logging.basicConfig(filename='logs.txt',
                    filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


reply_keyboard = [['Info', 'Feedback'],
                  ['Help']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)


STATUS_FINDER = "OFF"
PHOTO, WAIT = range(2)


def create_file():
    if os.path.isfile('history.json') is False:
        d = {}
        with open('history.json', 'w') as file:
            json.dump(d, file, indent=4, separators=(',', ': '))


def start(update, context):
    context.bot.send_chat_action(chat_id=update.message.chat.id,
                                 action=telegram.ChatAction.TYPING)
    print(update.message.from_user.id)
    update.message.reply_text("<b>Hi! I can find smb in VK.</b>\n" \
                              "Send me a <u>photo</u> and I'll give you results.",
                              reply_markup=markup,
                              parse_mode="HTML")
    create_file()
    with open('history.json', 'r') as file:
        data = json.load(file)
    with open('history.json', 'w') as file:
        data[int(update.message.from_user.id)] = time.time()
        json.dump(data, file, indent=4, separators=(',', ': '))


def info(update, context):
    context.bot.send_chat_action(chat_id=update.message.chat.id,
                                 action=telegram.ChatAction.TYPING)
    with open("info.txt", 'r') as file:
        reply_text = file.read()
        update.message.reply_text(reply_text,
                                  reply_markup=markup,
                                  parse_mode=telegram.ParseMode.MARKDOWN)


def help(update, context):
    context.bot.send_chat_action(chat_id=update.message.chat.id,
                                 action=telegram.ChatAction.TYPING)
    update.message.reply_text('<b><u>Load a photo to find a person in VK</u></b>\n\n'
                              'Press <b><u>INFO</u></b> to get more info about the bot.\n'
                              'Press <b><u>FEEDBACK</u></b> to write a feedback.\n'
                              '<i><b>/start</b></i> - reload the bot.\n'
                              '<i><b>/exit</b></i> - return to main menu.',
                              reply_markup=markup,
                              parse_mode="HTML")
    if update.message.from_user.id in admins_id:
        help_admins(update, context)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def repeat_input(update, context):
    update.message.reply_text("I don't understand you.\nPlease, press /help")










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









def help_admins(update, context):
    if update.message.from_user.id in admins_id:
        update.message.reply_text("<b><u>All avaliable comands:</u></b>"
                                  "\n<i>/start\n/help\n/show_history\n/add_ids"
                                  "\n/login\n/show_status\n/end</i>",
                                  parse_mode="HTML")









def login_start(update, context):
    update.message.reply_text("Write password_bot")
    return WAIT


def login_finish(update, context):
    if update.message.text == password_bot:
        update.message.reply_text("Success")
        if update.message.from_user.id not in admins_id:
            admins_id.append(update.message.from_user.id)
        return ConversationHandler.END
    else:
        update.message.reply_text("Wrong password")
        return ConversationHandler.END








def show_history(update, context):
    if update.message.from_user.id in admins_id:
        with open('history.json', 'r') as file:
            data = json.load(file)
        update.message.reply_text(data)
    else:
        repeat_input(update, context)









def reset_db(update, context):
    if update.message.from_user.id in admins_id:
        reset_db_()
    else:
        repeat_input(update, context)







def return_menu(update, context):
    context.bot.send_chat_action(chat_id=update.message.chat.id,
                                 action=telegram.ChatAction.TYPING)
    update.message.reply_text("<i>You returned in main menu</i>",
                              reply_markup=markup,
                              parse_mode="HTML"
                              )
    return ConversationHandler.END


def exit_in_menu(update, context):
    context.bot.send_chat_action(chat_id=update.message.chat.id,
                                 action=telegram.ChatAction.TYPING)
    update.message.reply_text("<i>You are in main menu</i>",
                              reply_markup=markup,
                              parse_mode='HTML'
                              )





def start_feedback(update, context):
    context.bot.send_chat_action(chat_id=update.message.chat.id,
                                 action=telegram.ChatAction.TYPING)
    update.message.reply_text("<b><i>Write me <u>feedback</u>, "
                              "it'll be sent to admins:</i></b>\n\n"
                              "<b>/exit - return to main menu</b>",
                              parse_mode='HTML',
                              )
    return WAIT


def send_feedback(update, context):
    message = update.message.text
    message_id = update.message.message_id
    chat_id = update.message.chat.id
    username = update.message.chat.username
    first_name = update.message.chat.first_name
    update.message.reply_text("<b><i>Successfully sent</i></b>",
                              reply_to_message_id=message_id,
                              reply_markup=markup,
                              parse_mode='HTML')
    for i in admins_id:
        if i != chat_id:
            context.bot.send_message(chat_id=i,
                                      text=f"<b><u>User info:</u></b>\n"
                                           f"<i>id:</i> {chat_id}\n"
                                           f"<i>username:</i> @{username}\n"
                                           f"<i>first_name:</i> {first_name}\n"
                                           f"<b><u>Message:</u></b>\n"
                                           f"<i>{message}</i>",
                                     parse_mode='HTML'
                                      )
    print("Success")
    return ConversationHandler.END


def try_answer_to_feedback(update, context):
    if update.message.from_user.id in admins_id:
        if update.message.reply_to_message.text is not None:
            try:
                text_reply = update.message.reply_to_message.text
                s = text_reply.split('\n')
                if len(s) >= 6\
                        and s[0] == 'User info:'\
                        and s[1][:3] == 'id:'\
                        and s[4] == 'Message:':
                    message = update.message.text
                    if message:
                        reply_id = int(s[1][4:])
                        username = update.message.chat.username
                        context.bot.send_message(chat_id=reply_id,
                                                 text=f"<b><u>Админ @{username} ответил:</u></b>\n"
                                                      f"<i>{message}</i>",
                                                 parse_mode='HTML'
                                                 )
                        update.message.reply_text("<b><i>Successfully sent</i></b>",
                                                  reply_markup=markup,
                                                  parse_mode='HTML')
                    else:
                        repeat_input(update, context)
                else:
                    repeat_input(update, context)
            except:
                repeat_input(update, context)
        else:
            repeat_input(update, context)






