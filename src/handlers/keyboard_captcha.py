from random import shuffle


class tg_kb_captcha():
    default_len = 4

    new_captcha = {":eggplant:": "Фиолетовый баклажан",
                   ":potato:": "Картофель",
                   ":carrot:": "Морковь",
                   ":cucumber:": "Огурец",
                   ":banana:": "Банан",
                   ":lemon:": "Лимон",
                   ":red_apple:": "Красное яблоко",
                   ":strawberry:": "Ягода",
                   ":beer_mug:": "Пивная кружка",
                   ":baby_bottle:": "Детская бутылочка",
                   ":wine_glass:": "Бокал вино",
                   ":cup_with_straw:": "Стаканчик с трубочкой",
                   ":bus:": "Автобус",
                   ":locomotive:": "Локомотив",
                   ":ambulance:": "Скорая помощь",
                   ":fire_engine:": "Пожарная машина",
                   ":ringed_planet:": "Сатурн",
                   ":crescent_moon:": "Полумесяц",
                   ":snowflake:": "Снежинка",
                   ":fire:": "Огонь",
                   ":droplet:": "Капля",
                   ":cloud:": "Облако",
                   ":coffin:": "Гроб",
                   ":water_closet:": "Надпись WC",
                   ":no_entry:": "Знак кирпич",
                   ":radioactive:": "Знак радиоактивности"}

    def get_today_captcha(self, captcha_len):
        if type(captcha_len) is not int or captcha_len < 1:
            captcha_len = self.default_len

        captcha_keys = list(self.new_captcha.keys())
        shuffle(captcha_keys)

        result_captcha = list()

        for single_key in captcha_keys:
            result_captcha.append(single_key)

        return result_captcha[-captcha_len:]

    def get_captcha_answer(self, captcha_idx):
        return self.new_captcha[captcha_idx]
