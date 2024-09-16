from handlers import has_cyrillic_and_similar_latin

black_list_filename = 'D:\\Boris\\Documents\\Projects\\Py\\ignat_bot\\src\\blacklist.txt '



def get_blacklist(chat_id):
    """Returns a list of blacklisted words for the chat."""
    bl_ctx_list = list()
    with open(black_list_filename, 'r', encoding='utf-8', errors='replace') as bl_f:
        bl_ctx_list = bl_f.read().split('\n')
    return list(filter(None, bl_ctx_list))


def check_for_bl(text_from_user, chat_id):
    text_from_user = text_from_user.upper()
    text_from_user = " ".join(text_from_user.split())
    for single_black_item in get_blacklist(chat_id):
        if single_black_item.upper() in text_from_user:
            return True
    return False

def check_for_has_cyrillic_and_similar_latin(chat_id):
    for single_black_item in get_blacklist(chat_id):
        spam, word = has_cyrillic_and_similar_latin(single_black_item)
        if spam:
            print(f'{spam}, "{word}", sentence = "{single_black_item}"')


s_cleanrus_string = 'Чистая строка'
s_cleanlat_string = 'Clean string'
s_bl_string1 = 'набор на бесплатный вебинар'
s_bl_string2 = 'Набор на бесплатный Вебинар'
s_bl_string3 = 'Набор на  бесплатный  Вебинар'

print(check_for_bl(s_cleanrus_string, '') is False)
print(check_for_bl(s_cleanlat_string, '') is False)
print(check_for_bl(s_bl_string1, '') is True)
print(check_for_bl(s_bl_string2, '') is True)
print(check_for_bl(s_bl_string3, '') is True)

test_text = 'Hаша команда'
print(has_cyrillic_and_similar_latin(test_text), test_text)
test_text = 'Беp'
print(has_cyrillic_and_similar_latin(test_text), test_text)
test_text = 'Bepнaя'
print(has_cyrillic_and_similar_latin(test_text), test_text)
test_text = 'Bepнo'
print(has_cyrillic_and_similar_latin(test_text), test_text)
test_text = 'Was'
print(has_cyrillic_and_similar_latin(test_text), test_text)
test_text = 'put'
print(has_cyrillic_and_similar_latin(test_text), test_text)
test_text = 'Всем привет'
print(has_cyrillic_and_similar_latin(test_text), test_text)
test_text = 'http:\\www.spb'
print(has_cyrillic_and_similar_latin(test_text), test_text)
test_text = 'has issue'
print(has_cyrillic_and_similar_latin(test_text), test_text)
test_text = 'Доход от 500usdt в неделю'
print(has_cyrillic_and_similar_latin(test_text), test_text)
test_text = 'ʍы ᴦоᴛоʙы обучиᴛь ʙᴀᴄ ʙᴄᴇʍу нᴇобходиʍоʍу'
print(has_cyrillic_and_similar_latin(test_text), test_text)
test_text = '250-350USD'
print(has_cyrillic_and_similar_latin(test_text), test_text)
test_text = 'crypto'
print(has_cyrillic_and_similar_latin(test_text), test_text)

print(check_for_has_cyrillic_and_similar_latin(12))