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

from datetime import datetime, timedelta

# from emoji import demojize
from emoji import emojize

user_dict = {}
waiting_dict = {}

database = ignat_db_helper()

# Logging module for debugging
log_format = '%(asctime)s %(levelname)s %(filename)-12s %(funcName)s %(lineno)d %(message)s'
logging.basicConfig(handlers=[RotatingFileHandler('ignat_bot.log',
                                                  maxBytes=500000,
                                                  backupCount=10)],
                    format=log_format,
                    level=config.LOGGER_LEVEL)

logger = logging.getLogger(__name__)  # this gets the root logger
logger.setLevel(config.LOGGER_LEVEL)


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


def add_user_to_waiting_dict(chat_id, user_id, correct_answer, job_name):
    logger.info('add_user_to_waiting_dict (chat_id %s, user_id \
                 %s, correct_answer %s), job_name %S' % (chat_id, user_id, 
                                                         correct_answer, job_name))
    if chat_id not in waiting_dict.keys():
        waiting_dict[chat_id] = {}
    waiting_dict[chat_id][user_id] = correct_answer
    logger.info('waiting_dict is %s' % waiting_dict)


def remove_from_waiting_list(chat_id, user_id, correct_answer, job_name):
    del waiting_dict[chat_id][from_user_id]


def is_Trusted(chat_id, user_id):
    if chat_id in user_dict.keys():
        if user_id in user_dict[chat_id].keys():
#            logger.info(user_dict[chat_id][user_id])
            return user_dict[chat_id][user_id]
    logger.info("isTrusted = None")
    return None


def add_Untrusted(chat_id, user_id):
    if chat_id not in user_dict.keys():
        user_dict[chat_id] = {}
    logger.info('add_New_User (chat_id %s, user_id %s,\
                 )' % (chat_id, user_id))
    return database.add_New_User(chat_id, user_id)


def set_Trusted(chat_id, user_id):
    logger.info('database.set_Trusted_User (chat_id %s, user_id %s,)' %
                (chat_id, user_id))
    return database.set_Trusted_User(chat_id, user_id)


def ban_Spammer(context: telegram.ext.CallbackContext):
    chat_id = context.job.context['chat_id']
    user_id = context.job.context['user_id']
    message_id = context.job.context['message_id']
    reply_message_id = context.job.context['reply_message_id']
    context.bot.deleteMessage(chat_id, message_id)
    context.bot.deleteMessage(chat_id, reply_message_id)
    until_date = datetime.now() + timedelta(seconds=config.kick_timeout)
    context.bot.kickChatMember(chat_id, user_id, until_date=until_date)
    try:
        #TODO: call here remove from waiting list
        remove_from_waiting_list(chat_id, user_id, '', '')
    except Exception as e:
        logger.info('Error while deleting %s from %s' % (chat_id, user_id))
        logger.info(e)


    logger.info('waiting_dict is %s' % waiting_dict)
    logger.info('%s removed due timeout' % (user_id))


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


def get_job_name(chat_id, user_id):
    return str(chat_id) + config.job_name_separator + str(user_id)


@send_typing_action
def hodor_watch_the_user(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    job_name = get_job_name(chat_id, user_id)
    message_id = update.message.message_id
    global user_dict

    logger.info(user_dict)

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
        logging.info('check if chineese')
        if (is_chineese.is_chineese(new_member.username) or
                is_chineese.is_chineese(new_member.full_name)):
            until = datetime.now() + timedelta(seconds=config.kick_timeout)
            context.bot.kickChatMember(chat_id, user_id, until_date=until)
            context.bot.deleteMessage(chat_id, message_id)
            logger.info('Chinese user %s with username %s fullname %s has been removed\
                        ' % (user_id, new_member.username, new_member.full_name))
            return

        if chat_id not in user_dict.keys():
            user_dict[chat_id] = {}

        if new_member.id not in user_dict[chat_id].keys():
            captcha_text = tg_kb_captcha().get_today_captcha(tg_kb_captcha)
            logging.info('captcha text is %s' % (captcha_text))

            # TODO: Transfert emoji back to keyboard_captcha class
            captcha_emoji = []

            for single_captcha in captcha_text:
                captcha_emoji.append(emojize(single_captcha, use_aliases=True))

            until = datetime.now() + timedelta(days=config.silence_timeout)
            context.bot.restrictChatMember(chat_id, user_id,
                                           permissions=config.READ_ONLY,
                                           until_date=until)

            keyboard = [[InlineKeyboardButton(captcha_emoji[0],
                                              callback_data=captcha_text[0]),
                         InlineKeyboardButton(captcha_emoji[1],
                                              callback_data=captcha_text[1]),
                         InlineKeyboardButton(captcha_emoji[2],
                                              callback_data=captcha_text[2]),
                         InlineKeyboardButton(captcha_emoji[3],
                                              callback_data=captcha_text[3])]]

            reply_markup = InlineKeyboardMarkup(keyboard)
            correct_answer = get_correct_captcha_answer_idx(captcha_text,
                                                            user_id)
            correct_btn_description = tg_kb_captcha().get_captcha_answer(correct_answer)

            if new_member.username:
                welcome_text = ('@%s чтобы доказать, что не бот,'
                                ' нажми в течение %s сек. кнопку с изображением: %s' %
                                (new_member.username, config.due_kb_timer,
                                    correct_btn_description))
            elif new_member.full_name:
                welcome_text = ('%s чтобы доказать, что не бот, нажми'
                                ' в течение %s сек. кнопку с изображением: %s' %
                                (new_member.full_name, config.due_kb_timer,
                                    correct_btn_description))
            else:
                welcome_text = ('Чтобы доказать, что не бот,'
                                ' нажми в течение %s сек. кнопку с изображением: %s' %
                                (config.due_kb_timer, correct_btn_description))

            logging.info('welcome text is %s' % (welcome_text))
            reply_message = update.message.reply_text(welcome_text, reply_markup=reply_markup)

            add_user_to_waiting_dict(chat_id, new_member.id, correct_answer, job_name)

            # TODO: обработать ситуацию, что зашел, получил кнопки и вышел
            # иначе будет Message to delete not found
            context.job_queue.run_once(ban_Spammer,
                                       config.due_kb_timer,
                                       context={'chat_id': chat_id,
                                                'user_id': user_id,
                                                'message_id':
                                                update.message.message_id,
                                                'reply_message_id':
                                                reply_message.message_id},
                                       name=job_name)


def hodor_hold_the_URL_door(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    save_message_text_to_database(update.message.from_user.id,
                                  update.message.from_user.username,
                                  update.message.text, update.message.caption,
                                  update.message.parse_entities(),
                                  update.message.caption_entities)

    if not is_Trusted(chat_id, user_id):
        until = datetime.now() + timedelta(seconds=config.kick_timeout)
        context.bot.kickChatMember(chat_id, user_id, until_date=until)
        context.bot.deleteMessage(chat_id, message_id)
        logger.info('Untrusted user %s has been removed'
                    ' because of link in first message' % (user_id))


def get_correct_captcha_answer_idx(captcha, from_user_id):
    correct_answer_idx = from_user_id % config.kb_amount_of_keys
    # logger.info(correct_answer_idx)
    # logger.info(captcha)
    # logger.info(from_user_id)
    return captcha[correct_answer_idx]


def button(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    from_user_id = query.from_user.id
    message_id = query.message.message_id
    job_name = str(chat_id) + config.job_name_separator + str(from_user_id)
    global user_dict

    # check if answer from potential spammer

    if (query.from_user.id == query.message.reply_to_message.from_user.id):

        correct_answer = waiting_dict[chat_id][from_user_id]
        logger.info("Message text: %s" % query.message.text)
        logger.info("Correct answer: %s" % correct_answer)
        logger.info("query.data: %s" % query.data)

        if (correct_answer == query.data):
            logger.info('Correct answer from %s in %s' %
                        (from_user_id, chat_id))
            logger.debug('set_Trusted(%s, %s)' % (chat_id, from_user_id))
            for j in context.job_queue.jobs():
                if job_name in j.name:
                    j.schedule_removal()
            if set_Trusted(chat_id, from_user_id):
                user_dict = database.get_user_dict()

            until = datetime.now()  # + timedelta(days=config.silence_timeout)
            context.bot.restrictChatMember(chat_id, from_user_id,
                                           permissions=config.UNBANNED,
                                           until_date=until)
            logging.info('Adding %s as trusted' % (from_user_id))
            if add_Untrusted(chat_id, from_user_id):
                logging.info('Added %s as untrusted' % (from_user_id))

            if set_Trusted(chat_id, from_user_id):
                logging.info('Setted %s as trusted' % (from_user_id))

            user_dict = database.get_user_dict()

            try:
                remove_from_waiting_list(chat_id, user_id, '', '')
                # TODO: call here remove from waiting table too

            except Exception as e:
                logger.info('Error while deleting %s from %s' % (chat_id, from_user_id))
                logger.info(e)

            logger.info('waiting_dict is %s' % waiting_dict)
            logging.info(user_dict)
        else:
            # no correct answer given
            # user_dict = add_Untrusted(chat_id, from_user_id)
            # logging.info(user_dict)

            logger.info('No correct answer from %s in %s' %
                        (chat_id, from_user_id))

            logger.info("job_name is %s" % job_name)
            logger.info("jobs is %s" % context.job_queue.jobs())
            for j in context.job_queue.jobs():
                if j.name == job_name:
                    j.schedule_removal()
            logger.debug('ban_Spammer(%s, %s)' % (chat_id, from_user_id))
            until = datetime.now() + timedelta(seconds=config.kick_timeout)
            context.bot.kickChatMember(chat_id, from_user_id, until_date=until)

            try:
                remove_from_waiting_list(chat_id, user_id, '', '')
                # TODO: call here remove from waiting table too

            except Exception as e:
                logger.info('Error while deleting %s from %s' % (chat_id, from_user_id))
                logger.info(e)

            logger.info('waiting_dict is %s' % waiting_dict)
            logger.info('Untrusted user %s has been removed'
                        ' because of incorrect answer' % (from_user_id))

        context.bot.delete_message(chat_id, message_id)
    else:
        pass
#        context.bot.send_message(chat_id,
#                                 "Ответить должен тот, кого спрашивают")


def hodor_hold_the_text_door(update, context):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    global user_dict
    save_message_text_to_database(update.message.from_user.id,
                                  update.message.from_user.username,
                                  update.message.text, update.message.caption,
                                  update.message.parse_entities(),
                                  update.message.caption_entities)

    if ((is_chineese.is_chineese(update.message.text) or
         is_chineese.is_chineese(update.message.caption)) and
            is_Trusted(chat_id, user_id) is not True):
        context.bot.delete_message(chat_id, message_id)
        until = datetime.now() + timedelta(seconds=config.kick_timeout)
        context.bot.kickChatMember(chat_id, user_id, until_date=until)
        context.bot.deleteMessage(chat_id, message_id)
        logger.info('Untrusted user %s has been removed'
                    ' because of link in first message' % (user_id))
        return

    if update.message.reply_markup is not None:
        logger.info('from [%s][%s] was keyboard in forward: %s ' %
                    (update.message.from_user.id,
                     update.message.from_user.username,
                     update.message.reply_markup))
        context.bot.delete_message(chat_id, message_id)
        until = datetime.now() + timedelta(seconds=config.kick_timeout)
        context.bot.kickChatMember(chat_id, user_id, until_date=until)
        context.bot.deleteMessage(chat_id, message_id)
        logger.info('Untrusted user %s has been removed'
                    ' because of keyboard in first message' % (user_id))

    if is_Trusted(chat_id, user_id) is False:
        if set_Trusted(chat_id, user_id):
            user_dict = database.get_user_dict()
    elif is_Trusted(chat_id, user_id) is None:
        if add_Untrusted(chat_id, user_id):
            if set_Trusted(chat_id, user_id):
                user_dict = database.get_user_dict()


def error(update, context):
    """Log Errors caused by Updates."""
    logger.error('Update "%s" caused error "%s"', update, context.error)


def main():
    global user_dict
    bot = telegram.Bot(token=config.token)

    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(token=config.token, use_context=True)

    user_dict = database.get_user_dict()
    logging.info(user_dict)

    logger.info("Authorized on account %s. "
                "version is %s" % (bot.username, config.version))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler
                           (Filters.status_update.new_chat_members,
                            hodor_watch_the_user))

    dispatcher.add_handler(MessageHandler
                           (Filters.text & (Filters.entity(MessageEntity.URL) |
                                            Filters.entity(
                                            MessageEntity.TEXT_LINK)),
                            hodor_hold_the_URL_door))

    dispatcher.add_handler(MessageHandler(Filters.text | Filters.forwarded,
                                          hodor_hold_the_text_door))

    dispatcher.add_handler(CallbackQueryHandler(button))

    # log all errors
    # dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # TODO: add here call retrive waiting list and create jobs


    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
