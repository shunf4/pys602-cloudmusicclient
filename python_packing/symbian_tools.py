class appuifw_pc:
    def note(self, unicodeStr):
        assert isinstance(unicodeStr, unicode)
        print unicodeStr
        
    def __init__(self):
        pass

from tools import s

try:
    import appuifw
except ImportError:
    appuifw = appuifw_pc()

def out(str1):
    appuifw.note(s(str1))