# run me as "nosetests -v --nocapture --with-coverage --cover-inclusive --cover-package="ignat_bot""
from nose.tools import *
from nose import main

# import os
# import sys
# import io

from emoji import demojize

from handlers import is_chineese
from handlers.handlers import get_eng_percent
from handlers.handlers import has_cyrillic_and_similar_latin
from handlers.keyboard_captcha import tg_kb_captcha
from ignat_db_helper import ignat_db_helper
import sqlite3


class Test_Bot:
    @classmethod
    def setup_class(self):
        print("Setup class test_bot!")
        # os.chdir("D:\\Boris\\Documents\\Projects\\Py\\ignat_bot\\")
        # print("work dir is", os.getcwd())
        # self.test_uid = 'test_UID'
        self.dbname = 'D:\\Boris\\Documents\\Projects\\Py\\ignat_bot\\src\\tests\\db\\ignat_test_db.db'

    @classmethod
    def teardown_class(self):
        print("Tear down class test_bot!")

    def test_chineese(self):
        s_china_char_string = '菠菜QP推广霸屏强推APP内置'
        s_arabic_char_string = 'ارسی بلدی'
        s_no_china_string = 'no_china'
        s_none = None
        s_list = []
        s_unicode = 'Ženja 🐲 Che'

        eq_(is_chineese.is_chineese(s_no_china_string), False)
        #eq_(is_chineese.is_chineese(s_china_char_string), True)
        eq_(is_chineese.is_chineese(s_none), False)
        eq_(is_chineese.is_chineese(s_list), False)
        eq_(is_chineese.is_chineese(s_arabic_char_string), False)
        eq_(is_chineese.is_chineese(s_unicode), False)

    def test_captcha_len(self):
        assert len(tg_kb_captcha().get_today_captcha(7)) == 7
        assert len(tg_kb_captcha().get_today_captcha(1)) == 1
        assert len(tg_kb_captcha().get_today_captcha(0)) is 4
        assert len(tg_kb_captcha().get_today_captcha('a')) is 4
        assert len(tg_kb_captcha().get_today_captcha(1.3)) is 4

    def test_eng_percent(self):
        s_russian_string = 'Строка с русским текстом'
        s_lat_string = 'String with a latin text'
        s_40_russian_string = 'Строка with a latin chars in the string. So let try'
        s_60_russian_string = 'Строка где много русских букв, даже больше, чем на латинском latin text'

        assert get_eng_percent(s_40_russian_string) > 0.5
        assert get_eng_percent(s_60_russian_string) < 0.5
        assert get_eng_percent(s_lat_string) > 0.8
        assert get_eng_percent(s_russian_string) < 0.2

    def get_blacklist(chat_id):
        """Returns a list of blacklisted words for the chat."""
        bl_ctx_list = list()
        with open(config.black_list_filename, 'r', encoding='utf-8', errors='replace') as bl_f:
            bl_ctx_list = bl_f.read().split('\n')
        return list(filter(None, bl_ctx_list))

    def check_for_bl(text_from_user, chat_id):
        text_from_user = text_from_user.upper()
        for single_black_item in get_blacklist(chat_id):
            if single_black_item.upper() in text_from_user:
                return True
        return False

    def test_blacklist(self):
        s_cleanrus_string = 'Чистая строка'
        s_cleanlat_string = 'Clean string'
        s_bl_string1 = 'набор на бесплатный вебинар'
        s_bl_string2 = 'Набор на бесплатный Вебинар'
        s_bl_string3 = 'Набор на  бесплатный  Вебинар'

        assert check_for_bl(s_cleanrus_string, '') is False
        assert check_for_bl(s_cleanlat_string, '') is False
        assert check_for_bl(s_bl_string1, '') is True
        assert check_for_bl(s_bl_string2, '') is True
        assert check_for_bl(s_bl_string3, '') is True

    def test_captcha_context(self):
        captcha = tg_kb_captcha().get_today_captcha(4)
        for char in captcha:
            print(char, tg_kb_captcha().get_captcha_answer(demojize(char)))
            assert (char in tg_kb_captcha().new_captcha) is True
            assert (isinstance(tg_kb_captcha().get_captcha_answer(demojize(char)), str)) is True

    def test_captcha_context_2(self):
        captcha = tg_kb_captcha().get_today_captcha(4)
        for char in captcha:
            print(char, tg_kb_captcha().get_captcha_answer(demojize(char)))
            assert (char in tg_kb_captcha().new_captcha) is True

    def test_db_connection(self):
        chat_id = -1001478270653
        user_id = 66294146
        self.database = ignat_db_helper(dbname=self.dbname)
        user_dict = self.database.get_user_dict()
        assert user_dict[chat_id][user_id] is True

    def test_db_insert(self):
        chat_id = -1001478270653
        user_id = 666999666
        removeQuery = 'delete from ignated_chat_users where chat_id = ? and user_id = ?'
        addNewQuery = "insert into ignated_chat_users (chat_id, user_id, is_trusted) values (?, ?, 0)"
        selectUserQuery = "select count(*) from ignated_chat_users where chat_id = ? and user_id= ?"

        connection = sqlite3.connect(self.dbname)
        connection.execute(removeQuery, (chat_id, user_id,))
        connection.commit()
        connection.close()

        self.database = ignat_db_helper(dbname=self.dbname)
        result = self.database.add_New_User(chat_id, user_id)
        user_dict = self.database.get_user_dict()

        assert user_dict[chat_id][user_id] is False
        assert (user_id in user_dict[chat_id].keys()) is True

        connection = sqlite3.connect(self.dbname)
        cursor = connection.execute(selectUserQuery, (chat_id, user_id,))
        for row in cursor:
            assert row[0] == 1
        assert result == 1
        connection.close()

    def test_db_setTrusted(self):
        chat_id = -1001478270653
        user_id = 666999666
        selectTrustedUserQuery = "select is_trusted from ignated_chat_users\
                            where chat_id = ? and user_id= ?"

        self.database = ignat_db_helper(dbname=self.dbname)
        result = self.database.set_Trusted_User(chat_id, user_id)
        user_dict = self.database.get_user_dict()

        assert user_dict[chat_id][user_id] is True
        assert result == 1

        connection = sqlite3.connect(self.dbname)
        cursor = connection.execute(selectTrustedUserQuery,
                                    (chat_id, user_id,))
        for row in cursor:
            assert row[0] == 1

        connection.close()
        connection = sqlite3.connect(self.dbname)
        cursor = connection.execute(selectTrustedUserQuery,
                                    (chat_id, user_id - 1,))
        for row in cursor:
            assert row[0] == 0

        connection.close()


if __name__ == '__main__':
    main()
