import re

is_chineese = lambda text: re.findall(r'[\u4e00-\u9fff]+', text)
