# coding: utf-8
import os
import sys
import time
import traceback
import StringIO
import httplib
import cfileman_fd8f9a7f as cfileman
import e32
import appuifw2_fd8f9a7f as appuifw2
import logging
from tools import s, us, getIOLength
from symbian_tools import out

Pi = 3.1416

LOG_FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s [%(filename)s] %(funcName)s (%(lineno)d) : %(message)s')
utilLog = logging.getLogger("NEPy-util")
utilLog.setLevel(logging.WARNING)
metaHandler = logging.StreamHandler(sys.stdout)
utilLog.addHandler(metaHandler)
#因为没有handler的话会报错，形成不停止的递归调用

class Stderr:
    def __init__(self, originalStderr, logger, writeFunc = None, flushFunc = None):
        self.originalStderr = originalStderr
        self.logger = logger
        self.writeFunc = writeFunc
        self.flushFunc = flushFunc

    def bind(self):
        sys.stderr = self

    def release(self):
        sys.stderr = self.originalStderr

    def write(self, sth):
        self.logger.error(sth)
        #self.originalStderr.write(sth)
        if self.writeFunc:
            self.writeFunc(sth)

    def flush(self):
        self.logger.handlers[0].flush()
        #self.originalStderr.write(sth)
        if self.flushFunc:
            self.flushFunc()

aoErr = e32.Ao_lock()
aoTErr = e32.Ao_timer()
errStr = unicode()
bodyBack = appuifw2.app.body
exitBack = appuifw2.app.exit_key_handler
msgBody = appuifw2.Text_display(text=u"", skinned=True)
def restoreError():
    global bodyBack, exitBack
    #aoErr.signal()
    appuifw2.app.body=bodyBack
    appuifw2.app.exit_key_handler=exitBack

continuousError = False
def resetContinuousError():
    global continuousError
    continuousError = False

def errorAddFunc(sth):
    global continuousError
    if not continuousError:
        appuifw2.note(s("发生错误。若程序不能正常运行，请重新启动程序。"))
        appuifw2.note(s("查看文件夹E:\\NeteaseDebug2下的日志文件来排查错误。"))
        continuousError = True
        aoTErr.cancel()
        aoTErr.after(2, resetContinuousError)
    #appuifw2.note(s(sth))
    #global errStr
    #errStr += s(sth)
    #errorDisplayFunc()

def errorDisplayFunc():
    try:
        global bodyBack, exitBack, errStr, msgBody
        if id(appuifw2.app.body) != id(msgBody):
            bodyBack = appuifw2.app.body
        if id(appuifw2.app.exit_key_handler) != id(restoreError):
            exitBack = appuifw2.app.exit_key_handler

        appuifw2.app.body = msgBody
        try:
            msgBody.set(s("有错误发生：\n") + errStr + s("\n请造访e:\\neteaseDebug2查看详情。按“退出”减返回上一级。"))
        except:
            pass
        
        appuifw2.app.exit_key_handler = restoreError
    except Exception, e:
        appuifw2.note(s(repr(e)))
    #aoErr.wait()

def getNewStdErrForLauncher(SYS_STDERR):
    return Stderr(SYS_STDERR, utilLog, errorAddFunc, errorDisplayFunc)

def setUtilLogHandler(handler):
    utilLog.addHandler(handler)

def createFolders(globalVars):

    dirList = [globalVars['MAIN_NETEASE_FOLDER'], 
        os.path.join(globalVars['MAIN_NETEASE_FOLDER'], "cache"), 
        os.path.join(globalVars['MAIN_NETEASE_FOLDER'], "playlist"),
        os.path.join(globalVars['MAIN_NETEASE_FOLDER'], "lyric"), 
        os.path.join(globalVars['MAIN_NETEASE_FOLDER'], "pic"), 
        os.path.join(globalVars['MAIN_NETEASE_FOLDER'], "data"),
        globalVars['MAIN_DEBUG_FOLDER'],
        globalVars['MAIN_NETEASE_MUSIC_FOLDER'],
        ]
    fileman = cfileman.FileMan()

    for x in dirList:
        x = s(x)
        if not os.path.isdir(x):
            os.makedirs(x)
        if x.find(globalVars['MAIN_NETEASE_MUSIC_FOLDER']) == -1:
            fileman.set_att(x, cfileman.EAttHidden)

    
def download(objUrl, objPath, callBack = None, errBack = lambda:None, writeCallBack = None):
    succeed = False
    retryCount = 0
    # while((not succeed) and retryCount < 4):
    if True:
        try:
            utilLog.info(s('<Download> ') + s(objUrl) + s(' To: ') + s(objPath))
            httpDownload(objUrl, objPath, callBack, writeCallBack)
            utilLog.info(u'Download Succeed')
            succeed = True
        except Exception, e:
            if os.path.exists(objPath):
                os.remove(objPath)
            errBack()
            utilLog.error(s('<Download Failure>x%s, %s: %s'), retryCount, e.__class__, e.args)
            utilLog.error(s(traceback.format_exc()))
            raise e

def httpDownload(objUrl, objPath, callBack = None, writeCallBack = None, bs = 8*1024, writebs = 512 * 1024):
    try:
        while True:
            urlhost = objUrl.split('/')[2]
            conn1 = httplib.HTTPConnection(urlhost, 80)
            conn1.request('GET',objUrl,'',{})
            responseIO = conn1.getresponse()
            utilLog.info('Downloading From ' + objUrl)
            if responseIO.status == 302 or bool(responseIO.getheader('Location')):
                conn1.close()
                objUrl = responseIO.getheader('Location')
                utilLog.info('Redirecting to ' + objUrl)
                continue
            elif responseIO.status == 200:
                break
            else:
                raise Exception, "STATUS %s" % responseIO.status
        
        responseData = StringIO.StringIO()
        totalSize = getIOLength(responseIO)
        utilLog.info(s('<FileSize> ') + unicode(totalSize))
        fileIO = open(objPath, 'wb')
        # if totalSize < 4*1024*1024:
        if totalSize < 1:
            callbackWhenRead(responseIO, responseData, callBack, bs, totalSize)
            utilLog.info('Load Completed.')
            responseData.seek(0)
            utilLog.info('Start Write Progress.')
            callbackWhenRead(responseData, fileIO, writeCallBack, writebs, totalSize)
            utilLog.info('Write Completed.')
        else:
            #modify: force instant readwrite
            utilLog.info('Big File, Enable Instant ReadWrite')
            callbackWhenRead(responseIO, fileIO, callBack, bs * 16, totalSize)
            utilLog.info('ReadWrite Completed')
            
        
        fileIO.close()
        responseData.close()
        conn1.close()
        
        del responseData
        del fileIO
        del responseIO
        del conn1
    except Exception, e:
        try:
            conn1.close()
            responseData.close()
            fileIO.close()
        except:
            pass
        try:
            del conn1
            del responseIO
            del responseData
            del fileIO
        except:
            pass
        raise Exception, e
        
        
def callbackWhenRead(readIO, writeIO, callBack, bs, totalSize):
    receivedBlock = 0
    
        
    if callBack: callBack(0, bs, totalSize)
    block = readIO.read(bs)
    receivedBlock = 1
    if callBack: callBack(receivedBlock, bs, totalSize)

    while block:
        receivedBlock += 1
        writeIO.write(block)
        block = readIO.read(bs)
        # logs('callback %s %s %s' % (receivedBlock, bs, totalSize))
        if callBack: callBack(receivedBlock, bs, totalSize)
        
def readableTime(msec, showMsec = False, noChar = False):
    hr = long(msec / 3600000L)
    msec = long(msec % 3600000L)
    min = long(msec / 60000)
    msec = long(msec % 60000)
    sec = long(msec / 1000)
    msec = long(msec % 1000)
    str1 = ''
    if noChar:
        unit = [':',':','.','']
        if not showMsec:unit[2] = ''
    else:
        unit = ['h','m','s','ms']
    if hr > 0: str1 = str1 + '%i%s' % (hr,unit[0])
    if min > 0: str1 = str1 + '%.2i%s' % (min,unit[1])
    if sec > 0: str1 = str1 + '%.2i%s' % (sec,unit[2])
    if showMsec: str1 = str1 + '%.3i%s' % (msec,unit[3])
    if str1 == '': str1 = '0'
    return str1
    
def readableTime2(msec):
    hr = long(msec / 3600000L)
    msec = long(msec % 3600000L)
    min = long(msec / 60000)
    msec = long(msec % 60000)
    sec = long(msec / 1000)
    msec = long(msec % 1000)
    str1 = ''
    unit = [':',':','.','']
    str1 = str1 + '%.2i%s' % (min,unit[1])
    str1 = str1 + '%.2i' % (sec)
    if str1 == '': str1 = '00:00'
    return str1
    
timeUnit = ['年', '月', '日', '时', '分', '秒']
timeUnit2 = ['年', '个月', '天', '小时', '分钟', '秒']
def fuzzyTime(tgSec, timeType = 2, AbsTimeDepth = 2):
    currTime_ = time.localtime()
    tgetTime_ = time.localtime(tgSec)
    currTime = currTime_[0:6]
    tgetTime = tgetTime_[0:6]
    #找到第一个不同的时间单位
    if currTime!=tgetTime:
        firstDiff = map(lambda x:currTime[x]==tgetTime[x], range(6) ).index(False)
    else:
        return cn('几乎同时')
    #0: 相对时间 1: 绝对时间 2: 相距2月以上则绝对时间，否则相对时间
    if timeType == 2:
        if (firstDiff == 0 or (firstDiff == 1 and abs(currTime[1] - tgetTime[1]) > 1)):
            timeType = 1
            AbsTimeDepth = 3 - firstDiff
        else:
            timeType = 0
        
    if timeType == 1:
        #timeString = str(currTime[firstDiff])+cn(timeUnit[firstDiff])
        timeString = ''.join(map(lambda x:str(tgetTime[x])+cn(timeUnit[x]), range(firstDiff, firstDiff+AbsTimeDepth)))
    else:
        timeString = str(abs(currTime[firstDiff] - tgetTime[firstDiff])) + cn(timeUnit2[firstDiff])+(cn('前'),cn('后'))[currTime[firstDiff] < tgetTime[firstDiff]]
    return timeString
    
WIDTHS = [
    (126,    1), (159,    0), (687,     1), (710,   0), (711,   1),
    (727,    0), (733,    1), (879,     0), (1154,  1), (1161,  0),
    (4347,   1), (4447,   2), (7467,    1), (7521,  0), (8369,  1),
    (8426,   0), (9000,   1), (9002,    2), (11021, 1), (12350, 2),
    (12351,  1), (12438,  2), (12442,   0), (19893, 2), (19967, 1),
    (55203,  2), (63743,  1), (64106,   2), (65039, 1), (65059, 0),
    (65131,  2), (65279,  1), (65376,   2), (65500, 1), (65510, 2),
    (120831, 1), (262141, 2), (1114109, 1),
]
def get_char_width_o(char):
        """
        查表(WIDTHS)获取单个字符的宽度
        """
        char = ord(char)
        if char == 0xe or char == 0xf:
            return 0

        for num, wid in WIDTHS:
            if char <= num:
                return wid
        return 1
def get_char_width(char):
        """
        查表(WIDTHS)获取单个字符的宽度
        """
        char = ord(char)
        if char == 0xe or char == 0xf:
            return 0
        widMapped=[0.,0.86,2.0]
        for num, wid in WIDTHS:
            if char <= num:
                return widMapped[wid]
        return 1

def getStringWidth(str1):
    if len(str1) == 0: return 0
    return reduce(lambda x,y:float(x)+get_char_width_o(y), u'0'+str1)

def getStringWidth_(str1):
    if len(str1) == 0: return 0
    return reduce(lambda x,y:float(x)+get_char_width(y), u'0'+str1)
    
def fillUnicodeByWidth(str1, width, filler=u' ', leftFill = True):
    str1Width = int(getStringWidth(str1))
    str1Filler = filler * int(width - str1Width)
    if leftFill:
        return str1Filler + str1
    else:
        return str1 + str1Filler
        
def displayLongText(str1):
    textArray = [str1[x:x+30] for x in range(0,len(str1),30)]
    for (x, y) in enumerate(textArray):
        appuifw.query(y + u' (' + str(x+1) + u'/' + str(len(textArray)) + u')' , 'query')
    
def splitUnicodeByWidth(str1, width):
    totalWidth = 0.
    cursorPosition = 0
    finalList = []
    for i in range(0, len(str1)):
        thisWidth = get_char_width(str1[i])
        if (totalWidth + thisWidth)>width:
            finalList[len(finalList):] = [str1[cursorPosition:i]]
            totalWidth = thisWidth
            cursorPosition = i
        else:
            totalWidth += thisWidth
    finalList[len(finalList):] = [str1[cursorPosition:]]
    return finalList

#转码用
def cn(str1):
    return s(str1)
        
def nc(str1):return s(str1).encode('utf-8')
def cnList(list1, toTuple=False):
    cnedList = [cn(x) for x in list1]
    if toTuple:cnedList = tuple(cnedList)
    return cnedList
    
#删除一个文件夹内所有文件（文件夹排除）
def cleanDir(Dir):
    if not os.path.isdir(Dir): return None
    for f in os.listdir(Dir):
        filePath = os.path.join(Dir,f)
        if os.path.isfile(filePath):
            try:
                os.remove(filePath)
            except:
                utilLog.info('remove error on %s' % filePath)
    return True

def clearCache_():
    dirs = ['e:\\neteaseDebug', 'e:\\netease', 'e:\\netease\\lyric', 'e:\\netease\\pic', 'e:\\netease\\cache\\playlist']
    for d in dirs:
        cleanDir(d)
        
    files = ['e:\\netease\\data\\cookie.txt', 'e:\\netease\\data\\captcha.png']
    for f in files:
        if os.path.isfile(f):
            try:
                os.remove(f)
            except:
                logs('remove error on %s' % f)
    out(cn('清除完成'))