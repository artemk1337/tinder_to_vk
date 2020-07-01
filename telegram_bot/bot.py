from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, PicklePersistence, run_async)
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ChatAction, ParseMode
import time
import logging
import json
import os
from datetime import datetime
import numpy as np


class TelegramBot:
    def __init__(self, FinderVK, ResetDB, ParsePageVK,
                 TOKEN=None, REQUEST_KWARGS=None,
                 admins_id=[], password_admin=None,
                 ):
        self.logger = None
        self.reply_keyboard = [['Info', 'Feedback'],
                               ['Help']]
        self.markup = ReplyKeyboardMarkup(self.reply_keyboard,
                                          one_time_keyboard=True,
                                          resize_keyboard=True)
        self.PHOTO, self.WAIT = range(2)
        self.FinderVK = FinderVK
        self.ResetDB = ResetDB
        self.ParsePageVK = ParsePageVK
        self.updater = None
        self.TOKEN = TOKEN
        self.REQUEST_KWARGS = REQUEST_KWARGS
        self.admins_id = admins_id
        self.password_admin = password_admin

    # logging errors
    def logging(self, filename='logs.txt'):
        if filename:
            logging.basicConfig(filename=filename,
                                filemode='a',
                                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                level=logging.INFO)
        else:
            logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    # hello-message
    def start(self, update, context):
        def create_file():
            if os.path.isfile('history.json') is False:
                d = {}
                with open('history.json', 'w') as file:
                    json.dump(d, file, indent=4, separators=(',', ': '))

        context.bot.send_chat_action(chat_id=update.message.chat.id,
                                     action=ChatAction.TYPING)
        print(update.message.from_user.id)
        update.message.reply_text("<b>Hi! I can find smb in VK.</b>\n" \
                                  "Send me a <u>photo</u> and I'll give you results.",
                                  reply_markup=self.markup,
                                  parse_mode="HTML")
        create_file()
        with open('history.json', 'r') as file:
            data = json.load(file)
        with open('history.json', 'w') as file:
            data[str(update.message.from_user.id)] = [{'time': str(datetime.now()),
                                                       'username': update.message.from_user.username}]
            json.dump(data, file, indent=4, separators=(',', ': '))

    # info-message
    def info(self, update, context):
        context.bot.send_chat_action(chat_id=update.message.chat.id,
                                     action=ChatAction.TYPING)
        with open("telegram_bot/info.txt", 'r') as file:
            reply_text = file.read()
            update.message.reply_text(reply_text,
                                      reply_markup=self.markup,
                                      parse_mode=ParseMode.MARKDOWN)

    def help(self, update, context):
        context.bot.send_chat_action(chat_id=update.message.chat.id,
                                     action=ChatAction.TYPING)
        update.message.reply_text('<b><u>Load a photo to find the person in VK</u></b>\n\n'
                                  'Press <b><u>INFO</u></b> to get more info about the bot.\n'
                                  'Press <b><u>FEEDBACK</u></b> to write a feedback.\n'
                                  '<i><b>/start</b></i> - reload the bot.\n'
                                  '<i><b>/exit</b></i> - return to main menu.',
                                  reply_markup=self.markup,
                                  parse_mode="HTML")
        if update.message.from_user.id in self.admins_id:
            self.help_admins(update, context)

    def error(self, update, context):
        """Log Errors caused by Updates."""
        self.logger.warning('Update "%s" caused error "%s"', update, context.error)

    def repeat_input(self, update, context):
        update.message.reply_text("I don't understand you.\nPlease, press /help")

    def help_admins(self, update, context):
        if update.message.from_user.id in self.admins_id:
            update.message.reply_text("<b><u>All avaliable comands:</u></b>"
                                      "\n<i>/start\n/help\n/show_history\n/add_ids"
                                      "\n/add_ids_group\n/login\n/show_status"
                                      "\n/parse_group_vk\n/exit</i>",
                                      parse_mode="HTML")

    def login_start(self, update, context):
        update.message.reply_text("Write password")
        return self.WAIT

    def login_finish(self, update, context):
        if update.message.text == self.password_admin:
            update.message.reply_text("Success")
            if update.message.from_user.id not in self.admins_id:
                self.admins_id.append(update.message.from_user.id)
            return ConversationHandler.END
        else:
            update.message.reply_text("Wrong password")
            return ConversationHandler.END

    def show_history(self, update, context):
        if update.message.from_user.id in self.admins_id:
            with open('history.json', 'r') as file:
                data = json.load(file)
            update.message.reply_text(data)
        else:
            self.repeat_input(update, context)

    def return_menu(self, update, context):
        context.bot.send_chat_action(chat_id=update.message.chat.id,
                                     action=ChatAction.TYPING)
        update.message.reply_text("<i>You returned in main menu</i>",
                                  reply_markup=self.markup,
                                  parse_mode="HTML"
                                  )
        return ConversationHandler.END

    def exit_in_menu(self, update, context):
        context.bot.send_chat_action(chat_id=update.message.chat.id,
                                     action=ChatAction.TYPING)
        update.message.reply_text("<i>You are in main menu</i>",
                                  reply_markup=self.markup,
                                  parse_mode='HTML'
                                  )

    def start_feedback(self, update, context):
        context.bot.send_chat_action(chat_id=update.message.chat.id,
                                     action=ChatAction.TYPING)
        update.message.reply_text("<b><i>Write me <u>feedback</u>, "
                                  "it'll be sent to admins:</i></b>\n\n"
                                  "<b>/exit - return to main menu</b>",
                                  parse_mode='HTML',)
        return self.WAIT

    def send_feedback(self, update, context):
        message = update.message.text
        message_id = update.message.message_id
        chat_id = update.message.chat.id
        username = update.message.chat.username
        first_name = update.message.chat.first_name
        update.message.reply_text("<b><i>Successfully sent</i></b>",
                                  reply_to_message_id=message_id,
                                  reply_markup=self.markup,
                                  parse_mode='HTML')
        for i in self.admins_id:
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
        #print("Success")
        return ConversationHandler.END

    def try_answer_on_feedback(self, update, context):
        if update.message.from_user.id in self.admins_id:
            if update.message.reply_to_message:
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
                                                      reply_markup=self.markup,
                                                      parse_mode='HTML')
                        else:
                            self.repeat_input(update, context)
                    else:
                        self.repeat_input(update, context)
                except:
                    self.repeat_input(update, context)
            else:
                self.repeat_input(update, context)

    def add_ids(self, update, context):
        if update.message.from_user.id in self.admins_id:
            update.message.reply_text("<b><u>Print ids. Example:</u></b>\n"
                                      "<code>[1, 2]</code>\n<b><u>or:</u></b>\n"
                                      "<code>[i for i in range(10, 20)]</code>\n\n"
                                      "<b>/exit - return to main menu</b>",
                                      parse_mode='HTML')
            return self.WAIT
        else:
            self.repeat_input(update, context)
            return ConversationHandler.END

    @run_async
    def put_ids(self, update, context):
        message = update.message.text
        if self.ParsePageVK.STATUS_PARSER == "ON":
            d = update.message.reply_text("Parser is busy.\nWait...")
            while self.ParsePageVK.STATUS_PARSER == "ON":
                context.bot.send_chat_action(chat_id=update.message.chat.id,
                                             action=ChatAction.TYPING,
                                             timeout=5)
                time.sleep(5)
        self.ParsePageVK.STATUS_PARSER = "ON"
        update.message.reply_text("*Parsing started*",
                                  parse_mode=ParseMode.MARKDOWN
                                  )
        self.ParsePageVK.start_parsing(ids=eval(message))
        update.message.reply_text("*Parsing finished*",
                                  parse_mode=ParseMode.MARKDOWN
                                  )
        self.ParsePageVK.STATUS_PARSER = "OFF"
        return ConversationHandler.END

    def show_status(self, update, context):
        if update.message.from_user.id in self.admins_id:
            if self.ParsePageVK.STATUS_PARSER == "ON":
                update.message.reply_text(f'Parser is <b>{self.ParsePageVK.STATUS_PARSER}</b>\n'
                                          f'Current id - <b>{self.ParsePageVK.CURRENT_ID}</b>',
                                          parse_mode='HTML')
            else:
                update.message.reply_text(f'Parser is <b>{self.ParsePageVK.STATUS_PARSER}</b>',
                                          parse_mode='HTML')

    @run_async
    def download_photo(self, update, context):
        context.bot.send_chat_action(chat_id=update.message.chat.id,
                                     action=ChatAction.TYPING)
        # print("LOADING PHOTO")
        save_path = './cache/images/'
        update.message.photo[0].get_file().\
            download(save_path + f'{update.message.from_user.id}.jpg')
        if self.FinderVK.STATUS_FINDER == "ON":
            update.message.reply_text("Please, wait...")
            while self.FinderVK.STATUS_FINDER == "ON":
                context.bot.send_chat_action(chat_id=update.message.chat.id,
                                             action=ChatAction.TYPING)
                time.sleep(0.25)
        self.FinderVK.STATUS_FINDER = "ON"
        update.message.reply_text("Success!\n*Wait results!*",
                                  reply_markup=self.markup,
                                  parse_mode=ParseMode.MARKDOWN)
        #print(self.FinderVK.STATUS_FINDER)
        dists = self.FinderVK.finder(save_path + f'{update.message.from_user.id}.jpg', None)
        #print(self.FinderVK.STATUS_FINDER)
        if dists:
            for i in dists:
                #print(i)
                while True:
                    try:
                        context.bot.send_chat_action(chat_id=update.message.chat.id,
                                                     action=ChatAction.UPLOAD_PHOTO)
                        keyboard_finder = [[InlineKeyboardButton(text=f"Go to page (confidence {round((1-i[1])*100)}%)",
                                                                 url=f"https://vk.com/id{i[2]}")]]
                        markup_finder = InlineKeyboardMarkup(keyboard_finder)
                        update.message.reply_photo(i[0], caption=None, reply_markup=markup_finder)
                        break
                    except Exception as e:
                        print(e)
                        pass
        else:
            update.message.reply_text("Sorry, no results :(")

    def reset_db(self, update, context):
        if update.message.from_user.id in self.admins_id:
            self.ResetDB.reset_db_()
            print("SUCCESS RESET DB")
            pass
        else:
            self.repeat_input(update, context)

    def parse_group_vk(self, update, context):
        if update.message.from_user.id in self.admins_id:
            context.bot.send_chat_action(chat_id=update.message.chat.id,
                                         action=ChatAction.TYPING)
            update.message.reply_text("<u>Send me url on group</u>\n\n"
                                      "<b>/exit - return to main menu</b>",
                                      parse_mode='HTML', reply_markup=None)
            return self.WAIT
        else:
            self.repeat_input(update, context)
            return ConversationHandler.END

    def start_parser_group(self, update, context):
        url_ = update.message.text.split('/')[-1]
        try:
            self.ParsePageVK.\
                parse_ids_from_group(url_)
        except Exception as e:
            update.message.reply_text(e)
        update.message.reply_text("<b><i>Successfully collected</i></b>",
                                  reply_markup=self.markup,
                                  parse_mode='HTML')
        return ConversationHandler.END

    def add_ids_group(self, update, context):
        if update.message.from_user.id in self.admins_id:
            update.message.reply_text("<u>Send me url</u>",
                                      parse_mode='HTML')
            return self.WAIT
        else:
            self.repeat_input(update, context)
            return ConversationHandler.END

    @run_async
    def start_add_ids_group(self, update, context):
        message = update.message.text
        if self.ParsePageVK.STATUS_PARSER == "ON":
            d = update.message.reply_text("Parser is busy.\nWait...")
            while self.ParsePageVK.STATUS_PARSER == "ON":
                context.bot.send_chat_action(chat_id=update.message.chat.id,
                                             action=ChatAction.TYPING,
                                             timeout=5)
                time.sleep(5)
        self.ParsePageVK.STATUS_PARSER = "ON"
        update.message.reply_text("*Parsing started*",
                                  parse_mode=ParseMode.MARKDOWN
                                  )
        self.ParsePageVK.start_parsing(ids=None, path=message.split('/')[-1])
        update.message.reply_text("*Parsing finished*",
                                  parse_mode=ParseMode.MARKDOWN
                                  )
        self.ParsePageVK.STATUS_PARSER = "OFF"
        return ConversationHandler.END

    def start_bot(self):
        # pp = PicklePersistence(filename='conversationbot')
        pp = False
        self.updater = Updater(self.TOKEN,
                               persistence=pp,
                               use_context=True,
                               request_kwargs=self.REQUEST_KWARGS)
        dp = self.updater.dispatcher
        conv_handler_login = ConversationHandler(
            entry_points=[CommandHandler('login', self.login_start)],
            states={self.WAIT: [CommandHandler('exit', self.return_menu),
                                MessageHandler(Filters.all, self.login_finish)]},
            fallbacks=[CommandHandler('exit', self.return_menu)],
            allow_reentry=True, persistent=False,
            name="login_conversation")
        conv_handler_add_ids = ConversationHandler(
            entry_points=[CommandHandler('add_ids', self.add_ids)],
            states={self.WAIT: [CommandHandler('exit', self.return_menu),
                                MessageHandler(Filters.text, self.put_ids)]},
            fallbacks=[CommandHandler('exit', self.return_menu)],
            allow_reentry=False, persistent=False,
            name="add_ids_conversation")
        conv_handler_feedback = ConversationHandler(
            entry_points=[MessageHandler(Filters.regex('^Feedback$'), self.start_feedback)],
            states={self.WAIT: [CommandHandler('exit', self.return_menu),
                                MessageHandler(Filters.text, self.send_feedback)]},
            fallbacks=[CommandHandler('exit', self.return_menu)],
            allow_reentry=False, persistent=False,
            name="feedback_conversation")
        conv_handler_parse_group_VK = ConversationHandler(
            entry_points=[CommandHandler('parse_group_vk', self.parse_group_vk)],
            states={self.WAIT: [CommandHandler('exit', self.return_menu),
                                MessageHandler(Filters.text, self.start_parser_group)]},
            fallbacks=[CommandHandler('exit', self.return_menu)],
            allow_reentry=False, persistent=False,
            name="parse_group_VK_conversation")
        conv_handler_add_ids_group = ConversationHandler(
            entry_points=[CommandHandler('add_ids_group', self.add_ids_group)],
            states={self.WAIT: [CommandHandler('exit', self.return_menu),
                                MessageHandler(Filters.text, self.start_add_ids_group)]},
            fallbacks=[CommandHandler('exit', self.return_menu)],
            allow_reentry=False, persistent=False,
            name="add_ids_group_conversation")
        dp.add_handler(conv_handler_login)  # /login
        dp.add_handler(conv_handler_add_ids)  # /add_ids
        dp.add_handler(conv_handler_add_ids_group)  # /add_ids_group
        dp.add_handler(conv_handler_feedback)  # Feedback
        dp.add_handler(conv_handler_parse_group_VK)  # Parser page VK /parse_group_vk
        dp.add_handler(CommandHandler('start', self.start))  # /start
        dp.add_handler(CommandHandler('exit', self.exit_in_menu))  # /exit in main menu
        dp.add_handler(CommandHandler('reset_db', self.reset_db))  # /reset_db
        dp.add_handler(CommandHandler('show_status', self.show_status))  # /show_status
        dp.add_handler(CommandHandler('show_history', self.show_history))  # /show_history
        dp.add_handler(CommandHandler('help', self.help))  # /help
        dp.add_handler(MessageHandler(Filters.regex('^(Info)$'), self.info))  # Info
        dp.add_handler(MessageHandler(Filters.regex('^(Help)$'), self.help))  # Info
        dp.add_handler(MessageHandler(Filters.photo, self.download_photo))
        dp.add_handler(MessageHandler(Filters.text, self.try_answer_on_feedback))
        dp.add_handler(MessageHandler(Filters.all, self.repeat_input))
        self.logging(None)
        dp.add_error_handler(self.error)
        self.updater.start_polling()
        print("Start bot")
        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        self.updater.idle()

