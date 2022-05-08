import string


def get_eng_percent(text_to_eval):
    full_len = len(text_to_eval)
    lat_chat_cnt = 0
    for single_char in text_to_eval:
        if single_char in string.ascii_letters:
            lat_chat_cnt += 1
    return lat_chat_cnt / full_len
