import logging
from telegram import ChatPermissions


LOGGER_LEVEL = logging.INFO
debug = True

version = "0.24.40"

dbname = '../db/ignat_db.db'

# 60 seconds / minute * x minutes
due_kb_minutes = 2
due_kb_timer = int(60 * due_kb_minutes)
kb_amount_of_keys = 4

job_name_separator = '$'
correct_answer_separator = ':'
btn_data_separator = '|'

btnDelete = 'btnDelete'
btnCaptcha = 'btnCaptcha'

#  If user is banned for more than 366 days or less than 30 seconds
#    from the current time they are considered to be banned forever
# days
kick_timeout = 10

# minutes
silence_timeout = due_kb_minutes + 2

# READ_ONLY = ChatPermissions(can_send_messages=False,
#                             can_send_media_messages=False,
#                             can_send_polls=False,
#                             can_send_other_messages=False,
#                             can_add_web_page_previews=False,
#                             can_change_info=False,
#                             can_invite_users=None,
#                             can_pin_messages=None)

# UNBANNED = ChatPermissions(can_send_messages=True,
#                            can_send_media_messages=True,
#                            can_send_polls=True,
#                            can_send_other_messages=True,
#                            can_add_web_page_previews=True,
#                            can_change_info=False,
#                            can_invite_users=None,
#                            can_pin_messages=None)

READ_ONLY = ChatPermissions(can_send_messages=False,
                            can_send_media_messages=False,
                            can_send_other_messages=False,
                            can_add_web_page_previews=False)

UNBANNED = ChatPermissions(can_send_messages=True,
                           can_send_media_messages=True,
                           can_send_other_messages=True,
                           can_add_web_page_previews=True)

default_locale = 'ru'
black_list_filename = 'blacklist.txt'
kick_bl_timeout = 60
