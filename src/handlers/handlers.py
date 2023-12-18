import string


def get_eng_percent(text_to_eval):
    full_len = len(text_to_eval)
    lat_chat_cnt = 0
    for single_char in text_to_eval:
        if single_char in string.ascii_letters:
            lat_chat_cnt += 1
    return lat_chat_cnt / full_len

def has_cyrillic_and_similar_latin(text):
    text_list = text.split(' ')

    similar_latin_chars = {'a', 'e', 'o', 'p', 'c', 'x', 'y', 't', 'u', 'h', 'b', 'k', 'm', 'r', 'l'}

    for word in text_list:
        if len(word) < 3:
            continue
        else:
            has_two_cyrillics = False
            cyrillic_counter = 0
            has_similar_latin = False
            for char in word:
                char = char.lower()
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


