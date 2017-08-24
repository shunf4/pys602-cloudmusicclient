# * -  coding: utf-8 - *

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
