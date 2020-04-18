from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, PicklePersistence)
import time
import logging
import json

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, PHOTO, FINISH = range(4)

reply_keyboard = [['Info', 'Load photo'],
                  ['Exit']]
start_keyboard = [['/start']]

markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
markup_start = ReplyKeyboardMarkup(start_keyboard, one_time_keyboard=True)


admins_id = [436264579]




def start(update, context):
    reply_text = "Hi! I can find person in VK."
    print(update.message.from_user.id)
    update.message.reply_text(reply_text, reply_markup=markup)
    #with open('history.json', 'wr') as file:
        #data = json.load(file)
    return CHOOSING


def info(update, context):
	reply_text = "version 1.0"
	update.message.reply_text(reply_text, reply_markup=markup)
	return CHOOSING


def finish(update, context):
	if 'choice' in context.user_data:
		del context.user_data['choice']
	reply_text = "Goodbye!"
	update.message.reply_text(reply_text, markup=markup_start)
	return ConversationHandler.END


def error(update, context):
	"""Log Errors caused by Updates."""
	logger.warning('Update "%s" caused error "%s"', update, context.error)


def repeat_input(update, context):
	update.message.reply_text("I don't understand you.\nPlease, press /help")


def get_photo(update, context):
	update.message.reply_text("Load your photo:")
	return PHOTO


def download_photo(update, context):
	print("LOADING PHOTO")
	save_path = './'
	update.message.photo[0].get_file().download(save_path + './image.jpg')
	update.message.reply_text("Please, wait...")
	time.sleep(2) # Тут будет сам скрипт
	update.message.reply_text("Success!", reply_markup=markup)
	# update.message.reply_text("Вывод результатов", reply_markup=markup)
	print("LOADING PHOTO SUCCESS")
	return CHOOSING


def help(update, context):
	if update.message.from_user.id in admins_id:
		update.message.reply_text("All avaliable comands:\
		\n/start\n/help\n/show_history\n/add_id\n/start_parser")
	else:
		update.message.reply_text("All avaliable comands:\
		\n/start\n/help")


def main():
    pp = PicklePersistence(filename='conversationbot')
    updater = Updater('', persistence=pp, use_context=True)
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [MessageHandler(Filters.regex('^(Info)$'),
                                      info),
					   MessageHandler(Filters.regex('^Load photo$'),
                                      get_photo),
                       ],
			PHOTO: [MessageHandler(Filters.photo,
                                   download_photo),
                   ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Exit$'), finish),
				   MessageHandler(Filters.all, repeat_input)
				  ],
		allow_reentry=True,
        name="my_conversation",
        persistent=True
    )
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(MessageHandler(Filters.command, help))
    dp.add_handler(MessageHandler(Filters.all, help))
    

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
