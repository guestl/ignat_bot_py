# -*- coding: utf-8 -*-

# helper for work with database
import sqlite3

import config

import logging  
import os


os.chdir(os.path.dirname(os.path.abspath(__file__)))


class ignat_db_helper:
    """class helper for work with SQLite3 database

    methods:
        __init__ -- setup db setting
        add_currency_rates_data -- insert parsed data into rates table
    """

    def __init__(self, dbname=config.dbname):
        self.dbname = dbname
        logging.debug(dbname)
        try:
            self.connection = sqlite3.connect(dbname)
            self.cursor = self.connection.cursor()
        except Exception as e:
            logging.error(e)
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
            sql_text = "select chat_id, user_id, is_trusted from ignated_chat_users"
            self.cursor.execute(sql_text)
        except Exception as e:
            logging.error(e)
            logging.error(self.check_sql_string(sql_text))

        if self.cursor:
            for row in self.cursor:
                if row[0] not in result.keys():
                    result[row[0]] = {}
                result[row[0]][row[1]] = bool(row[2])
        return result

    def get_domain(self, src_id):
        domain = None

        try:
            sql_text = 'select rs.DOMAIN from rates_sources rs where rs.ID = ? group by rs.DOMAIN'
            self.cursor.execute(sql_text, (src_id,))
        except Exception as e:
            logging.error(e)
            logging.error(self.check_sql_string(sql_text, (src_id, )))

        if self.cursor:
            for row in self.cursor:
                domain = row[0]

        return domain

    # TODO: проверить, если на входе один список, а не список списков
    def add_currency_rates_data(self, parsed_data):
        logging.debug("add_currency_rates_data -> parsed data is ")
        logging.debug(parsed_data)

        try:
            sql_text = "REPLACE INTO rates (SRC_ID, BUY_VALUE, SELL_VALUE, AVRG_VALUE, " \
                       "RATE_DATETIME, CUR_ID_FROM, CUR_ID_TO, QUANT) VALUES (?,?,?,?,?,?,?,?)"
            self.connection.executemany(sql_text, parsed_data)

            self.connection.commit()
        except Exception as e:
            logging.error(e)
            logging.error(sql_text)
            logging.error(parsed_data)

        logging.debug("Commit done")

    def update_loader_log(self, src_id):

        logging.debug("add_loader log data for source ")
        logging.debug(src_id)

        try:
            sql_text = "INSERT INTO log_load (SRC_ID) VALUES (?)"
            self.connection.execute(sql_text, (src_id,))

            self.connection.commit()
        except Exception as e:
            raise e
            logging.error(self.check_sql_string(sql_text, (src_id, )))

        logging.debug("Commit done")

    def add_cache(self, data_for_cache):
        try:
            sql_text = "REPLACE INTO cache_rates (SRC_ID, REQUESTED_RATE_DATE, CACHE_DATA) VALUES (?,?,?)"
            self.connection.executemany(sql_text, (data_for_cache,))

            self.connection.commit()
        except Exception as e:
            logging.error(e)
            logging.error(sql_text)
            logging.error(data_for_cache)

        logging.debug("Commit done")
