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

from handlers.keyboard_captcha import tg_kb_captcha
from handlers import is_chineese

user_dict = {}
waiting_dict = {}
database = ignat_db_helper()

# Logging module for debugging
logging.basicConfig(
                    handlers=[RotatingFileHandler('ignat_bot.log', maxBytes=500000,
                backupCount=10)],
            format='%(asctime)s - %(levelname)s - %(lineno)d - %(message)s',
            level=config.LOGGER_LEVEL)

logger = logging.getLogger(__name__)  # this gets the root logger
logger.setLevel(config.LOGGER_LEVEL)


def load_database_into_memory():
    user_dict = database.get_user_dict()

    logger.info('доверенный ли юзер 66294146 в чате -1001478270653 - %s'
        % user_dict[-1001478270653][66294146])
    logger.info('всего в бд %s чата' % len(user_dict))

    for key in user_dict.keys():
        logger.info('в чате %s всего %s пользователей'
            % (key, len(user_dict[key])))

    return user_dict


def save_message_text_to_database(userID, userName, userMessageText,
                                  userMessageCaption, userMessageEntities,
                                  userMessageCaptionEntities):
    logger.info('from [%s][%s] was text: %s ' %
                (userID, userName, userMessageText))
    logger.info('from [%s][%s] was caption: %s ' %
                (userID, userName, userMessageCaption))
    logger.info('from [%s][%s] was messageEntities: %s ' %
                (userID, userName, userMessageEntities))
    logger.info('from [%s][%s] was captionEntities: %s ' %
                (userID, userName, userMessageCaptionEntities))


def add_user_into_database(chat_id, user_id, is_trusted):
    logger.debug('add_user_into_database (chat_id %s, user_id %s,\
                 is_trusted %s)' % (chat_id, user_id, is_trusted))


def update_user_into_database(chat_id, user_id, is_trusted):
    logger.debug('update_user_into_database (chat_id %s, user_id %s,\
                 is_trusted %s)' % (chat_id, user_id, is_trusted))


def add_user_to_waiting_dict(chat_id, user_id):
    logger.debug('add_user_to_waiting_dict (chat_id %s, user_id \
                 %s)' % (chat_id, user_id))


def is_Trusted(chat_id, user_id):
    return user_dict[chat_id][user_id]


def add_Untrusted(chat_id, user_id):
    if chat_id not in user_dict.keys():
        user_dict[chat_id] = {}
    user_dict[chat_id][user_id] = False
    add_user_into_database(chat_id, user_id, False)


def set_Trusted(chat_id, user_id):
    user_dict[chat_id][user_id] = True
    update_user_into_database(chat_id, user_id, True)


# TODO: проверить, что удаляется сообщение после бана
def ban_Spammer(context: telegram.ext.CallbackContext):
    chat_id = context.job.context['chat_id']
    user_id = context.job.context['user_id']
    message_id = context.job.context['message_id']
    reply_message_id = context.job.context['reply_message_id']
    context.bot.deleteMessage(chat_id, message_id)
    context.bot.deleteMessage(chat_id, reply_message_id)
    context.bot.send_message(chat_id, text='ban_Spammer %s in %s' % (user_id, chat_id))


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
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    job_name = str(chat_id) + config.job_name_separator + str(user_id)

#    logger.debug(update.message)

    logger.debug('New user [%s][%s] has language: %s ' %
                 (update.message.from_user.id,
                  update.message.from_user.username,
                  update.message.from_user.language_code))

    save_message_text_to_database(update.message.from_user.id,
                                  update.message.from_user.username,
                                  update.message.text, update.message.caption,
                                  update.message.parse_entities(),
                                  update.message.caption_entities)

    for new_member in update.message.new_chat_members:
        if is_chineese.is_chineese(new_member.username) or (is_chineese.is_chinese(new_member.full_name)):
            pass

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

        add_Untrusted(chat_id, new_member.id)
        add_user_to_waiting_dict(chat_id, new_member.id)

        context.job_queue.run_once(ban_Spammer,
                                   config.due_kb_timer,
                                   context={'chat_id': chat_id,
                                            'user_id': user_id},
                                   name=job_name)


@send_typing_action
def hodor_hold_the_URL_door(update, context):

    save_message_text_to_database(update.message.from_user.id,
                                  update.message.from_user.username,
                                  update.message.text, update.message.caption,
                                  update.message.parse_entities(),
                                  update.message.caption_entities)


'''
    logger.info(update.message.reply_markup)

    logger.info('from [%s][%s] was URL: %s ' %
                      (update.message.from_user.id,
                      update.message.from_user.username,
                      update.message.reply_markup))

    update.message.reply_text("Нельзя ссылку, дебик")
'''


# TODO: удалить
@send_typing_action
def hodor_hold_the_forward_door(update, context):

    save_message_text_to_database(update.message.from_user.id,
                                update.message.from_user.username,
                                update.message.text, update.message.caption,
                                update.message.parse_entities(),
                                update.message.caption_entities)


'''
    logger.info(update.message.reply_markup)

    if is_ChineseText(update.message.text):
        add_Untrusted(update.message.chat_id, update.message.from_user.id)
        ban_Spammer(update.message.chat_id, update.message.from_user.id)
        context.bot.delete_message(update.message.chat_id,
                        update.message.message_id)

    if update.message.reply_markup is not None:
        logger.info('from [%s][%s] was keyboard in forward: %s ' %
                      (update.message.from_user.id,
                      update.message.from_user.username,
                      update.message.reply_markup))

        update.message.reply_text("Нельзя срать ебать клавиатурой в форварде")
'''


def get_correct_captcha_answer(message_text, from_user_id):
    correct_answer_idx = from_user_id % config.kb_amount_of_keys
    logger.info(correct_answer_idx)
    logger.info(message_text)
    logger.info(from_user_id)
    return message_text.split(" ")[correct_answer_idx]


def button(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    from_user_id = query.from_user.id
    job_name = str(chat_id) + config.job_name_separator + str(from_user_id)

    # check if answer from potential spammer

    if (query.from_user.id == query.message.reply_to_message.from_user.id):
        correct_answer = query.message.text.split(" ")[-1]
        logger.info(query.message.text)
        logger.info(correct_answer)
        logger.info(query.data)
#        edited_text = "Selected option: {}".format(query.data)
#        edited_text += " and " + str(correct_answer == query.data)
#        query.edit_message_text(text=edited_text)
        if (correct_answer == query.data):
            context.bot.send_message(chat_id, text='good guy')
            # TODO: снять блокировку пользователя
            logger.debug('set_Trusted(%s, %s)' % (chat_id, from_user_id))
            for j in context.job_queue.jobs():
                if job_name in j.name:
                    j.schedule_removal()
            set_Trusted(chat_id, from_user_id)
        else:
            add_Untrusted(chat_id, from_user_id)
            logger.debug('add_Untrusted(%s, %s)' % (chat_id, from_user_id))

            # TODO: проверить, что удалится спам-сообщение
            context.bot.send_message(chat_id, text='ban spammer!')
            logger.info("job_name is %s" % job_name)
            logger.info("jobs is %s" % context.job_queue.jobs())
            for j in context.job_queue.jobs():
                if j.name == job_name:
                    j.schedule_removal()
            logger.debug('ban_Spammer(%s, %s)' % (chat_id, from_user_id))
        context.bot.delete_message(chat_id,
                                   query.message.message_id)
    else:
        context.bot.send_message(chat_id,
                                 "Ответить должен тот, кого спрашивают")


@send_typing_action
def hodor_hold_the_text_door(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    save_message_text_to_database(update.message.from_user.id,
                                  update.message.from_user.username,
                                  update.message.text, update.message.caption,
                                  update.message.parse_entities(),
                                  update.message.caption_entities)

    logger.debug(update.message.reply_markup)

    if is_chineese.is_chineese(update.message.text):
        context.bot.send_message(chat_id, text='ban spammer!')
        context.bot.delete_message(chat_id,
                                   update.message.message_id)
        return

    captcha_text = tg_kb_captcha().get_today_captcha()
    job_name = str(chat_id) + config.job_name_separator + str(user_id)

    keyboard = [[InlineKeyboardButton(captcha_text[0],
                                      callback_data=captcha_text[0]),
                 InlineKeyboardButton(captcha_text[1],
                                      callback_data=captcha_text[1]),
                 InlineKeyboardButton(captcha_text[2],
                                      callback_data=captcha_text[2]),
                 InlineKeyboardButton(captcha_text[3],
                                      callback_data=captcha_text[3])]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_text = '@%s, чтобы доказать, что не бот, надо нажать кнопку %s' %\
                 (update.message.from_user.username,
                  get_correct_captcha_answer(' '.join(map(str, captcha_text)), user_id))

    reply_message = update.message.reply_markdown(reply_text,
                                                  reply_markup=reply_markup)

# TODO: временно заблокировать юзера на писание, пока не ответит на клавиатуру
# TODO: передать в job context юзернейм и чат для бана
    context.job_queue.run_once(ban_Spammer,
                               config.due_kb_timer,
                               context={'chat_id': chat_id,
                                        'user_id': user_id,
                                        'message_id':
                                        update.message.message_id,
                                        'reply_message_id':
                                        reply_message.message_id
                                        },
                               name=job_name)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.error('Update "%s" caused error "%s"', update, context.error)


def main():
    bot = telegram.Bot(token=config.token)

    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(token=config.token, use_context=True)

    user_dict = load_database_into_memory()

    logger.info("Authorized on account %s" % bot.username)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler
                           (Filters.status_update.new_chat_members,
                            hodor_watch_the_user))

#TODO: слить с форвардом ниже
    dispatcher.add_handler(MessageHandler
                           (Filters.text & (Filters.entity(MessageEntity.URL) |
                                            Filters.entity(
                                            MessageEntity.TEXT_LINK)),
                            hodor_hold_the_URL_door))

#    dispatcher.add_handler(MessageHandler(Filters.forwarded,
#                                          hodor_hold_the_forward_door))

    dispatcher.add_handler(MessageHandler(Filters.text | Filters.forwarded,
                                          hodor_hold_the_text_door))

    dispatcher.add_handler(CallbackQueryHandler(button))

    # log all errors
    #dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
