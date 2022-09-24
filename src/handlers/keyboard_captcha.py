from random import shuffle
from random import uniform
import json


class tg_kb_captcha():
    def __init__(self):
        self.default_len = 4
        self.kb_filename = './kaptcha.json'
        self.new_captcha = dict()

        #with open(self.kb_filename, 'w', encoding='utf8') as f:
        #    json.dump(self.new_captcha, f, ensure_ascii=False,
        #               sort_keys=True, indent=4, )

    def get_today_captcha(self, captcha_len):
        if uniform(0, 2) < 1.6 or bool(self.new_captcha) is False:
            with open(self.kb_filename, 'r', encoding='utf8') as f:
                self.new_captcha = json.load(f)

        if type(captcha_len) is not int or captcha_len < 1:
            captcha_len = self.default_len

        captcha_keys = list(self.new_captcha.keys())
        shuffle(captcha_keys)

        result_captcha = list()

        for single_key in captcha_keys:
            result_captcha.append(single_key)

        return result_captcha[-captcha_len:]

    def get_captcha_answer(self, captcha_idx):
        if bool(self.new_captcha) is False:
            with open(self.kb_filename, 'r', encoding='utf8') as f:
                self.new_captcha = json.load(f)

        ret_list = self.new_captcha[captcha_idx]
        shuffle(ret_list)
        return ret_list[-1]
