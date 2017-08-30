# * -  coding: utf-8 - *
import urllib
import httplib
import logging
import StringIO
import binascii
import os
import sys
import re
import random
from tools import s, getIOLength, print_, noneThen
from Cookie import SimpleCookie
sys.path.append(os.path.abspath(".\\lib"))
try:
    from Crypto.Cipher import AES
except ImportError:
    import aes as AES
import simplejson as json
import base64
import hashlib
import socket
socket.setdefaulttimeout(5)

COOKIE_APPVER = 'appver=2.7.1;'
CSRF_RE = re.compile(r'(?<=__csrf=)(\w+)')
UID_RE = re.compile(r'(?<=NETEASE\_WDA\_UID=).*(?=#\|)')
EXPIREDATE_RE = re.compile(r'expires\s*=\s*(?P<date>.+?);', re.I)

URL_PROTOCOL = "http://"
URL_HOST = "music.163.com"


NEAPI_METHOD_GET = 0
NEAPI_METHOD_POST_NORMAL = 1
NEAPI_METHOD_POST_ENCRYPTED = 2
NEAPI_METHOD_GET_AND_POST_ENCRYPTED = 3
NEAPI_BRS = [('b', 96000),('l', 128000),('m', 192000),('h', 320000)]

URL_LOGIN_REFRESH = "/weapi/login/token/refresh"
URL_LOGIN_EMAIL = "/weapi/login/"
URL_LOGIN_PHONE = "/weapi/login/cellphone"
URL_CAPTCHA_IMAGE = "/captcha"
URL_CAPTCHA_SUBMIT = "/weapi/image/captcha/verify/hf"
URL_NEAPIS = {
    "getUserSonglistList" : 
        [("/api/user/playlist", NEAPI_METHOD_GET, {
            'songlistListSonglist': lambda obj, n:obj['playlist'][n],
            'songlistListLength': lambda obj:len(obj['playlist']),
            'songlistName': lambda obj: obj['name'],
            'songlistCreateTime': lambda obj: obj['createTime'],
            'songlistUpdateTime': lambda obj: obj['updateTime'],
            'songlistCoverURL': lambda obj: obj['coverImgUrl'],
            'songlistID': lambda obj: obj['id'],
        }), ("/weapi/user/playlist", NEAPI_METHOD_POST_ENCRYPTED, {
            'songlistListSonglist': lambda obj, n:obj['playlist'][n],
            'songlistListLength': lambda obj:len(obj['playlist']),
            'songlistName': lambda obj: obj['name'],
            'songlistCreateTime': lambda obj: obj['createTime'],
            'songlistUpdateTime': lambda obj: obj['updateTime'],
            'songlistCoverURL': lambda obj: obj['coverImgUrl'],
            'songlistID': lambda obj: obj['id'],
        })],
    "getRecommendationSonglist" : 

        [("/weapi/v2/discovery/recommend/songs", NEAPI_METHOD_POST_ENCRYPTED, {
            'songlistSong': lambda obj, n:obj['recommend'][n],
            'songlistLength': lambda obj:len(obj['recommend']),
            'songName': lambda obj: obj['name'],
            'songlistSongsID': lambda obj: [x['id'] for x in obj['recommend']],
            'songlistSongsName': lambda obj: [x['name'] for x in obj['recommend']],
            'songDuration': lambda obj: obj['duration'],
            #'songlistSongsID2': lambda obj: [map(lambda x:song.get(x).get('id'), [u"bMusic",u"lMusic", u"mMusic", u"hMusic"]) for song in obj['recommend']],
            'songID': lambda obj: obj['id'],
            'songID2': lambda obj: map(lambda x:noneThen(obj.get(x,{}),{}).get('id'), [u"bMusic",u"lMusic", u"mMusic", u"hMusic"]),
            'songAlbumName': lambda obj: obj['album']['name'],
            'songAlbumID': lambda obj: obj['album']['id'],
            'songAlbumCoverURL': lambda obj: obj['album']['picUrl'],
            'songArtistsName': lambda obj: [artist['name'] for artist in obj.get('artists',[])],
            'songArtistsID': lambda obj: [artist['id'] for artist in obj.get('artists',[])],
            'songTrackNo': lambda obj: obj["no"],
            'songAlias': lambda obj: noneThen(obj["alias"], []),
        })],
    "getFMSonglist" : 
        [("/weapi/v1/radio/get", NEAPI_METHOD_POST_ENCRYPTED, {
            'songlistSong': lambda obj, n:obj['data'][n],
            'songlistLength': lambda obj:len(obj['data']),
            'songName': lambda obj: obj['name'],
            'songlistSongsID': lambda obj: [x['id'] for x in obj['data']],
            'songlistSongsName': lambda obj: [x['name'] for x in obj['data']],
            'songlistSongsID2': lambda obj: [map(lambda x:noneThen(song.get(x,{}), {}).get('id'), [u"bMusic",u"lMusic", u"mMusic", u"hMusic"]) for song in obj['data']],
            'songID': lambda obj: obj['id'],
            'songID2': lambda obj: map(lambda x:noneThen(obj.get(x,{}),{}).get('id'), [u"bMusic",u"lMusic", u"mMusic", u"hMusic"]),
            'songAlbumName': lambda obj: obj['album']['name'],
            'songAlbumID': lambda obj: obj['album']['id'],
            'songDuration': lambda obj: obj['duration'],
            'songAlbumCoverURL': lambda obj: obj['album']['picUrl'],
            'songArtistsName': lambda obj: [artist['name'] for artist in obj.get('artists',[])],
            'songArtistsID': lambda obj: [artist['id'] for artist in obj.get('artists',[])],
            'songTrackNo': lambda obj: obj["no"],
            'songAlias': lambda obj: noneThen(obj["alias"]),
        })],
    "NE_likeFMSong" : 
        [("/weapi/v1/radio/like", NEAPI_METHOD_POST_ENCRYPTED, {})],
    "NE_trashFMSong" : 
        [("/weapi/v1/radio/trash/add", NEAPI_METHOD_POST_ENCRYPTED, {})],
    "getSonglist" : 
        [("/weapi/v3/playlist/detail", NEAPI_METHOD_POST_ENCRYPTED, 
        {
            'songlistCreateTime': lambda obj:obj['playlist']['createTime'],
            'songlistCoverURL': lambda obj:(obj['playlist']['coverImgUrl']),
            'songlistName': lambda obj: obj['playlist']['name'],
            'songlistCreatorName': lambda obj: obj['playlist']['creator']['name'],
            'songlistCreatorID': lambda obj: obj['playlist']['creator']['userId'],
            'songlistID': lambda obj: obj['playlist']['id'],
            'songlistTotalLen': lambda obj: obj['playlist']['trackCount'],
            'songlistThisLen': lambda obj: len(obj['playlist']['tracks']),
            'songlistUpdateTime': lambda obj: obj['playlist']['updateTime'],
            'songlistUpdateTime': lambda obj: obj['playlist']['updateTime'],
            'songlistSong': lambda obj,n:obj['playlist']['tracks'][n],
            'NE_songlistSongID':lambda obj,n:obj['playlist']['trackIds'][n]['id'],
            'songlistSongsID': lambda obj: [x['id'] for x in obj['playlist']['tracks']],
            'songlistSongsName': lambda obj: [x['name'] for x in obj['playlist']['tracks']],

            'songName': lambda obj: obj['name'],
            #'songlistSongID2s': lambda obj: [map(lambda x:song.get(x).get('id'), [u"b",u"l", u"m", u"h"]) for song in obj['playlist']['tracks']],
            'songID': lambda obj: obj['id'],
            #'songID2': lambda obj: map(lambda x:obj.get(x).get('id'), [u"b",u"l", u"m", u"h"]),
            'songAlbumName': lambda obj: obj['al']['name'],
            'songAlbumID': lambda obj: obj['al']['id'],
            'songAlbumCoverURL': lambda obj: obj['al']['picUrl'],
            'songDuration': lambda obj: obj['dt'],
            'songArtistsName': lambda obj: [artist['name'] for artist in obj.get('ar',[])],
            'songArtistsID': lambda obj: [artist['id'] for artist in obj.get('ar',[])],
            'songTrackNo': lambda obj: obj["no"],
            'songAlias': lambda obj: noneThen(obj["a"], []),
        }
        )
        ],
    "NE_subscribeSonglist" : 
        [("/weapi/playlist/subscribe", NEAPI_METHOD_POST_ENCRYPTED, {})],
    "getAlbum" : 
        [("/api/album/%s", NEAPI_METHOD_GET, 
        {
            'albumArtistsName': lambda obj: [artist["name"] for artist in obj['album']['artists']],
            'albumArtistsID': lambda obj:[artist["id"] for artist in obj['album']['artists']],
            'albumID': lambda obj: obj['album']['name'],
            'albumName': lambda obj: obj['album']['name'],
            'albumCoverURL': lambda obj: obj['album']['picUrl'],
            'albumSong': lambda obj,n: obj['album']['songs'][n],
            'albumSongsName' : lambda obj: [song["name"] for song in obj['album']['songs']],
            'albumSongsID' : lambda obj: [song["id"] for song in obj['album']['songs']],
            'albumSongsID2': lambda obj: [map(lambda x:noneThen(song.get(x,{}), {}).get('dfsId'), [u"bMusic",u"lMusic", u"mMusic", u"hMusic"]) for song in obj['album']['songs']],
            
            'albumTotalLen': lambda obj: obj['album']['size'],
            'songName': lambda obj: obj['name'],
            'songID': lambda obj: obj['id'],
            'songID2': lambda obj: map(lambda x:noneThen(obj.get(x + "Music",{}),{}).get('dfsId'), [u"b",u"l", u"m", u"h"]),
            'songAlbumName': lambda obj: obj['album']['name'],
            'songAlbumID': lambda obj: obj['album']['id'],
            'songDuration': lambda obj: obj['duration'],
            'songAlbumCoverURL': lambda obj: obj['album']['picUrl'],
            'songArtistsName': lambda obj: [artist['name'] for artist in obj.get('artists',[])],
            'songArtistsID': lambda obj: [artist['id'] for artist in obj.get('artists',[])],
            'songTrackNo': lambda obj: obj["no"],
            'songAlias': lambda obj: noneThen(obj["alias"]),
        }
        ),
        ("/weapi/v1/album/%s", NEAPI_METHOD_POST_ENCRYPTED, 
        {
            'albumArtistsName': lambda obj: [artist["name"] for artist in obj['album']['artists']],
            'albumArtistsID': lambda obj:[artist["id"] for artist in obj['album']['artists']],
            'albumID': lambda obj: obj['album']['name'],
            'albumName': lambda obj: obj['album']['name'],
            'albumCoverURL': lambda obj: obj['album']['picUrl'],
            'albumSong': lambda obj,n: obj['album']['songs'][n],
            'albumSongsName' : lambda obj: [song["name"] for song in obj['album']['songs']],
            'albumSongsID' : lambda obj: [song["id"] for song in obj['songs']],
            'albumSongsID2': lambda obj: [map(lambda x:noneThen(song.get(x,{}),{}).get('fid'), [u"b",u"l", u"m", u"h"]) for song in obj['songs']],
            
            'albumTotalLen': lambda obj: obj['album']['size'],
            'songName': lambda obj: obj['name'],
            'songID': lambda obj: obj['id'],
            'songID2': lambda obj: map(lambda x:noneThen(obj.get(x + "",{}),{}).get('fid'), [u"b",u"l", u"m", u"h"]),
            'songAlbumName': lambda obj: obj['al']['name'],
            'songAlbumID': lambda obj: obj['al']['id'],
            'songDuration': lambda obj: obj['dt'],
            'songAlbumCoverURL': lambda obj: obj['al']['picUrl'],
            'songArtistsName': lambda obj: [artist['name'] for artist in obj.get('ar',[])],
            'songArtistsID': lambda obj: [artist['id'] for artist in obj.get('ar',[])],
            'songTrackNo': lambda obj: obj["no"],
            'songAlias': lambda obj: noneThen(obj["a"]),
        }
        )
        ],
    "getSongs" : 
        [("/api/song/detail", NEAPI_METHOD_GET, 
        {
            'songsSong': lambda obj,n: obj['songs'][n],
            'songsSongsName' : lambda obj: [song["name"] for song in obj['songs']],
            'songsSongsID' : lambda obj: [song["id"] for song in obj['songs']],
            #'songsSongsID2': lambda obj: [map(lambda x:song.get(x).get('dfsId'), [u"bMusic",u"lMusic", u"mMusic", u"hMusic"]) for song in obj['album']['songs']],
            
            'songsTotalLen': lambda obj: len(obj['songs']),
            'songName': lambda obj: obj['name'],
            'songID': lambda obj: obj['id'],
            'songID2': lambda obj: map(lambda x:noneThen(obj.get(x + "Music",{}),{}).get('dfsId'), [u"b",u"l", u"m", u"h"]),
            'songAlbumName': lambda obj: obj['album']['name'],
            'songAlbumID': lambda obj: obj['album']['id'],
            'songDuration': lambda obj: obj['duration'],
            'songAlbumCoverURL': lambda obj: obj['album']['picUrl'],
            'songArtistsName': lambda obj: [artist['name'] for artist in obj.get('artists',[])],
            'songArtistsID': lambda obj: [artist['id'] for artist in obj.get('artists',[])],
            'songTrackNo': lambda obj: obj["no"],
            'songAlias': lambda obj: noneThen(obj["alias"], []),
        }
        ),
        ("/weapi/song/detail", NEAPI_METHOD_POST_ENCRYPTED, 
        {
            'songsSong': lambda obj,n: obj['songs'][n],
            'songsSongsName' : lambda obj: [song["name"] for song in obj['songs']],
            'songsSongsID' : lambda obj: [song["id"] for song in obj['songs']],
            #'songsSongsID2': lambda obj: [map(lambda x:song.get(x).get('dfsId'), [u"bMusic",u"lMusic", u"mMusic", u"hMusic"]) for song in obj['album']['songs']],
            
            'songsTotalLen': lambda obj: len(obj['songs']),
            'songName': lambda obj: obj['name'],
            'songID': lambda obj: obj['id'],
            'songID2': lambda obj: map(lambda x:noneThen(obj.get(x + "",{}),{}).get('dfsId'), [u"b",u"l", u"m", u"h"]),
            'songAlbumName': lambda obj: obj['al']['name'],
            'songDuration': lambda obj: obj['dt'],
            'songAlbumID': lambda obj: obj['al']['id'],
            'songAlbumCoverURL': lambda obj: obj['al']['picUrl'],
            'songArtistsName': lambda obj: [artist['name'] for artist in obj.get('ar',[])],
            'songArtistsID': lambda obj: [artist['id'] for artist in obj.get('ar',[])],
            'songTrackNo': lambda obj: obj["no"],
            'songAlias': lambda obj: noneThen(obj["a"]),
        }
        )
        ],
    "getSongsURL" : 
        [("/weapi/song/enhance/player/url", NEAPI_METHOD_POST_ENCRYPTED, 
        {
            'urls': lambda obj: [x.get('url') if isinstance(x, dict) else None for x in obj['data']]
        }
        )
        ],
    "getLyric" : 
        [("/weapi/song/lyric", NEAPI_METHOD_GET_AND_POST_ENCRYPTED, 
        {
            'lyric': lambda obj: obj.get("lrc",{}).get("lyric"),
            'translatedLyric': lambda obj: obj.get("tlyric",{}).get("lyric"),
        }
        )
        ],
    "getSongComments" : 
        [("/weapi/v1/resource/comments/%s", NEAPI_METHOD_POST_ENCRYPTED, 
        {
            'CommentsHotComment': lambda obj,n: obj["hotComments"][n],
            'CommentsHotLength' : lambda obj: len(obj["hotComments"]),
            'CommentsComment': lambda obj,n: obj["comments"][n],
            'CommentsLength' : lambda obj: len(obj["comments"]),

            'CommentsMore' : lambda obj: (obj["more"]),
            'CommentsHotMore' : lambda obj: (obj["moreHot"]),
            'CommentsTotalLength' : lambda obj: (obj["total"]),

            'CommentID' : lambda obj: obj['commentId'],
            'CommentContent' : lambda obj: obj['content'],
            'CommentReplyingUsername' : lambda obj: obj['beReplied']['user']['name'],
            'CommentReplyingContent' : lambda obj: obj['beReplied']['content'],
            'isCommentLiked' : lambda obj: obj['liked'],
            'CommentLikedCount' : lambda obj: obj['likedCount'],
            'CommentTime' : lambda obj: time.localtime(obj['time'] / 1000),
            'CommentUsername' : lambda obj: obj['user']['nickname'],
        }
        )
        ],
    "likeSongComment" : 
        [("/weapi/v1/comment/%slike", NEAPI_METHOD_POST_ENCRYPTED, 
        {
        }
        )
        ],
}

CLIENT_TOKEN_TEMP = '''
    1_1UlfKAX7rcMafd1M0ndPFJPGITMgOexy_IZ8ivs4nXAGjweA4z6VEtLdEP143Y5Bg
'''.strip().replace('\n', '')

MODULUS = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
NONCE = '0CoJUm6Qyw8W8jud'
PUBKEY = '010001'
MAGIC_MP3DFS = str('3go8&$8*3*3h0k(2)2')

LOG_FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s [%(filename)s] %(funcName)s (%(lineno)d) : %(message)s')

HTTPLOG_FORMATTER = logging.Formatter('%(asctime)s - %(name)s <%(funcName)s> : %(message)s')

HTTP_BLOCKSIZE =  8192

HEADER_BASE = {'Referer': 'http://music.163.com/','Content-Type':"application/x-www-form-urlencoded"}

tmpDebug = logging.getLogger('Temporary')
tmpDebug.setLevel(logging.WARNING)
#tmpH = logging.Handler()

tmpH = logging.FileHandler("e:\\neteaseDebug2\\tmplog.txt",  mode="w")

tmpH.setFormatter(LOG_FORMATTER)
tmpDebug.addHandler(tmpH)

d = tmpDebug.debug

class NEApiError(Exception):
    def __init__(self, arg):
        Exception.__init__(self)
        self.args = (arg,)

class NEApiNeedCaptcha(NEApiError):
    def __init__(self, arg):
        NEApiError.__init__(self, arg)

class NEApiWrongPassword(NEApiError):
    def __init__(self, arg):
        NEApiError.__init__(self, arg)

class NEApiBlockedByYundun(NEApiError):
    def __init__(self, arg):
        NEApiError.__init__(self, arg)

class NEApiNeedLogin(NEApiError):
    def __init__(self, arg):
        NEApiError.__init__(self, arg)

def SimpleCookie2Str(cookie):
    return ';'.join(map(lambda x,y:'%s=%s'%(x,y.value), cookie.keys(), cookie.values()))

def str2SimpleCookie(inCookie):
    if(isinstance(inCookie, str) or isinstance(inCookie, unicode)):
        if(isinstance(inCookie, unicode)):
            inCookie = inCookie.encode("utf-8")
        elif isinstance(inCookie, str):
            pass
        else:
            raise TypeError, "inCookie should be a str or unicode."
        #Since Python2.5 have a bug on unquoted ExpiresDate String
        inCookie = EXPIREDATE_RE.sub(lambda matched:"Expires=\"%s\";" % matched.group('date'), inCookie)
        inCookie = SimpleCookie(inCookie)
    elif isinstance(inCookie, SimpleCookie):
        pass
    else:
        raise TypeError, 'inCookie must be Headercookie str or SimpleCookie Object'
    return inCookie

def readWriteCallback(readIO, writeIO, callbackFunc, blockSize, totalSize):
    receivedBlocks = 0
    receivedSize = 0
    if callbackFunc:
        #tmpDebug.debug("callback Func: %s %s %s %s" %(receivedBlocks, blockSize, receivedSize, totalSize))
        callbackFunc(receivedBlocks, blockSize, receivedSize, totalSize)

    while True:
        block = readIO.read(blockSize)
        if (not block):
            break
        receivedBlocks += 1
        receivedSize += len(block)
        writeIO.write(block)
        if callbackFunc:
            #tmpDebug.debug("callback Func: %s %s %s %s" %(receivedBlocks, blockSize, receivedSize, totalSize))
            callbackFunc(receivedBlocks, blockSize, receivedSize, totalSize)

def isURLAvailable(url):
    host = url.split("/")[2]
    conn = httplib.HTTPConnection(host, port = 80)
    conn.request("GET", url,None,{})
    resp = conn.getresponse()
    code = resp.status

    available = True
    if code is not 200:
        available = False

    resp.close()
    conn.close()
    return available

def rawHTTP(host, url, method, params, query, header, httpLogger, callback):
    if isinstance(query, dict):
        query = urllib.urlencode(query)
    if query:
        url = url + "?" + query
    httpLogger.info(u'Request URI : %s ; Host : %s' % s(url, host))
    httpLogger.info(u"Request Headers  : %s" % header)
    httpLogger.info(u'Request Body : %s' % s(params))

    if isinstance(params, dict):
        params = urllib.urlencode(params)
    if not isinstance(params, str):
        params = str(params)

    d("Start Connection")
    conn = httplib.HTTPConnection(host, port = 80)
    d("Start Request")
    conn.request(method, url, params, header)
    d("Start Getting Resp")
    resp = conn.getresponse()
    d("End Getting Resp")

    httpLogger.info(u"HeaderMsgs : %s" % resp.msg.dict)

    totalSize = getIOLength(resp)
    httpLogger.info(u'Response Length : %s' % totalSize)
    respBody = StringIO.StringIO()

    readWriteCallback(resp, respBody, callback, HTTP_BLOCKSIZE, totalSize)

    cookie = ''.join(x for x in resp.msg.headers if x.strip().upper().find('SET-COOKIE:') == 0)

    cookie = str2SimpleCookie(cookie)

    httpLogger.info(u'Respose Cookie : %s' % cookie)
    httpLogger.info(u'Response Body : (level 15 for short, level debug for long)')

    result = respBody.getvalue()
    if(len(result) < 1000):
        httpLogger.log(15, result)
    else:
        if httpLogger.handlers  and httpLogger.handlers[0].level < 15:
            httpLogger.debug(result)
    httpLogger.info(u'(Length : %d)' % len(result))
    
    resp.close()
    conn.close()
    respBody.close()
    return (cookie, result)

def getItem(funcList, item, *args):
    obj = item
    for arg in args:
        if not isinstance(arg, tuple):
            arg = (arg,)
        obj = funcList[arg[0]](obj, *arg[1:])
    return obj

class NEEncrypt:
    def __init__(self):
        pass

    def loadParams(self, params):
        self.params = params
        text = json.dumps(params)
        secKey = self._createSecretKey(16)
        encText = self._aesEncrypt(self._aesEncrypt(text, NONCE), secKey)
        encSecKey = self._rsaEncrypt(secKey, PUBKEY, MODULUS)
        self.encryptedData = {
            'params' : encText,
            'encSecKey' : encSecKey
        }

    def loadDfsID(self, dfsID, serverNo = None):
        self.dfsID = dfsID
        self._encDfsID()
        if serverNo == None:
            serverNo = random.randint(1,4)
        self.mp3URL =  "http://p%s.music.126.net/%s/%s.mp3" % (serverNo, self.encryptedDfsID, self.dfsID)

    def getMP3URL(self):
        return self.mp3URL

    def getEncryptedData(self):
        return self.encryptedData

    def _encDfsID(self):
        dfsID = str(self.dfsID)
        encryptedDfsID = ''
        magicLen = len(MAGIC_MP3DFS)
        for i, x in enumerate(dfsID):
            encryptedDfsID += chr(ord(x) ^ ord(MAGIC_MP3DFS[i % magicLen]))
        md5Encryptor = hashlib.md5(encryptedDfsID)
        result = md5Encryptor.digest()

        result = result.encode('base64')[:-1]
        result = result.replace('/', '_')
        result = result.replace('+', '-')

        self.encryptedDfsID = result

    def _aesEncrypt(self, text, secKey):
        pad = 16 - len(text) % 16
        text = text + pad * chr(pad)
        encryptor = AES.new(secKey, 2, '0102030405060708')
        ciphertext = encryptor.encrypt(text)
        ciphertext = base64.encodestring(ciphertext).replace('\n','')
        return ciphertext.decode()

    def _modpow(self, base, exponent, mod):
        ans = 1
        index = 0
        while(1 << index <= exponent):
            if(exponent & (1 << index)):
                ans = (ans * base) % mod
            index += 1
            base = (base * base) % mod
        return ans

    def _rsaEncrypt(self, text, pubKey, modulus):
        text = (''.join(reversed(text))).encode()
        rs = self._modpow(long(binascii.hexlify(text), 16), long(pubKey, 16), long(modulus, 16))
        return ('%x' % rs).zfill(256)

    def _createSecretKey(self, size):
        return ''.join('%x' % random.randint(0, 15) for x in range(size))

class NEApi:
    def __init__(self, config = {}):
        self.config = {}
        self.apiLog = logging.getLogger('APILog.' + hex(id(self))[2:-1])
        self.httpLog = logging.getLogger('HTTPLog.' + hex(id(self))[2:-1])
        self.apiLog.setLevel(logging.DEBUG)
        self.httpLog.setLevel(logging.DEBUG)
        self.cookie = SimpleCookie()
        if config:
            self.updateConfig(config)

        self.logined = False
        self.csrf = ''
        self.needCaptcha = False
        self.captchaID = ''
        self.captcha = ''

    def updateConfig(self, inConfig):
        self.config.update(inConfig)
        if inConfig.has_key("HTTPLogHandler") or inConfig.has_key("LogHandler"):
            self.setLog(self.config["HTTPLogHandler"], self.config["LogHandler"])
        if inConfig.has_key("LoadLocalDataFunc") or inConfig.has_key("WriteLocalDataFunc"):
            self.setLocalDataFunc(self.config["LoadLocalDataFunc"], self.config["WriteLocalDataFunc"])
            self.apiLog.debug("LocalData Read/Write Function Set to be %s/%s." % (self.loadLocalDataFunc, self.writeLocalDataFunc))
            self._loadLocalData()
            d(u"loaded LocalData : %s" % self.localData)
        self.setReadCallback(inConfig.get("readCallback"))

    def _loadLocalData(self):
        self.localData = self.loadLocalDataFunc()
        self._loadCookie()

    def setLocalDataFunc(self, inLoadLocalDataFunc, inWriteLocalDataFunc):
        if not (callable(inLoadLocalDataFunc) or inLoadLocalDataFunc is None):
            raise TypeError, u"inLoadLocalDataFunc is not a callable."
        if not (callable(inWriteLocalDataFunc) or inWriteLocalDataFunc is None):
            raise TypeError, u"inWriteLocalDataFunc is not a callable."
        self.loadLocalDataFunc = inLoadLocalDataFunc
        self.writeLocalDataFunc = inWriteLocalDataFunc
        self._loadLocalData()

    def setClientToken(self, tokenStr):
        self.localData['clientToken'] = tokenStr
        self.writeLocalDataFunc(self.localData)

    def setCookieFile(self, inCookieFile):
        inCookieFile = os.path.abspath(inCookieFile)
        if not os.path.exists(inCookieFile):
            file0 = open(inCookieFile, 'wb')
            file0.close()
        self.cookieFile = inCookieFile
        self.cookie = SimpleCookie()

    def setReadCallback(self, func):
        self.readCallback = func

    def setLog(self, inHTTPLogHandler, inLogHandler):
        if(inHTTPLogHandler):
            inHTTPLogHandler.setFormatter(HTTPLOG_FORMATTER)
            self.httpLog.addHandler(inHTTPLogHandler)
        if(inLogHandler):
            inLogHandler.setFormatter(LOG_FORMATTER)
            self.apiLog.addHandler(inLogHandler)
    
    def setCookie(self, inCookie):
        if not isinstance(inCookie, SimpleCookie):
            inCookie = str2SimpleCookie(inCookie)
        self.cookie = inCookie
        self.apiLog.info(u'Cookie Set : %s' % self.cookie)
        self._loadCSRF()

    def setAndWriteCookie(self, inCookie):
        self.setCookie(inCookie)
        self._writeCookie()

    def updateCookie(self, inCookie):
        inCookie = str2SimpleCookie(inCookie)
        self.cookie.update(inCookie)
        self.apiLog.info(u'Cookie Updated : %s' % self.cookie)
        self._loadCSRF()
        self._writeCookie()

    def _loadCSRF(self):
        # csrfFind = CSRF_RE.findall(inCookie)
        # if csrfFind:
        #     self.csrf = csrfFind[0]
        # uidFind = UID_RE.findall(inCookie)
        # if(uidFind):
        #     self.setUid(uidFind[0])
        if(self.cookie.has_key("__csrf")):
            self.csrf = self.cookie['__csrf'].value;
        else:
            self.csrf = ''
        self.apiLog.info("CSRF Updated : %s" % self.csrf)



    def keepLogined(self, forceRelogin = False):
        if self.needCaptcha:
            self.apiLog.warning(u"Need Captcha for Login, Please verify captcha first.")
        if not forceRelogin:
            checkLoginC, checkLoginR = self._encHTTP(URL_LOGIN_REFRESH, {"csrf_token": self.csrf}, {"csrf_token": self.csrf})
            self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
            checkLoginR = json.loads(checkLoginR)
            self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)            
            if checkLoginR['code'] == 301:
                #not logined
                self.apiLog.info('Refresh Login: not logined.')
            elif checkLoginR['code'] == 200:
                self.apiLog.info('Refresh Login: logined.')
                #update cookie
                self.updateCookie(checkLoginC)
                self.logined = True
                return
            else:
                raise NEApiError, u"%s returned code %s" % (URL_LOGIN_REFRESH, checkLoginR['code'])

        self.logined = False
        self.login()

    def login(self):
        md5Encoder = hashlib.md5(self.config["password"].encode())
        encodedPassword = md5Encoder.hexdigest()

        if not self.config["isPhone"]:
            loginDict = {
                'username' : self.config["username"],
                'password' : encodedPassword,
                'rememberLogin' : 'true',
                'csrf_token' : self.csrf,
                'clientToken' : noneThen(self.localData['clientToken'],"")
            }
            loginURL = URL_LOGIN_EMAIL
        else:
            loginDict = {
                'phone' : self.config["cellphone"],
                'password' : encodedPassword,
                'rememberLogin' : 'true',
                'csrf_token' : self.csrf
            }
            loginURL = URL_LOGIN_PHONE

        loginC, loginR = self._encHTTP(loginURL, loginDict, {"csrf_token" : self.csrf})
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        loginR = json.loads(loginR)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)    
        

        if loginR['code'] == 415:
            #IP高频
            self.needCaptcha = True
            self.captchaID = loginR['captchaId']
            raise NEApiNeedCaptcha("IP Blocked. Please verify captcha.")
            
        if loginR['code'] == 200:
            self.logined = True
            self.updateCookie(loginC)
            self.setLocalDataItem("userProfile", loginR["profile"])

        if loginR['code'] == 502:
            raise NEApiWrongPassword("Login Failed for wrong username or password.")

        if loginR['code'] == 461:
            raise NEApiBlockedByYundun, "Blocked by yundun. Please change ClientToken."

    def getCaptchaURL(self):
        return u"%s?%s"%(URL_PROTOCOL + URL_HOST + URL_CAPTCHA_IMAGE,urllib.urlencode({'id' : self.captchaID}))
    
    def getCaptchaID(self):
        return self.captchaID

    def sendCaptcha(self, inputCapt):
        self.captcha = inputCapt
        captchaData = {'id' : self.captchaID, 'captcha': inputCapt}
        captchaC, captchaR = self._encHTTP(URL_CAPTCHA_SUBMIT, captchaData, {"csrf_token" : self.csrf})
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        captchaR = json.loads(captchaR)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        if captchaR['result']:
            self.needCaptcha = False
        

    def _myHTTP(self, url, method = 'GET', params = '', query  = '', header = {}):
        newHeader = HEADER_BASE
        newHeader['Cookie'] = SimpleCookie2Str(self.cookie)
        newHeader.update(header)
        return rawHTTP(URL_HOST, url, method, params, query, newHeader, self.httpLog, self.config.get("readCallback"))

    def _encHTTP(self, url, params = {'' : ''}, query = {}, header = {}):
        self.httpLog.info('Encrypted Data : %s' % urllib.urlencode(params))
        neEncryptor = NEEncrypt()
        neEncryptor.loadParams(params)
        encParams = neEncryptor.getEncryptedData()

        return self._myHTTP(url, 'POST', encParams, query, header)

    def _mySubmit(self, APIURL, params, *urlFormat):
        url = APIURL[0]
        if urlFormat:
            self.apiLog.debug("urlFormat : " + str(urlFormat))
            url = url % urlFormat
            self.apiLog.debug("url after formatting : " + str(url))
            
        csrfParam = {'csrf_token' : self.csrf}
        postParams = csrfParam.copy()
        getQuery = csrfParam.copy()
        if APIURL[1] == NEAPI_METHOD_GET:
            getQuery.update(params)
            return self._myHTTP(url, 'GET', {}, getQuery, {})
        if APIURL[1] == NEAPI_METHOD_POST_NORMAL:
            postParams.update(params)
            return self._myHTTP(url, 'POST', postParams, getQuery, {})
        if APIURL[1] == NEAPI_METHOD_POST_ENCRYPTED:
            postParams.update(params)
            return self._encHTTP(url, postParams, getQuery, {})
        if APIURL[1] == NEAPI_METHOD_GET_AND_POST_ENCRYPTED:
            postParams.update(params[1])
            getQuery.update(params[0])
            return self._encHTTP(url, postParams, getQuery, {})

    def _loadCookie(self):
        # file1 = open(self.cookieFile, 'r')
        # cookie = file1.read()
        # cookie = SimpleCookie(cookie)
        # self.setCookie(cookie)
        # file1.close()
        cookie = str2SimpleCookie(self.localData['cookie'])
        self.setCookie(cookie)
        d(u"loaded Cookie : %s" % self.cookie)

    def _writeCookie(self):
        # file1=open(self.cookieFile,'wb')
        # file1.write(self.cookie.output())
        # file1.close()
        self.localData['cookie'] = self.cookie.output()
        self.writeLocalDataFunc(self.localData)

    def setLocalDataItem(self, key, value):
        self.localData[key] = value
        self.writeLocalDataFunc(self.localData)

    
    def getUserSonglistList(self, uid = 0, offset = 0, limit = 1000):
        """
            Get ALL songlists of this user.
            Old API: limit can't be zero or negative.
            when UID is zero, returns current user's songlists.
        """
        #get current function name getUserSonglistList
        #URL_NEAPIS includes its URL and API, stored in key named after this function
        currAPIVersion = self.config['apiVersion']
        currAPIURL = URL_NEAPIS[sys._getframe().f_code.co_name]
        currAPIURL = currAPIURL[min(currAPIVersion, len(currAPIURL) - 1)]
        currDict = {
            'offset' : offset,
            'limit' : limit,
            'uid' : uid,
        }

        currC, currR = self._mySubmit(currAPIURL, currDict)
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        currR = json.loads(currR)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        self.updateCookie(currC)
        self.checkCode(currR['code'])

        return currR, currAPIURL[2]

    def getRecommendationSonglist(self, limit = 20, offset = 0, total = True):
        """
            Get User's daily recommendation songlist.
        """
        currAPIVersion = self.config['apiVersion']
        currAPIURL = URL_NEAPIS[sys._getframe().f_code.co_name]
        currAPIURL = currAPIURL[min(currAPIVersion, len(currAPIURL) - 1)]
        currDict = {
            'limit' : limit,
            'offset': offset,
            'total' : total
        }

        currC, currR = self._mySubmit(currAPIURL, currDict)
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        currR = json.loads(currR)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        self.updateCookie(currC)
        self.checkCode(currR['code'])

        return currR, currAPIURL[2]

    def getFMSonglist(self, limit = 3):
        """
            Get User's daily recommendation songlist.
        """
        currAPIVersion = self.config['apiVersion']
        currAPIURL = URL_NEAPIS[sys._getframe().f_code.co_name]
        currAPIURL = currAPIURL[min(currAPIVersion, len(currAPIURL) - 1)]
        currDict = {
            'limit' : limit,
        }

        currC, currR = self._mySubmit(currAPIURL, currDict)
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        currR = json.loads(currR)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        self.updateCookie(currC)
        self.checkCode(currR['code'])

        return currR, currAPIURL[2]

    def NE_likeFMSong(self, songID, alg = "itembased", like = True, atSecond = "-1"):
        """
            Like a song in FM. Netease Music Limited
        """
        currAPIVersion = self.config['apiVersion']
        currAPIURL = URL_NEAPIS[sys._getframe().f_code.co_name]
        currAPIURL = currAPIURL[min(currAPIVersion, len(currAPIURL) - 1)]
        currDict = {
            'alg' : alg,
            'like': repr(like).lower(),
            'time': atSecond,
            'trackId': songID
        }

        currC, currR = self._mySubmit(currAPIURL, currDict)
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        currR = json.loads(currR)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        self.updateCookie(currC)
        self.checkCode(currR['code'])

        return currR, currAPIURL[2]

    def NE_trashFMSong(self, songID, alg = "itembased", atSecond = "-1"):
        """
            Trash a song in FM. Netease Music Limited
        """
        currAPIVersion = self.config['apiVersion']
        currAPIURL = URL_NEAPIS[sys._getframe().f_code.co_name]
        currAPIURL = currAPIURL[min(currAPIVersion, len(currAPIURL) - 1)]
        currDict = {
            'alg' : alg,
            'time': atSecond,
            'songId': songID
        }

        currC, currR = self._mySubmit(currAPIURL, currDict)
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        currR = json.loads(currR)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        self.updateCookie(currC)
        self.checkCode(currR['code'])

        return currR, currAPIURL[2]

    def getSonglist(self, songlistID, limit = 1000, offset = 0, total = False):
        """
            get the songs in a songlist by its id
        """
        currAPIVersion = self.config['apiVersion']
        currAPIURL = URL_NEAPIS[sys._getframe().f_code.co_name]
        currAPIURL = currAPIURL[min(currAPIVersion, len(currAPIURL) - 1)]
        currDict = {
            'id' : songlistID,
            'limit': limit,
            'n' : limit,
            'offset' : offset,
            'total' : total,
        }

        currC, currR = self._mySubmit(currAPIURL, currDict)
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        currR = json.loads(currR)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        self.updateCookie(currC)
        self.checkCode(currR['code'])

        return currR, currAPIURL[2]

    def getAlbum(self, albumID):
        """
            get the songs in a album by its id
        """
        currAPIVersion = self.config['apiVersion']
        currAPIURL = URL_NEAPIS[sys._getframe().f_code.co_name]
        currAPIURL = currAPIURL[min(currAPIVersion, len(currAPIURL) - 1)]
        currDict = {
        }
        #modify in arguments
        currC, currR = self._mySubmit(currAPIURL, currDict, albumID)
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        currR = json.loads(currR)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        self.updateCookie(currC)
        self.checkCode(currR['code'])

        return currR, currAPIURL[2]

    def NE_subscribeSonglist(self, songlistID):
        """
            favorite/subscribe songlist created by another user.
            Netease Limited
        """
        currAPIVersion = self.config['apiVersion']
        currAPIURL = URL_NEAPIS[sys._getframe().f_code.co_name]
        currAPIURL = currAPIURL[min(currAPIVersion, len(currAPIURL) - 1)]
        currDict = {
            'id' : songlistID,
        }

        currC, currR = self._mySubmit(currAPIURL, currDict)
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        currR = json.loads(currR)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        self.updateCookie(currC)
        self.checkCode(currR['code'])

        return currR, currAPIURL[2]

    def getSongs(self, songIDList):
        """
            get details of the songs by their ids.
            songIDList: a list that includes ids.
            the order of response is sorted to be consistent with songIDList
        """
        for i, songID in enumerate(songIDList):
            if not isinstance(songID, str):
                songIDList[i] = str(songID)

        currAPIVersion = self.config['apiVersion']
        #currAPIVersion = 0
        currAPIURL = URL_NEAPIS[sys._getframe().f_code.co_name]
        currAPIURL = currAPIURL[min(currAPIVersion, len(currAPIURL) - 1)]
        if currAPIVersion == 0:
            currDict = {
                'ids' : repr(songIDList).replace(" ", "").replace("'", "").replace("\"", ""),
            }
        if currAPIVersion == 1:
            currDict = {
                #'c' : json.dumps([{ "ids" : songIDList}]).replace(" ", ""),
                'ids' : repr(songIDList).replace(" ", "").replace("'", "").replace("\"", ""),
                #'c' : json.dumps([{ "id" : [int(x) for x in songIDList]}]).replace(" ", ""),
            }

        currC, currR = self._mySubmit(currAPIURL, currDict)
        #print currR
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        currR = json.loads(currR)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        self.updateCookie(currC)
        self.checkCode(currR['code'])
#modify
        sortedData = range(len(songIDList))
        for song in currR['songs']:
            sortedData[songIDList.index(str(song['id']))] = song

        for i, song in enumerate(sortedData):
            if isinstance(song, int):
                sortedData[i] = {}
                #raise NEApiError, "not all songdetails are responsed back here."

        currR['songs'] = sortedData
        return currR, currAPIURL[2]

    def getSongsURL(self, songIDList, br):
        """
            get URLs of songs by their ids
            songIDList: a list that includes ids.
            br: one of 'b' 'l' 'm' 'h' or 0 1 2 3
            sorted to be consistent with songIDList
        """
        for i, songID in enumerate(songIDList):
            if not isinstance(songID, str):
                songIDList[i] = str(songID)
        self.apiLog.info("songIDList : %s" % repr(songIDList))
        
        if isinstance(br, int):
            br = NEAPI_BRS[br][0]
        currAPIVersion = self.config['apiVersion']
        currAPIURL = URL_NEAPIS[sys._getframe().f_code.co_name]
        currAPIURL = currAPIURL[min(currAPIVersion, len(currAPIURL) - 1)]

        currDict = {
            'ids' : repr(songIDList).replace(" ", "").replace("'", "").replace("\"", ""),
            'br' : dict(NEAPI_BRS)[br]
        }

        currC, currR = self._mySubmit(currAPIURL, currDict)
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        currR = json.loads(currR)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        self.updateCookie(currC)
        self.checkCode(currR['code'])

        sortedData = range(len(songIDList))
        self.apiLog.info("songIDList : %s" % repr(songIDList))
        for song in currR['data']:
            sortedData[songIDList.index(str(song['id']))] = song

        currR['data'] = sortedData
        return currR, currAPIURL[2]
        

    def getSongsURL_direct(self, songIDList, br, **kwargs):
        """
            DIRECT_FUNCTION
            get URLs of songs by their ids
            songIDList: a list that includes ids.
            br: one of 'b' 'l' 'm' 'h'
        """

        # url will be None when getting URL by WEAPI
        urlList = [None] * len(songIDList)
        if not kwargs.get('forceOldAPI'):
            urlListR, urlListFunc = self.getSongsURL(songIDList, br)
            urlListU = getItem(urlListFunc, urlListR, "urls")
            for i,x in enumerate(urlListU):
                if x is not None:
                    urlList[i] = x
                    pass

        try:
            haveNone = urlList.index(None)
        except ValueError:
            haveNone = -1

        if haveNone != -1:
            #use old api + album + mp3enckey to get
            if kwargs.has_key("songDict"):
                songDict = kwargs["songDict"]
            else:
                songDict, songDictFunc = self.getSongs(songIDList)
                songDict = songDict["songs"]

            mp3URLEncryptor = NEEncrypt()
            for urlI, url in enumerate(urlList):
                if url is None:
                    # get url by album
                    if songDict[urlI].has_key("al"):
                        albumID = songDict[urlI]["al"]["id"]
                    elif songDict[urlI].has_key("album"):
                        albumID = songDict[urlI]["album"]["id"]
                    else:
                        raise ValueError, "No album info in songDict"
                    backupAPIVersion = self.config['apiVersion']
                    self.config['apiVersion'] = 0
                    album, albumFunc = self.getAlbum(albumID)
                    self.config['apiVersion'] = backupAPIVersion
                    brNum = [y[0] for y in (NEAPI_BRS)].index(br)

                    try:
                        albumSongsID = getItem(albumFunc, album, "albumSongsID")
                        albumSongsDfsID = getItem(albumFunc, album, "albumSongsID2")
                        albumSongIndex = albumSongsID.index(int(songIDList[urlI]))
                    except KeyError:
                        self.apiLog.error("song %s keyerror ! " % songIDList[urlI])
                        continue

                    self.apiLog.info("albumSongsDfsID : " + repr(albumSongsID))
                    availableDfsIDURL = []
                    for i, dfsID in enumerate(albumSongsDfsID[albumSongIndex]):
                        if dfsID is not None:
                            mp3URLEncryptor.loadDfsID(int(dfsID))
                            thisURL = mp3URLEncryptor.getMP3URL()
                            if isURLAvailable(thisURL):
                                availableDfsIDURL.append(thisURL)
                            else:
                                availableDfsIDURL.append(None)               
                        else:
                            availableDfsIDURL.append(None)
                    self.apiLog.info("availableDfsIDURL : %s" % (availableDfsIDURL,))
                    
                    availableBrs = [i for i, entry in enumerate(availableDfsIDURL) if entry is not None]

                    if availableBrs == []:
                        self.apiLog.error("No available DFSID-encrypted URL for Song %s !!" % songIDList[urlI])
                        continue

                    closestSelector = [abs(i - brNum) for i in availableBrs]
                    closestBrNumIndex = closestSelector.index(min(closestSelector))
                    closestBrNum = availableBrs[closestBrNumIndex]
                    self.apiLog.info("availableBrs : " + str(availableBrs))
                    self.apiLog.info("closestSelector : " + str(closestSelector))
                    self.apiLog.info("closestBrNumIndex : " + str(closestBrNumIndex))
                    self.apiLog.info("closestBrNum : " + str(closestBrNum))

                    if closestBrNum >= len(albumSongsDfsID):
                        continue
                    
                    urlList[urlI] = availableDfsIDURL[closestBrNum]
                    
        self.apiLog.info("All urls: " + json.dumps(urlList))
        return urlList

    def getLyric(self, songID):
        """
            Get lrc-typed lyric.
        """
        currAPIVersion = self.config['apiVersion']
        currAPIURL = URL_NEAPIS[sys._getframe().f_code.co_name]
        currAPIURL = currAPIURL[min(currAPIVersion, len(currAPIURL) - 1)]
        currDict = {
        }
        currQuery = {
            'id' : songID,
            'lv' : -1,
            'kv' : -1,
            'tv' : -1,
        }

        currC, currR = self._mySubmit(currAPIURL, (currQuery, currDict))
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        currR = json.loads(currR)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        self.updateCookie(currC)
        self.checkCode(currR['code'])

        return currR, currAPIURL[2]

    def getSongComments(self, songID, limit = 10, offset = 0,  total = False):
        """
            Get comments of a song
        """
        currAPIVersion = self.config['apiVersion']
        currAPIURL = URL_NEAPIS[sys._getframe().f_code.co_name]
        currAPIURL = currAPIURL[min(currAPIVersion, len(currAPIURL) - 1)]

        rid = "R_SO_4_%s" % songID

        currDict = {
            "limit" : limit,
            "offset" : offset,
            "rid" : rid,
            "total" : total,
        }

        currC, currR = self._mySubmit(currAPIURL, currDict, rid)
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        currR = json.loads(currR)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        self.updateCookie(currC)
        self.checkCode(currR['code'])

        return currR, currAPIURL[2]

    def likeSongComment(self, commentID, songID, like = True):
        """
            Like/unlike a comment of a song
        """
        currAPIVersion = self.config['apiVersion']
        currAPIURL = URL_NEAPIS[sys._getframe().f_code.co_name]
        currAPIURL = currAPIURL[min(currAPIVersion, len(currAPIURL) - 1)]

        rid = "R_SO_4_%s" % songID

        currDict = {
            "commentID" : commentID,
            "threadID" : rid,
            "like" : repr(like).lower()
        }

        currC, currR = self._mySubmit(currAPIURL, currDict, ("un","")[like])
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        currR = json.loads(currR)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        self.updateCookie(currC)
        self.checkCode(currR['code'])
        #liking a liked comment will cause 400 error

        return currR, currAPIURL[2]

    def checkCode(self, code):
        if code == 301:
            self.logined = False
            raise NEApiNeedLogin, u"Login status has expired or you haven't logined. Please log in again."

        if code == 200:
            pass
        elif code == 400:
            raise NEApiError, u"Illegal Operation!"
        
        return

    def compat_getComments(self, songId, commentThreadId = '_', offset=0, total=False, limit=10):
        #此处commentThreadId赋值为R_AL_3_XXX之类的可以获取其他种类的评论(歌手/专辑/歌单)
        if commentThreadId == '_':
            commentThreadId = 'R_SO_4_%s' % songId
        commUrl = '/weapi/v1/resource/comments/%s' % commentThreadId
        commReq = {
            'offset' : offset,
            'total' : total,
            'limit' : limit
        }
        (commCookie, commResult) = self._encHTTP(commUrl, commReq)
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        commResult = json.loads(commResult)
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        hotCommList = commResult.get('hotComments')
        ordCommList = commResult.get('comments')
        totalNum = commResult.get('total')
        haveMore = commResult.get('more')
        return (hotCommList, ordCommList, totalNum, haveMore)
    
    def compat_favorComment(self, commentId, threadId, favor = True):
        #必须提供threadId，否则按默认的歌曲来
        favorReq = {
        'commentId' : commentId,
        'threadId' : threadId,
        'like' : repr(favor).lower(),
        "csrf_token" : self.csrf
        }

        favorUrl = '/weapi/v1/comment/%slike' % ('un','')[favor]
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        favorResult = json.loads(self._encHTTP(favorUrl, favorReq)[1])
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        message = u''
        favorSuc = False
        if 'message' in favorResult:
            message = favorResult['message']
        else:
            message = str(favorResult.get('code'))
            if favorResult.get('code') == 200:
                favorSuc = True
        return (favorSuc, message)

    #1 单曲
    #10 专辑
    #100 歌手
    #1000 歌单
    #1002 用户
    def compat_search(self, keyword, type, limit=10, offset=0):
    #待改进API，旧的API只能显示10条

        searchReq = {
        's' : keyword,
        'type' : type,
        'limit' : limit,
        'offset' : offset
        }
        searchURL = '/api/search/get'
        self.apiLog.info("%s Json Loads Begin", sys._getframe().f_code.co_name)
        searchResult = json.loads(self._myHTTP(searchURL, 'POST', urllib.urlencode(searchReq))[1])['result']
        self.apiLog.info("%s Json Loads End", sys._getframe().f_code.co_name)
        
        return searchResult
