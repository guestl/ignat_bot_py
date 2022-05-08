# -*- coding: utf-8 -*-
import yaml
import os


os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Locales:
    def __init__(self, loc):
        with open(r'lngstrres.yaml') as file:
            lng_dict = yaml.load(file, Loader=yaml.FullLoader)

        if loc == "en":
            self.new_member = lng_dict['en_new_member']
        elif loc == "ru":
            self.new_member = lng_dict['ru_new_member']
