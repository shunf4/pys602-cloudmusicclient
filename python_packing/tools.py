# * -  coding: utf-8 - *
import sys
def _raw_s(str1):
    #decode from utf=8 to unicode
    if(isinstance(str1, unicode)):
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


def getIOLength(readIO):
    try:
        if readIO.len == None:
            raise AttributeError
        else:
            totalSize = long(readIO.len)
            return totalSize
    except AttributeError:
        pass

    try:
        if readIO.getheader("Content-Length") == None:
            raise AttributeError
        else:
            totalSize = int(readIO.getheader("Content-Length"))
            return totalSize
    except AttributeError:
        pass

    try:
        if readIO.length == None:
            raise AttributeError
        else:
            totalSize = readIO.length
            return totalSize
    except AttributeError:
        pass

    #raise IOError, "Can't read Length"
    return 10485760


def print_(sth):
    print sth

def noneThen(sth, sth2):
    if sth is not None:
        return sth
    return sth2
