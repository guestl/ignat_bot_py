from random import shuffle


class tg_kb_captcha():
    default_len = 4

    new_captcha = {":alarm_clock:": ["будильник", "часы"],
                   ":potato:": ["Картошка", "Бульба"],
                   ":carrot:": ["Морковь", "Оранжевый корнеплод"],
                   ":soccer_ball:": ["Мяч", "Футбольный мяч", "Круглая штука для футбола"],
                   ":banana:": ["Бaнан"],
                   ":lemon:": ["Лимoн"],
                   ":red_apple:": ["Красное яблoко"],
                   ":strawberry:": ["Ягoда"],
                   ":beer_mug:": ["Что-то с пивом", "Емкость для пива"],
                   ":baby_bottle:": ["Детская бутылочкa"],
                   ":wine_glass:": ["Bино", "Забродивший сок винограда"],
                   ":cup_with_straw:": ["Коктельный стакан"],
                   ":bus:": ["Автобуc", "Машина для перевозки людей"],
                   ":locomotive:": ["Локомoтив", "Паравоз"],
                   ":ambulance:": ["Скоpая помощь", "Машина врачей"],
                   ":fire_engine:": ["Пожарнaя машина", "Машина пожарных"],
                   ":ringed_planet:": ["Сaтурн", "Планета с кольцами"],
                   ":crescent_moon:": ["Полумeсяц", "Кусок луны"],
                   ":snowflake:": ["Снeжинка"],
                   ":fire:": ["Огoнь"],
                   ":droplet:": ["Кaпля"],
                   ":cloud:": ["Oблако"],
                   ":coffin:": ["Гpоб", "Ящик для трупа"],
                   ":water_closet:": ["Табличка туалета"],
                   ":no_entry:": ["Проезд запрещен", "Дорожный запрещающий знак"],
                   ":radioactive:": ["Радиоактивная oпасность"]}

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
        ret_list = self.new_captcha[captcha_idx]
        shuffle(ret_list)
        return ret_list[-1]
