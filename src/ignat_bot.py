# Python-telegram-bot libraries
import telegram
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler
from telegram.ext import CommandHandler
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
from mwt import MWT

# from emoji import demojize
from emoji import emojize

# TODO: possibility to change language + admin panel
# TODO: nextgen captcha
# TODO: change log format, remove text message logging

user_dict = {}
waiting_dict = {}

database = ignat_db_helper()

# Logging module for debugging
log_format = '%(asctime)s %(filename)-12s %(funcName)s %(lineno)d %(message)s'
logging.basicConfig(handlers=[RotatingFileHandler('ignat_bot.log',
                                                  maxBytes=500000,
                                                  encoding='utf-8',
                                                  backupCount=10)],
                    format=log_format,
                    level=config.LOGGER_LEVEL)

logger = logging.getLogger(__name__)  # this gets the root logger
logger.setLevel(config.LOGGER_LEVEL)


@MWT(timeout=60 * 60)
def get_admin_usernames(bot, chat_id):
    """Returns a list of admin IDs for a given chat. Results are cached for 1 hour."""
    #return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]
    admins_usernames_list = [('@' + admin.user.username) for admin in bot.get_chat_administrators(chat_id) if admin.user.is_bot == False]
    return admins_usernames_list


@MWT(timeout=60 * 60)
def get_admin_ids(bot, chat_id):
    """Returns a list of all admin IDs for a given chat. Results are cached for 1 hour."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]


def get_admins_usernamelist(bot, chat_id):
    result_list = list()

    if chat_id == -1001076839211:
        result_list.append('@vskrsnie')
        result_list.append('@ZhFfFTb')
        result_list.append('@Yankin66')
    else:
        result_list = get_admin_usernames(bot, chat_id)

    return result_list


def call_admins(update, context):
    logger.info('we are in call_admins')
    result = ''

    if update.message is None:
        return

    if update.message.from_user is None:
        return

    if update.message.text is None:
        return

    chat_id = update.message.chat_id
    logger.info(chat_id)
    logger.info(update.message.text)

    if update.message.from_user.id:
        user_id = update.message.from_user.id
    if update.message.from_user.first_name:
        user_names = update.message.from_user.first_name
    if update.message.from_user.last_name:
        user_names += ' ' + update.message.from_user.last_name
    message_id = update.message.message_id

    username = 'person with no user name'
    if update.message.from_user.username:
        username = '@' + update.message.from_user.username
    # message_id = update.message.message_id

    logger.info(user_id)
    logger.info(user_names)
    logger.info(username)
    # database.update_by_somename(user_id, user_names, username)

    admin_list = get_admins_usernamelist(context.bot,
                                         update.message.chat_id)

    logger.info(admin_list)
    if len(admin_list) == 0:
        return

    for single_admin in admin_list:
        result += ('\r\n' + single_admin)

    # new_str = update.message.text
    # logger.info(update.message.text)
    keyboard = [[InlineKeyboardButton("Удоли", callback_data=config.btnDelete
                                               + config.btn_data_separator
                                               + str(user_id))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # update.message.reply_text(result, parse_mode="Markdown")

    result += "\r\nCall to arms from {} {}".format(user_names, username)

    logger.info(result)
    if update.message.reply_to_message is None:
        # update.message.reply_text(result)
        context.bot.send_message(chat_id, result, reply_markup=reply_markup)

    else:
        update.message.reply_to_message.reply_text(result, reply_markup=reply_markup)
    context.bot.deleteMessage(chat_id, message_id)


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
    logger.info('add_user_to_waiting_dict')
    logger.info('%s %s %s %s' % (chat_id, user_id, correct_answer, job_name))

    database.add_New_User_to_waiting_list(chat_id,
                                          user_id,
                                          correct_answer,
                                          job_name)

    if chat_id not in waiting_dict.keys():
        waiting_dict[chat_id] = {}
    waiting_dict[chat_id][user_id] = correct_answer
    logger.info('waiting_dict is %s' % waiting_dict)


def remove_from_waiting_list(chat_id, user_id, correct_answer, job_name):
    del waiting_dict[chat_id][user_id]
    database.delete_from_waiting_list(chat_id,
                                      user_id,
                                      correct_answer,
                                      job_name)


def is_Trusted(chat_id, user_id):
    if chat_id in user_dict.keys():
        if user_id in user_dict[chat_id].keys():
            # logger.info(user_dict[chat_id][user_id])
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
        # TODO: call here remove from waiting list
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
    message_id = update.message.message_id
    global user_dict

    #logger.info(user_dict)

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
        chat_id = update.message.chat_id
        user_id = new_member.id

        if is_Trusted(chat_id, user_id):
            logger.info('Trusted user %s in chat %s'
                        ' so didnt show him captcha' % (user_id, chat_id))
            continue

        job_name = get_job_name(chat_id, user_id)

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
                                              callback_data= config.btnCaptcha +
                                              config.btn_data_separator +
                                              captcha_text[0] +
                                              config.btn_data_separator +
                                              str(new_member.id)),
                         InlineKeyboardButton(captcha_emoji[1],
                                              callback_data=config.btnCaptcha +
                                              config.btn_data_separator +
                                              captcha_text[1] +
                                              config.btn_data_separator +
                                              str(new_member.id)),
                         InlineKeyboardButton(captcha_emoji[2],
                                              callback_data=config.btnCaptcha +
                                              config.btn_data_separator +
                                              captcha_text[2] +
                                              config.btn_data_separator +
                                              str(new_member.id)),
                         InlineKeyboardButton(captcha_emoji[3],
                                              callback_data=config.btnCaptcha +
                                              config.btn_data_separator +
                                              captcha_text[3] +
                                              config.btn_data_separator +
                                              str(new_member.id))]]

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

            add_user_to_waiting_dict(chat_id,
                                     new_member.id,
                                     correct_answer,
                                     job_name)

            # TODO: обработать ситуацию, что зашел, получил кнопки и вышел
            # иначе будет Message to delete not found
            context.job_queue.run_once(ban_Spammer,
                                       config.due_kb_timer,
                                       context={'chat_id': chat_id,
                                                'user_id': new_member.id,
                                                'message_id':
                                                update.message.message_id,
                                                'reply_message_id':
                                                reply_message.message_id},
                                       name=job_name)


def hodor_hold_the_URL_door(update, context):
#    chat_id = update.message.chat_id
    if update.message.from_user is None:
        user_id = -1
    else:
        user_id = update.message.from_user.id
#    message_id = update.message.message_id
    save_message_text_to_database(user_id,
                                  update.message.from_user.username,
                                  update.message.text, update.message.caption,
                                  update.message.parse_entities(),
                                  update.message.caption_entities)
"""
    if not is_Trusted(chat_id, user_id):
        until = datetime.now() + timedelta(seconds=config.kick_timeout)
        context.bot.kickChatMember(chat_id, user_id, until_date=until)
        context.bot.deleteMessage(chat_id, message_id)
        logger.info('Untrusted user %s has been removed'
                    ' because of link in first message' % (user_id))
"""


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

    querydata_list = query.data.split(config.btn_data_separator)
    if querydata_list[0] == config.btnCaptcha:
        answer_from_captcha = querydata_list[1]
        suspected_user_id = int(querydata_list[2])

        job_name = str(chat_id) + config.job_name_separator + str(from_user_id)
        global user_dict

        # check if answer from potential spammer

        logger.info("from_user_id %s" % from_user_id)
        logger.info("suspected_user_id %s" % suspected_user_id)
        logger.info(from_user_id == suspected_user_id)

        if (from_user_id == suspected_user_id):

            logger.info("query.data: %s" % query.data)
            logger.info("Message text: %s" % query.message.text)

            correct_answer = waiting_dict[chat_id][from_user_id]
            logger.info("Correct answer: %s" % correct_answer)

            if (correct_answer == answer_from_captcha):
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
                    remove_from_waiting_list(chat_id,
                                             from_user_id,
                                             '',
                                             '')
                    # TODO: call here remove from waiting table too

                except Exception as e:
                    logger.info('Error while deleting %s from %s' % (chat_id, from_user_id))
                    logger.info(e)

                logger.info('waiting_dict is %s' % waiting_dict)
                logging.info(user_dict[chat_id])
            else:
                # no correct answer given
                # user_dict = add_Untrusted(chat_id, from_user_id)
                # logging.info(user_dict)

                logger.info('No correct answer from %s in %s' %
                            (chat_id, from_user_id))

                logger.info("job_name is %s" % job_name)

                try:
                    logger.info("jobs is %s" % context.job_queue.jobs())
                except Exception as e:
                    logger.info(e)

                for j in context.job_queue.jobs():
                    if j.name == job_name:
                        j.schedule_removal()
                logger.debug('ban_Spammer(%s, %s)' % (chat_id, from_user_id))
                until = datetime.now() + timedelta(seconds=config.kick_timeout)
                context.bot.kickChatMember(chat_id, from_user_id, until_date=until)

                try:
                    remove_from_waiting_list(chat_id,
                                             from_user_id,
                                             '',
                                             '')
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
    elif querydata_list[0] == config.btnDelete:
        callToArm_user_id = int(querydata_list[1])

        listWhoCanDelete = list()
        listWhoCanDelete = get_admin_ids(context.bot, chat_id)
        listWhoCanDelete.append(int(callToArm_user_id))

        if (from_user_id in listWhoCanDelete):
            logger.info('DELETE call from correct user')
            context.bot.deleteMessage(chat_id, message_id)
        else:
            pass


def hodor_hold_the_text_door(update, context):
    if update.message is None:
        return
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
        #context.bot.delete_message(chat_id, message_id)
        until = datetime.now() + timedelta(seconds=config.kick_timeout)
        context.bot.kickChatMember(chat_id, user_id, until_date=until)
        context.bot.deleteMessage(chat_id, message_id)
        logger.info('Untrusted user %s has been removed'
                    ' because of link in first message' % (user_id))
        return

    if update.message.reply_markup is not None and is_Trusted(chat_id, user_id) is not True:
        logger.info('from [%s][%s] was keyboard in forward: %s ' %
                    (update.message.from_user.id,
                     update.message.from_user.username,
                     update.message.reply_markup))
        #context.bot.delete_message(chat_id, message_id)
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
    if not config.debug:
        logging.info(user_dict)

    logger.info("Authorized on account %s. "
                "version is %s" % (bot.username, config.version))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

#    alarm_handler = CommandHandler('alrm',
#                                   call_admins,
#                                   (Filters.user(username='@guestl') & Filters.command))

    alarm_handler_alrm = CommandHandler('alrm',
                                        call_admins,
                                        (Filters.command))

    alarm_handler_alarm = CommandHandler('alarm',
                                         call_admins,
                                         (Filters.command))

    dispatcher.add_handler(MessageHandler
                           (Filters.status_update.new_chat_members,
                            hodor_watch_the_user))

    dispatcher.add_handler(MessageHandler
                           (~Filters.command & 
                            Filters.text & (Filters.entity(MessageEntity.URL) |
                                            Filters.entity(
                                            MessageEntity.TEXT_LINK)),
                            hodor_hold_the_URL_door))

    dispatcher.add_handler(MessageHandler(~Filters.command & 
                                          (Filters.text | Filters.forwarded),
                                          hodor_hold_the_text_door))

    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(alarm_handler_alrm)
    dispatcher.add_handler(alarm_handler_alarm)

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
