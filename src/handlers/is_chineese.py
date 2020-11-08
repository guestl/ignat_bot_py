#   import re

#   is_chineese = lambda text: re.findall(r'[\u4e00-\u9fff]+', text)
# https://stackoverflow.com/questions/1366068/whats-the-complete-range-for-chinese-characters-in-unicode


def is_chineese(text):
    if ((text is None)) or (type(text) is not str):
            return False
    return False
#   временная заглушка, т.к. проверка не нужна
#    for char in text:
#        if ord(char) in range(19968, 40959):
#            # ord('\u4e00')..ord('\u9FFF')
#            return True
#    return False
