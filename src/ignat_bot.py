# Python-telegram-bot libraries
import telegram
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler
from telegram import ChatAction, MessageEntity
from functools import wraps
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Logging and requests libraries
import logging
from logging.handlers import RotatingFileHandler

# Importing token from config file
import config
from ignat_db_helper import ignat_db_helper

import re
from keyboard_captcha import tg_kb_captcha


user_dict = {}
database = ignat_db_helper()


def load_database_into_memory():
    user_dict = database.get_user_dict()

    logging.debug(user_dict[-1001478270653][66294146])
    logging.debug(len(user_dict))
    for key in user_dict.keys():
        logging.debug(len(user_dict[key]))

    return user_dict


def save_message_text_to_database(userID, userName, userMessageText,
                                    userMessageCaption, userMessageEntities,
                                    userMessageCaptionEntities):

    logging.debug('from [%s][%s] was text: %s ' %
                  (userID, userName, userMessageText))

    logging.debug('from [%s][%s] was caption: %s ' %
                  (userID, userName, userMessageCaption))

    logging.debug('from [%s][%s] was messageEntities: %s ' %
                  (userID, userName, userMessageEntities))

    logging.debug('from [%s][%s] was captionEntities: %s ' %
                  (userID, userName, userMessageCaptionEntities))


def add_user_into_database(chat_id, user_id, is_trusted):
    pass


def update_user_into_database(chat_id, user_id, is_trusted):
    pass


def is_Trusted(chat_id, user_id):
    return user_dict[chat_id][user_id]


def is_ChineseText(text_to_check):
    return re.findall(r'[\u4e00-\u9fff]+', text_to_check)


def add_Untrusted(chat_id, user_id):
    if chat_id not in user_dict.keys():
        user_dict[chat_id] = {}
    user_dict[chat_id][user_id] = False
    add_user_into_database(chat_id, user_id, False)


def set_Trusted(chat_id, user_id):
    user_dict[chat_id][user_id] = True
    update_user_into_database(chat_id, user_id, True)


def ban_Spammer(chat_id, user_id):
    pass


# Typing animation to show to user to imitate human interaction
def send_action(action):
    """Sends `action` while processing func command."""

    def decorator(func):
        @wraps(func)
        def command_func(update, context, *args, **kwargs):
            context.bot.send_chat_action(chat_id=update.effective_message.chat_id,
                                            action=action)
            return func(update, context, *args, **kwargs)
        return command_func

    return decorator


send_typing_action = send_action(ChatAction.TYPING)


@send_typing_action
def hodor_watch_the_user(update, context):
    logging.debug(update.message)

    logging.debug('New user [%s][%s] has language: %s ' %
                  (update.message.from_user.id,
                  update.message.from_user.username,
                  update.message.from_user.language_code))

    save_message_text_to_database(update.message.from_user.id,
                                update.message.from_user.username,
                                update.message.text, update.message.caption,
                                update.message.parse_entities(),
                                update.message.caption_entities)

    for new_member in update.message.new_chat_members:
        if is_ChineseText(new_member.username):
            pass

        add_Untrusted(update.message.chat.id, new_member.id)


@send_typing_action
def hodor_hold_the_URL_door(update, context):

    save_message_text_to_database(update.message.from_user.id,
                                update.message.from_user.username,
                                update.message.text, update.message.caption,
                                update.message.parse_entities(),
                                update.message.caption_entities)

    logging.info(update.message.reply_markup)

    logging.info('from [%s][%s] was URL: %s ' %
                      (update.message.from_user.id,
                      update.message.from_user.username,
                      update.message.reply_markup))

    update.message.reply_text("Нельзя ссылку, дебик")


@send_typing_action
def hodor_hold_the_forward_door(update, context):

    save_message_text_to_database(update.message.from_user.id,
                                update.message.from_user.username,
                                update.message.text, update.message.caption,
                                update.message.parse_entities(),
                                update.message.caption_entities)

    logging.info(update.message.reply_markup)

    if is_ChineseText(update.message.text):
        add_Untrusted(update.message.chat_id, update.message.from_user.id)
        ban_Spammer(update.message.chat_id, update.message.from_user.id)
        context.bot.delete_message(update.message.chat_id,
                        update.message.message_id)

    if update.message.reply_markup is not None:
        logging.info('from [%s][%s] was keyboard in forward: %s ' %
                      (update.message.from_user.id,
                      update.message.from_user.username,
                      update.message.reply_markup))

        update.message.reply_text("Нельзя срать ебать клавиатурой в форварде")


def get_correct_captcha_answer(message_text):
    return message_text.split(" ")[-1]


def button(update, context):
    query = update.callback_query

    # check if answer from potential spammer

    if (query.from_user.id == query.message.reply_to_message.from_user.id):
        correct_answer = get_correct_captcha_answer(query.message.text)
#        edited_text = "Selected option: {}".format(query.data)
#        edited_text += " and " + str(correct_answer == query.data)
#        query.edit_message_text(text=edited_text)
        if (correct_answer == query.data):
            set_Trusted(query.message.chat_id, query.message.from_user.id)
        else:
            add_Untrusted(update.effective_message.chat_id, query.message.from_user.id)
            ban_Spammer(update.effective_message.chat_id, query.message.from_user.id)
        context.bot.delete_message(update.effective_message.chat_id,
                        query.message.message_id)
    else:
        pass
#        context.bot.send_message(update.effective_message.chat_id,
#                    "Ответить должен тот, кого спрашивают")


@send_typing_action
def hodor_hold_the_text_door(update, context):

    save_message_text_to_database(update.message.from_user.id,
                                update.message.from_user.username,
                                update.message.text, update.message.caption,
                                update.message.parse_entities(),
                                update.message.caption_entities)

    logging.debug(update.message.reply_markup)

    if is_ChineseText(update.message.text):
        add_Untrusted(update.message.chat_id, update.message.from_user.id)
        ban_Spammer(update.message.chat_id, update.message.from_user.id)
        context.bot.delete_message(update.message.chat_id,
                        update.message.message_id)

    if update.message.reply_markup is not None:
        logging.info('from [%s][%s] was keyboard in text: %s ' %
                      (update.message.from_user.id,
                      update.message.from_user.username,
                      update.message.reply_markup))

        update.message.reply_text("Нельзя срать ебать клавиатурой в сообщении")

    captcha_text = tg_kb_captcha().get_today_captcha()

    keyboard = [[InlineKeyboardButton(captcha_text[0],
                    callback_data=captcha_text[0]),
                 InlineKeyboardButton(captcha_text[1],
                    callback_data=captcha_text[1]),
                 InlineKeyboardButton(captcha_text[2],
                    callback_data=captcha_text[2]),
                 InlineKeyboardButton(captcha_text[3],
                    callback_data=captcha_text[3])]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_markdown("@" + update.message.from_user.username +
                 " если не спамбот, то нажми кнопку " + captcha_text[0],
                 reply_markup=reply_markup)

def error(update, context):
    """Log Errors caused by Updates."""
    logging.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    bot = telegram.Bot(token=config.token)

    # Logging module for debugging
    logging.basicConfig(
                handlers=[RotatingFileHandler('ignat_bot.log', maxBytes=500000, backupCount=10)],
                format='%(asctime)s - %(levelname)s - %(lineno)d - %(message)s',
                level=logging.DEBUG)
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(token=config.token, use_context=True)

    user_dict = load_database_into_memory()

    logging.info("Authorized on account %s" % bot.username)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members,
                                    hodor_watch_the_user))

    dispatcher.add_handler(MessageHandler(Filters.text &
                                    (Filters.entity(MessageEntity.URL) |
                                    Filters.entity(MessageEntity.TEXT_LINK)),
                                    hodor_hold_the_URL_door))

    dispatcher.add_handler(MessageHandler(Filters.forwarded,
                                    hodor_hold_the_forward_door))

    dispatcher.add_handler(MessageHandler(Filters.text,
                                    hodor_hold_the_text_door))

    dispatcher.add_handler(CallbackQueryHandler(button))

    # on noncommand i.e message - echo the message on Telegram

    # log all errors
    dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
