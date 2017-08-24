
import os
#execfile(os.environ['PYTHONSTARTUP'])
import neapi
import urllib
import logging
try:
    import ujson as json
except ImportError:
    import json

import socket
socket.setdefaulttimeout(3)

def localDataFuncWrapper(localDataFileName, defaultLocalData):
    def loadLocalData(localDataFileName, defaultLocalData):
        localDataFileName = os.path.abspath(localDataFileName)
        
        if not os.path.exists(localDataFileName):
            localDataStr = json.dumps(defaultLocalData)
            file0 = open(localDataFileName, 'wb')
            file0.write(localDataStr)
            file0.close()
            return defaultLocalData

        file1 = open(localDataFileName, 'r')
        localDataStr = file1.read()
        localData = json.loads(localDataStr)
        file1.close()
        return localData

    def writeLocalData(localDataFileName, localDataObject):
        localDataFileName = os.path.abspath(localDataFileName)
        localDataStr = json.dumps(localDataObject)

        file1 = open(localDataFileName, 'wb')
        file1.write(localDataStr)
        file1.close()
        
    return lambda:loadLocalData(localDataFileName, defaultLocalData), lambda localData:writeLocalData(localDataFileName, localData)

apiLogH = logging.StreamHandler()
httpLogH = logging.StreamHandler()

apiLogH.setLevel(15)
httpLogH.setLevel(15)

demoLoadLocalData, demoWriteLocalData = localDataFuncWrapper(".\\localdata.txt", {"cookie": "", "clientToken" : "1_1UlfKAX7rcMafd1M0ndPFJPGITMgOexy_IZ8ivs4nXAGjweA4z6VEtLdEP143Y5Bg"})

apiConfig = {
    "username" : "fs2018",
    "password" : "defAPa1997_eu",
    "cellphone" : "",
    "isPhone" : False,
    "HTTPLogHandler" : httpLogH,
    "LogHandler" : apiLogH,
    "HTTPLogHandler" : httpLogH,
    "LoadLocalDataFunc" : demoLoadLocalData,
    "WriteLocalDataFunc" : demoWriteLocalData,
    "apiVersion" : 1,
    "readCallback": None
}

api = neapi.NEApi(apiConfig)

userCancelLogin = False
while True:
    if userCancelLogin:
        break

    while api.needCaptcha:
        captchaURL = api.getCaptchaURL()
        urllib.urlretrieve(captchaURL, ".\\captcha.png")
        captcha = raw_input("Please input captcha: ")
        if(captcha == ''):
            #User Cancellation
            userCancelLogin = True
            continue
        api.sendCaptcha(captcha)

    try:
        api.keepLogined()
    except neapi.NEApiNeedCaptcha:
        continue
    except neapi.NEApiBlockedByYundun:
        clientToken = raw_input("Please input another available clientToken: ")
        if clientToken == '':
            #User Cancellation
            userCancelLogin = True
            continue
        api.setClientToken(clientToken)
        continue

    break

songlistList, songlistListF = api.getUserSonglistList(0, 0, 4)

print neapi.getItem(songlistListF, songlistList, ("songlistListLength"))
print neapi.getItem(songlistListF, songlistList, ("songlistListSonglist", 1), "songlistName")
