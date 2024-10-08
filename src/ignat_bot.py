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
from tgtoken import tgtoken
from ignat_db_helper import ignat_db_helper

from handlers.keyboard_captcha import tg_kb_captcha
from handlers import is_chineese
# from handlers.handlers import has_cyrillic_and_similar_latin
from handlers.handlers import check_for_bl

from datetime import datetime, timedelta
from mwt import MWT

# from emoji import demojize
from emoji import emojize

from collections import defaultdict
import threading

# TODO: possibility to change language + admin panel
# TODO: nextgen captcha

user_dict = {}
waiting_dict = {}

# Словарь для хранения сообщений по media_group_id
media_groups = defaultdict(list)
# Таймеры для отслеживания, когда медиа-группа считается завершенной
group_timers = {}

database = ignat_db_helper()
stg_kb_captcha = tg_kb_captcha()


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
    """Returns a list of admin IDs for a given chat. 
       Results are cached for 1 hour."""
    #return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]
    admins_usernames_list = [('@' + admin.user.username) for admin in bot.get_chat_administrators(chat_id) if admin.user.is_bot == False]
    return admins_usernames_list


@MWT(timeout=60 * 60)
def get_admin_ids(bot, chat_id):
    """Returns a list of all admin IDs for a given chat.
       Results are cached for 1 hour."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]


@MWT(timeout=60 * 15)
def get_blacklist(chat_id):
    """Returns a list of blacklisted words for the chat."""
    bl_ctx_list = list()
    with open(config.black_list_filename, 'r', encoding='utf-8', errors='replace') as bl_f:
        bl_ctx_list = bl_f.read().split('\n')
    return list(filter(None, bl_ctx_list))


def get_admins_usernamelist(bot, chat_id):
    result_list = list()

    if chat_id == -1001076839211:
        result_list.append('@vskrsnie')
        result_list.append('@Yankin66')
        result_list.append('@Life1over')
        result_list.append('@Nataliolsi')
        result_list.append('@guestl')
    else:
        result_list = get_admin_usernames(bot, chat_id)

    return result_list


def call_admins(update, context):
    logger.debug('we are in call_admins')
    result = ''

    if update.message is None:
        return

    if update.message.from_user is None:
        return

    if update.message.text is None:
        return

    chat_id = update.message.chat_id
    logger.debug(chat_id)
    logger.debug(update.message.text)

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

    logger.debug(user_id)
    logger.debug(user_names)
    logger.debug(username)
    # database.update_by_somename(user_id, user_names, username)

    admin_list = get_admins_usernamelist(context.bot,
                                         update.message.chat_id)

    logger.debug(admin_list)
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


def save_message_text_to_database(chat_id, userID, userName, userMessageText,
                                  userMessageCaption, userMessageEntities,
                                  userMessageCaptionEntities):
    if userMessageText:
        database.save_message(chat_id, userID, userMessageText)


def add_user_to_waiting_dict(chat_id, user_id, correct_answer, job_name):
    logger.debug('add_user_to_waiting_dict')
    logger.debug('%s %s %s %s' % (chat_id, user_id, correct_answer, job_name))

    database.add_New_User_to_waiting_list(chat_id,
                                          user_id,
                                          correct_answer,
                                          job_name)

    if chat_id not in waiting_dict.keys():
        waiting_dict[chat_id] = {}
    waiting_dict[chat_id][user_id] = correct_answer
    logger.debug('waiting_dict is %s' % waiting_dict)


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
    logger.debug("isTrusted = None")
    return None


def add_Untrusted(chat_id, user_id):
    if chat_id not in user_dict.keys():
        user_dict[chat_id] = {}
    logger.debug('add_New_User (chat_id %s, user_id %s,\
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
    try:
        context.bot.deleteMessage(chat_id, message_id)
    except Exception as e:
        logger.error('Can not delete a message in %s' % (chat_id))
        logger.error(e)
    try:
        context.bot.deleteMessage(chat_id, reply_message_id)
    except Exception as e:
        logger.error('Can not delete a message in %s' % (chat_id))
        logger.error(e)
    until_date = datetime.now() + timedelta(seconds=config.kick_timeout)

    try:
        context.bot.kick_chat_member(chat_id, user_id, until_date=until_date)
    except Exception as e:
        logger.error('Can not kick a spamer in %s' % (chat_id))
        logger.error(e)
    try:
        remove_from_waiting_list(chat_id, user_id, '', '')
    except Exception as e:
        logger.error('Error while deleting %s from %s' % (chat_id, user_id))
        logger.error(e)

    logger.debug('waiting_dict is %s' % waiting_dict)
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

    # logger.info(user_dict)

#    logger.debug(update.message)

    logger.debug('New user [%s][%s] has language: %s ' %
                 (update.message.from_user.id,
                  update.message.from_user.username,
                  update.message.from_user.language_code))

    save_message_text_to_database(update.message.chat_id,
                                  update.message.from_user.id,
                                  update.message.from_user.username,
                                  update.message.text, update.message.caption,
                                  update.message.parse_entities(),
                                  update.message.caption_entities)

    for new_member in update.message.new_chat_members:
        chat_id = update.message.chat_id
        user_id = new_member.id

        if context.bot.id == user_id:
            if is_Trusted(chat_id, user_id):
                continue
            else:
                set_Trusted(chat_id, user_id)
                continue

        if is_Trusted(chat_id, user_id):
            logger.debug('Trusted user %s in chat %s'
                        ' so didnt show him captcha' % (user_id, chat_id))
            continue

        job_name = get_job_name(chat_id, user_id)

        logger.debug('check if chineese')
        if (is_chineese.is_chineese(new_member.username) or
                is_chineese.is_chineese(new_member.full_name)):
            until = datetime.now() + timedelta(seconds=config.kick_timeout)

            try:
                context.bot.kick_chat_member(chat_id, user_id, until_date=until)
            except Exception as e:
                logger.error('Can not kick a chinese user in %s' % (chat_id))
                logger.error(e)

            try:
                context.bot.deleteMessage(chat_id, message_id)
            except Exception as e:
                logger.error('Can not delete a message in %s' % (chat_id))
                logger.error(e)

            logger.debug('Chinese user %s with username %s fullname %s has been removed\
                        ' % (user_id, new_member.username, new_member.full_name))
            return

        if chat_id not in user_dict.keys():
            user_dict[chat_id] = {}

        if new_member.id not in user_dict[chat_id].keys():
            captcha_text = stg_kb_captcha.get_today_captcha(tg_kb_captcha)
            logger.info('captcha text is %s' % (captcha_text))

            # TODO: Transfert emoji back to keyboard_captcha class
            captcha_emoji = []

            for single_captcha in captcha_text:
                captcha_emoji.append(emojize(single_captcha, use_aliases=True))

            until = datetime.now() + timedelta(minutes=config.silence_timeout)
            try:
                logger.debug('Going to restrict some guy')
                context.bot.restrictChatMember(chat_id, user_id,
                                               permissions=config.READ_ONLY,
                                               until_date=until)
                logger.debug('Restricted')
            except Exception as e:
                logger.error('>> Error while restrict user')
                logger.error('known chats are -1001253360480,-1001732066603, -1001076839211')
                logger.error('chat_id = ' + str(chat_id))
                logger.error('user_id = ' + str(user_id))
                logger.error('update.message.chat.title = ' + update.message.chat.title)
                logger.error('update.message.chat.username = ' + update.message.chat.username)
                logger.error('<< Error while restrict user')
                logger.error(e)

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
            correct_btn_description = stg_kb_captcha.get_captcha_answer(correct_answer)

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

            logger.info('welcome text is %s' % (welcome_text))
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
    pass


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

        logger.debug("from_user_id %s" % from_user_id)
        logger.debug("suspected_user_id %s" % suspected_user_id)
        logger.debug(from_user_id == suspected_user_id)

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
                try:
                    logger.debug('Going to unrestrict some guy')
                    context.bot.restrictChatMember(chat_id, from_user_id,
                                                   permissions=config.UNBANNED,
                                                   until_date=until)
                    logger.debug('UnRestricted')
                except Exception as e:
                    logger.error('>> Error while unrestrict user')
                    logger.error('known chats are -1001253360480,-1001732066603, -1001076839211')
                    logger.error('chat_id = ' + str(chat_id))
                    logger.error('from_user_id = ' + str(from_user_id))
                    logger.error('query.message.chat.title = ' + query.message.chat.title)
                    logger.error('query.message.chat.username = ' + query.message.chat.username)
                    logger.error('<< Error while unrestrict user')
                    logger.error(e)

                logger.debug('Adding %s as trusted' % (from_user_id))
                if add_Untrusted(chat_id, from_user_id):
                    logger.debug('Added %s as untrusted' % (from_user_id))

                if set_Trusted(chat_id, from_user_id):
                    logger.debug('Setted %s as trusted' % (from_user_id))

                user_dict = database.get_user_dict()

                try:
                    remove_from_waiting_list(chat_id,
                                             from_user_id,
                                             '',
                                             job_name)
                    # TODO: call here remove from waiting table too

                except Exception as e:
                    logger.error('Error while deleting %s from %s' % (chat_id, from_user_id))
                    logger.error(e)

                logger.debug('waiting_dict is %s' % waiting_dict)
                # logger.info(user_dict[chat_id])
            else:
                # no correct answer given
                # user_dict = add_Untrusted(chat_id, from_user_id)
                # logger.info(user_dict)

                logger.info('No correct answer from %s in %s' %
                            (chat_id, from_user_id))

                logger.debug("job_name is %s" % job_name)

                try:
                    logger.debug("jobs is %s" % context.job_queue.jobs())
                except Exception as e:
                    logger.error(e)

                for j in context.job_queue.jobs():
                    if j.name == job_name:
                        j.schedule_removal()
                logger.debug('ban_Spammer(%s, %s)' % (chat_id, from_user_id))
                until = datetime.now() + timedelta(seconds=config.kick_timeout)

                try:
                    context.bot.kick_chat_member(chat_id, from_user_id, until_date=until)
                except Exception as e:
                    logger.error('Error while kicking %s from %s' % (from_user_id, chat_id))
                    logger.error(e)

                try:
                    remove_from_waiting_list(chat_id,
                                             from_user_id,
                                             '',
                                             job_name)
                    # TODO: call here remove from waiting table too
                except Exception as e:
                    logger.error('Error while deleting %s from waiting list in %s' % (from_user_id, chat_id))
                    logger.error(e)

                logger.debug('waiting_dict is %s' % waiting_dict)
                logger.info('Untrusted user %s has been removed'
                            ' because of incorrect answer' % (from_user_id))

            try:
                context.bot.delete_message(chat_id, message_id)
            except Exception as e:
                logger.error('Error while delete a message in %s' % (chat_id))
                logger.error(e)

        else:
            context.bot.answer_callback_query(query.id, text="Ответить должен тот, кого спрашивают")
    elif querydata_list[0] == config.btnDelete:
        callToArm_user_id = int(querydata_list[1])

        listWhoCanDelete = list()
        listWhoCanDelete = get_admin_ids(context.bot, chat_id)
        listWhoCanDelete.append(int(callToArm_user_id))

        if (from_user_id in listWhoCanDelete):
            logger.debug('DELETE call from correct user')
            try:
                context.bot.deleteMessage(chat_id, message_id)
            except Exception as e:
                logger.error('Error while delete a message in %s' % (chat_id))
                logger.error(e)
        else:
            context.bot.answer_callback_query(query.id, text="Удоляет или автор, или одмины")


# Функция для удаления спам-групп
def remove_spam_group(group_id, context):
    chat_id = media_groups[group_id][0].chat_id
    # Проверка на спам
    for msg in media_groups[group_id]:
        if msg.caption is not None: #and is_Trusted(chat_id, user_id) is not True:
            logger.info(f'msg.caption ---> {msg.caption}')
            bl_word, bl_result, reason = check_for_bl(msg.caption, chat_id, get_blacklist(chat_id)) 
            if bl_result:
                until = datetime.now() + timedelta(seconds=config.kick_bl_timeout)
                try:
                    context.bot.kick_chat_member(chat_id, msg.from_user.id, until_date=until)
                except Exception as e:
                    logger.error('Can not kick in %s' % (chat_id))
                    logger.error(e)
                try:
                    # Удаляем все сообщения в группе
                    for msg in media_groups[group_id]:
                        context.bot.delete_message(chat_id=chat_id, message_id=msg.message_id)
                    logger.info(f"Deleted media group {group_id} for spam")
                    logger.info('User %s has been temporarily removed "%s"'
                                ' blacklisted word "%s" in the message' % (msg.from_user.id, reason, bl_word))
                    context.bot.unban_chat_member(chat_id, msg.from_user.id)
                    break
                except Exception as e:
                    logger.error('Can not delete a message in %s' % (chat_id))
                    logger.error(e)

    # Удаляем группу из памяти
    del media_groups[group_id]
    del group_timers[group_id]


def hodor_hold_the_photo_door(update, context):
    message = update.message
    if message is None:
        return

    # Проверяем, что сообщение является частью медиа-группы
    if message.media_group_id:
        group_id = message.media_group_id

        # Сохраняем сообщение в словарь по media_group_id
        media_groups[group_id].append(message)
        logger.info(media_groups)

        # Сбрасываем существующий таймер, если группа еще обновляется
        if group_id in group_timers:
            group_timers[group_id].cancel()
            # logger.info('reset timer')

        # Устанавливаем таймер на 5 секунд (регулируйте время по необходимости)
        # logger.info('set timer')
        timer = threading.Timer(5.0, remove_spam_group, [group_id, context])
        group_timers[group_id] = timer
        timer.start()


def hodor_hold_the_text_door(update, context):
    if update.message is None:
        return
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    message_id = update.message.message_id
    global user_dict
    message_text = update.message.text
    save_message_text_to_database(update.message.chat_id,
                                  update.message.from_user.id,
                                  update.message.from_user.username,
                                  message_text, update.message.caption,
                                  update.message.parse_entities(),
                                  update.message.caption_entities)

    if (is_chineese.is_chineese(message_text)
            and is_Trusted(chat_id, user_id) is not True):
        # context.bot.delete_message(chat_id, message_id)
        until = datetime.now() + timedelta(seconds=config.kick_timeout)
        try:
            context.bot.kick_chat_member(chat_id, user_id, until_date=until)
        except Exception as e:
            logger.error('Can not kick in %s' % (chat_id))
            logger.error(e)
        try:
            context.bot.deleteMessage(chat_id, message_id)
        except Exception as e:
            logger.error('Can not delete a message in %s' % (chat_id))
            logger.error(e)
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
        try:
            context.bot.kick_chat_member(chat_id, user_id, until_date=until)
        except Exception as e:
            logger.error('Can not kick in %s' % (chat_id))
            logger.error(e)
        try:
            context.bot.deleteMessage(chat_id, message_id)
        except Exception as e:
            logger.error('Can not delete a message in %s' % (chat_id))
            logger.error(e)
        logger.info('Untrusted user %s has been removed'
                    ' because of keyboard in first message' % (user_id))

    if message_text is not None: #and is_Trusted(chat_id, user_id) is not True:
        bl_word, bl_result, reason = check_for_bl(message_text, chat_id, get_blacklist(chat_id)) 
        if bl_result:
            logger.info(update.message.text)
            until = datetime.now() + timedelta(seconds=config.kick_bl_timeout)
            try:
                context.bot.kick_chat_member(chat_id, user_id, until_date=until)
            except Exception as e:
                logger.error('Can not kick in %s' % (chat_id))
                logger.error(e)
            try:
                context.bot.deleteMessage(chat_id, message_id)
            except Exception as e:
                logger.error('Can not delete a message in %s' % (chat_id))
                logger.error(e)
            logger.info('User %s has been temporarily removed "%s"'
                        ' blacklisted word "%s" in the message' % (user_id, reason, bl_word))
            context.bot.unban_chat_member(chat_id, user_id)
            return

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

    bot = telegram.Bot(token=tgtoken)

    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(token=tgtoken, use_context=True)

    logger.info("Authorized on account %s. "
                "version is %s" % (bot.username, config.version))

    user_dict = database.get_user_dict()
    if not config.debug:
        logger.info(len(user_dict))

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

    alarm_handler_sos = CommandHandler('sos',
                                       call_admins,
                                       (Filters.command))

    dispatcher.add_handler(MessageHandler
                           (Filters.status_update.new_chat_members,
                            hodor_watch_the_user))

    dispatcher.add_handler(MessageHandler
                           (~Filters.command
                            & Filters.text & (Filters.entity(MessageEntity.URL)
                                            | Filters.entity(
                                            MessageEntity.TEXT_LINK)),
                            hodor_hold_the_URL_door))

    dispatcher.add_handler(MessageHandler(~Filters.command
                                          & (Filters.text),
                                          hodor_hold_the_text_door))

    dispatcher.add_handler(MessageHandler(~Filters.command 
                                          & (Filters.photo | Filters.forwarded),
                                          hodor_hold_the_photo_door))

    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(alarm_handler_alrm)
    dispatcher.add_handler(alarm_handler_alarm)
    dispatcher.add_handler(alarm_handler_sos)

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
