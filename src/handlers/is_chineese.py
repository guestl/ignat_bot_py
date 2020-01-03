#   import re

#   is_chineese = lambda text: re.findall(r'[\u4e00-\u9fff]+', text)


def is_chineese(text):
    if ((text is None)) or (type(text) is not str):
            return False
    for char in text:
        if ord(char) >= 14000:
            return True
    return False
