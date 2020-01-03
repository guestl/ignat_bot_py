from emoji import emojize
from random import shuffle


class tg_kb_captcha():
    default_len = 4
    captcha = [emojize(":eggplant:", use_aliases=True),
               emojize(":potato:", use_aliases=True),
               emojize(":carrot:", use_aliases=True),
               emojize(":cucumber:", use_aliases=True),
               emojize(":banana:", use_aliases=True),
               emojize(":lemon:", use_aliases=True),
               emojize(":red_apple:", use_aliases=True),
               emojize(":strawberry:", use_aliases=True),
               emojize(":beer_mug:", use_aliases=True),
               emojize(":baby_bottle:", use_aliases=True),
               emojize(":wine_glass:", use_aliases=True),
               emojize(":cup_with_straw:", use_aliases=True),
               emojize(":bus:", use_aliases=True),
               emojize(":locomotive:", use_aliases=True),
               emojize(":ambulance:", use_aliases=True),
               emojize(":fire_engine:", use_aliases=True),
               emojize(":ringed_planet:", use_aliases=True),
               emojize(":crescent_moon:", use_aliases=True),
               emojize(":snowflake:", use_aliases=True),
               emojize(":fire:", use_aliases=True),
               emojize(":droplet:", use_aliases=True),
               emojize(":cloud:", use_aliases=True),
               emojize(":coffin:", use_aliases=True),
               emojize(":water_closet:", use_aliases=True),
               emojize(":no_entry:", use_aliases=True),
               emojize(":radioactive:", use_aliases=True)]

    def get_today_captcha(self, captcha_len):
        if type(captcha_len) is not int or captcha_len < 1:
            captcha_len = self.default_len
        shuffle(self.captcha)
        return self.captcha[-captcha_len:]
