import string


def get_eng_percent(text_to_eval):
    full_len = len(text_to_eval)
    lat_chat_cnt = 0
    for single_char in text_to_eval:
        if single_char in string.ascii_letters:
            lat_chat_cnt += 1
    return lat_chat_cnt / full_len


def remove_separators(text):
    separators = {'-', '.', ',', ':', ';', '"', '/', '\\', '_', '!',
                  '?', '%', '*', '(', ')', '{', '}', '[', ']', '|',
                  '=', '&', '#', '№', '—', '\''}
    space_char = ' '
    for separator in separators:
        text = text.replace(separator, space_char)
    return text


def has_cyrillic_and_similar_latin(text):
    text = text.lower()
    similar_latin_chars = {'a', 'e', 'o', 'p', 'c', 'x', 'y', 't', 'u',
                           'h', 'b', 'k', 'm', 'r', 'l'}
    space_char = ' '
    text = remove_separators(text)
    text_list = text.split(space_char)

    for word in text_list:
        if len(word) < 3:
            continue
        else:
            has_two_cyrillics = False
            cyrillic_counter = 0
            has_similar_latin = False
            for char in word:
                #char = char.lower()
                # print(f'{text_list=}, {word=}, {char=}, {cyrillic_counter=}, {has_similar_latin=}, {has_two_cyrillics=}')
                if char >= 'а' and char <= 'я':
                    cyrillic_counter += 1
                if cyrillic_counter > 1:
                    has_two_cyrillics = True

                if char in similar_latin_chars:
                    has_similar_latin = True

        if has_two_cyrillics and has_similar_latin:
            return word, True

    return '', False


def check_for_bl(text_from_user, chat_id, chat_blacklist):
    # text_from_user = remove_separators(text_from_user)
    if text_from_user is None:
        return "", False, None
    # text_from_user = text_from_user.upper()
    text_from_user = " ".join(text_from_user.split())
    word, isSpam = has_cyrillic_and_similar_latin(text_from_user)
    if isSpam:
        return word, isSpam, "Mix of latin and cyrillic"
    for single_black_item in chat_blacklist:
        if single_black_item.lower() in text_from_user.lower():
            return single_black_item, True, "Is in blacklist"
    return "", False, None
