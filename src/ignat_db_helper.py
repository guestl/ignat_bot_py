# -*- coding: utf-8 -*-

# helper for work with database
import sqlite3

import config

import logging
import os

'''
addUntrustedQuery := "insert into ignated_chat_users (chat_id, user_id, is_trusted) values ($1, $2, 1)"

addTrustedQuery := "insert into ignated_chat_users (chat_id, user_id) values ($1, $2)"

updateTrustedQuery := "update ignated_chat_users set is_trusted = true where chat_id = $1 and user_id = $2" 

+ getUsersQuery := "select chat_id, user_id, is_trusted from ignated_chat_users"

не надо удалять. надо апдейтнуть, как спамера и проверять на наличие в бд
deleteSpammerQuery := "delete from ignated_chat_users where chat_id = $1 and user_id = $2"
'''

logger = logging.getLogger(__name__)
logger.setLevel(config.LOGGER_LEVEL)


os.chdir(os.path.dirname(os.path.abspath(__file__)))

#TODO: сделать коммиты при записи в бд и периодическое переоткрытие базы, чтобы легче было подменять ее
class ignat_db_helper:
    """class helper for work with SQLite3 database

    methods:
        __init__ -- setup db setting
        add_currency_rates_data -- insert parsed data into rates table
    """

    def __init__(self, dbname=config.dbname):
        self.dbname = dbname
        logger.debug(dbname)
        try:
            self.connection = sqlite3.connect(dbname)
            self.cursor = self.connection.cursor()
        except Exception as e:
            logger.error(e)
            raise e

    # I got this piece of code from
    #    http://stackoverflow.com/questions/5266430/how-to-see-the-real-sql-query-in-python-cursor-execute"
    # it doesn't work pretty good,
    #   but I can see a sql text and it's enough for me
    def check_sql_string(self, sql_text, values):
        unique = "%PARAMETER%"
        sql_text = sql_text.replace("?", unique)
        for v in values:
            sql_text = sql_text.replace(unique, repr(v), 1)
        return sql_text

    def get_user_dict(self):
        result = {}

        try:
            sql_text = "select chat_id, user_id, is_trusted\
                        from ignated_chat_users"
            self.cursor.execute(sql_text)
        except Exception as e:
            logger.error(e)
            logger.error(self.check_sql_string(sql_text))

        if self.cursor:
            for row in self.cursor:
                if row[0] not in result.keys():
                    result[row[0]] = {}
                result[row[0]][row[1]] = bool(row[2])
        return result

    def add_New_User(self, chat_id, user_id):
        add_New_User_Query = "insert into ignated_chat_users\
                              (chat_id, user_id, is_trusted) values (?, ?, 0)"

        try:
            self.cursor.execute(add_New_User_Query, (chat_id, user_id, ))
            self.connection.commit()
        except Exception as e:
            logger.error(e)
            logger.error(self.check_sql_string(add_New_User_Query,
                                               (chat_id, user_id, )))

        return self.cursor.rowcount

    def set_Trusted_User(self, chat_id, user_id):
        set_Trusted_User_Query = "update ignated_chat_users\
                              set is_trusted = 1\
                              where chat_id = ? and user_id = ?"

        try:
            self.cursor.execute(set_Trusted_User_Query, (chat_id, user_id, ))
            self.connection.commit()
        except Exception as e:
            logger.error(e)
            logger.error(self.check_sql_string(set_Trusted_User_Query,
                                               (chat_id, user_id, )))

        return self.cursor.rowcount
