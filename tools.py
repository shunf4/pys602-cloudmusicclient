# * -  coding: utf-8 - *
import sys
def _raw_s(str1):
    #decode from utf=8 to unicode
    if(isinstance(str, unicode)):
        return str1
    if(not isinstance(str1, str)):
        str1 = repr(str1)
    return str1.decode("utf-8")
    # else:
    #     raise TypeError, u"str1 has Type %s, which doesn't match str or unicode" % type(str1)

def s(*arg):
    if(len(arg) == 1):
        return _raw_s(arg[0])
    return tuple([_raw_s(x) for x in arg])



def us(arg):
    if(len(arg) == 1):
        return _raw_s(arg[0]).encode("utf-8")
    return tuple([_raw_s(x).encode("utf-8") for x in arg])


class Stderr:
    def __init__(self, originalStderr, logger, extraFunc = None):
        self.originalStderr = originalStderr
        self.logger = logger
        self.extraFunc = extraFunc
        
    def bind(self):
        sys.stderr = self

    def release(self):
        sys.stderr = self.originalStderr

    def write(self, sth):
        self.logger.error(sth.replace("\n",""))
        self.originalStderr.write(sth)
        if extraFunc:
            extraFunc(sth)
