# coding=utf-8
import sys
import os
import time
import socket

import neapi
import random
import ujson as json
import re
import logging

try:
    import cfileman
except ImportError:
    pass

from tools import s, us, out

#提取有用歌词的正则表达式
#先寻找一个以 [ + 非数字开头的标签框 如[ar:XX] 即\[\D[^\]]*\]
#然后匹配0或任意数量个\n
RE_LYRICLINE = re.compile('\[\D[^\]]*\][\n]*(\[\d.*)',re.DOTALL)
RE_LYRICLINE_BETA = re.compile('\[[\d`\:\.]*\].*',re.MULTILINE)
 

def procLyric(inLyric, testParam = False):
    #先用正则将没用的部分去掉，并用\n分割，留下纯歌词

    trimLrc = RE_LYRICLINE.findall('[mark]' + inLyric)[0].split(u'\n')

    lrcList = []
    for lrcLine in trimLrc:
        z = lrcLine.split(u']')
        if len(z) > 1:
            for i in range(0,len(z)-1):
                t = z[i][1:]
                #处理时间，有00:00.920和00:00.92两种格式
                t1 = t.split(u':')
                t2 = t1[1].split('.')
                minute = int("0" + t1[0])
                sec = int("0" + t2[0])
                msc = t2[1]
                if len(msc) == 2:
                    msc = int("0" + msc) * 10
                else:
                    msc = int("0" + msc)
                totaltime = ((minute*60000) + (sec*1000) + msc)
                lrcList.append(( totaltime , [z[len(z)-1] , ''] ))
    return lrcList
    
def procTLyric(lrcDict, inTLyric, testParam = False):
    
    trimTLrc = RE_LYRICLINE.findall('[mark]' + inTLyric)[0].split(u'\n')

    for lrcLine in trimTLrc:
        z = lrcLine.split(u']')
        if len(z) > 1:
            for i in range(0,len(z)-1):
                t = z[i][1:]
                #处理时间，有00:00.920和00:00.92两种格式
                t1 = t.split(u':')
                t2 = t1[1].split('.')
                min = int("0" + t1[0])
                sec = int("0" + t2[0])
                msc = t2[1]
                if len(msc) == 2:
                    msc = int("0" + msc) * 10
                else:
                    msc = int("0" + msc)
                totaltime = ((min*60000) + (sec*1000) + msc)
                if totaltime in lrcDict:
                    lrcDict[totaltime][1] = z[len(z)-1]
    return lrcDict

def sortLyric(lrcDict):
    # lrcDictKeySorted = list(lrcDict)
    # lrcDictKeySorted.sort()
    # lrcDictVarSorted = map(lambda x:lrcDict[x], lrcDictKeySorted)
    # lrcList = map(lambda x,y:(x,y) , lrcDictKeySorted, lrcDictVarSorted)
    return sorted(lrcDict.items())

#PlayList的任务是对一个指定的网易云歌曲List(如[0,2,3,4,5])进行播放
class Playlist:
    def __init__(self, playlist, apii, order=0, picsize=73, br='m', volume=1, debugMode = False, logH = None, lyricPathFormat = "e:\\%s", picPathFormat = "e:\\%s", songPathFormat="e:\\%s_%s"):
        self.logs = logging.getLogger("Playlist_" + hex(id(self)))
        if logH is not None:
            self.logs.addHandler(logH)
        self.logs.setLevel(logging.DEBUG)

        #该playlist用的api实例
        self.api = apii if apii else neapi.NEApi({})
        #0 - 列表循环  1 - 单曲循环  2 - 随机播放
        self.order = order
        self.br = br
        self.volume = volume
        #将来可能要实现历史播放功能
        self.historyList = []
        #更新songList，同时获得其详细信息listDetail，并根据order生成playingList
        #若电台或稍后更新playlist，可设置为[]
        self.updateList(playlist)

        self.lyricPathFormat = lyricPathFormat
        self.picPathFormat = picPathFormat
        self.songPathFormat = songPathFormat

        #downCallback: 下载文件时候的callback
        #downCallbackWrapper: 下载文件时候的callback的Wrapper，在主程序中给其赋值一个函数，downCallbackWrapper('提示文字')(chunknum,chunksize,totalsize)为urlretreive的回调方式
        #songCallback: self.player的播放状态发生变化时调用的callback
        self.downCallbackWrapper = lambda a:lambda b,c,d:None
        self.writeCallbackWrapper = lambda a:lambda b,c,d:None
        self.songCallback = lambda a,b,c:None
        #设置界面所需的专辑图片尺寸，默认为73
        self.picSize = picsize
        self.isScroll = False
        self.logs.info('End Init Playlist')
        self.playCallback = lambda:None
        self.errCallback = lambda:None
        self.player = False
        self.playlistName = s('歌单')
        self.debugMode = debugMode
        
        #初始参数设置完成
        
    def setPlaylistName(self, name):
        self.playlistName = name
        
    def updateList(self, newList):
        #songList: 输入时的歌单(歌曲Id的数组)，按照默认排序
        self.songList = newList
        self.initOrder()
        if self.songList != []:#非电台模式下（有歌曲），用api中的方法获取各歌曲信息
            procResult, procFunc = self.api.getSongs(self.songList)
            self.listdetail = procResult['songs']
            self.listFunc = procFunc
            self.getDownloadUrls(self.br)
        else:
            self.listdetail = []
            self.listdown = []
            #电台怎么办？
        self.logs.info('End Update List')
    
    def updateListByDict(self, listDict, listFunc):
        #输入已经获得的歌曲详情列表Dict来更新
        self.songList = [x['id'] for x in listDict]
        self.initOrder()
        self.listFunc = listFunc
        if self.songList != []:
            self.listdetail = listDict
            
            # self.listdown = [x['url'] for x in self.api.getSongsDetail(self.songList)]
            self.getDownloadUrls(self.br)
        else:
            self.listdetail = []
            self.listdown = []
        self.logs.info('End Update List By Dict')
            
    def getDownloadUrls(self, br):
        self.listdown = self.api.getSongsURL_direct(self.songList, self.br)
        self.logs.info('End Get Urls')
            
    def initOrder(self, order = -1):
        self.currPos = 0
        #playingIndex: 在实际播放列表playingList中的索引号
        #songIndex: 在当前输入的列表songList中的索引号（初始置为-1）
        self.playingIndex = 0
        self.songIndex = 0
        #playingList: 播放时依次对应于该播歌曲在songList中的索引组成的数组，由数字组成
        #默认状态下为[0,1,...n-1]
        if order==-1:
            order = self.order
        else:
            self.order = order
        self.playingList = range(len(self.songList))
        if self.order == 2:
            #随机播放状态下，打乱playingList的次序
            random.shuffle(self.playingList)
            
    def updateOrder(self, order = -1):
        if order==-1:
            order = self.order
        else:
            self.order = order
        self.playingList = range(len(self.songList))
        if self.order == 0 or self.order == 1:
            self.playingIndex = self.songIndex
        if self.order == 2:
            self.playingIndex = 0
            random.shuffle(self.playingList)

    def fetchLyric(self, songId):
        self.logs.info('Start Fetching Lyric')
        #根据songId获取歌词，生成一个{毫秒数:(歌词, 歌词翻译)}的lrcList
        
        # lrcPath ='e:\\netease\\lyric\\%s.txt' % songId
        lrcPath = os.path.self.lyricPath % songId
        lrcPath = os.path.abspath(lrcPath)
        if os.path.exists(lrcPath):
            file1 = open(lrcPath,'r')
            lyricResult = json.loads(file1.read())
            file1.close()
        else:
            lyricR, lyricFunc = self.api.getLyric(songId)
            self.logs.info(u'End Get Lyric')
            file2 = open(lrcPath,'wb')
            file2.write(json.dumps(lyricR))
            file2.close()
            lyricResult = lyricR
        lyric  = False
        tLyric  = False
        isScroll = False
        self.lyric = ''

        lyricFunc = neapi.URL_NEAPIS["getLyric"][0][2]
        lyric = neapi.getItem(lyricFunc, lyricResult, "lyric")
        tLyric = neapi.getItem(lyricFunc, lyricResult, "translatedLyric")
        
        if lyric:
            self.lyric = lyric
            lrcList = procLyric(lyric)
            if lrcList == []:
                #无标签，解析不能，注意，此时和“纯音乐”等情况一样，返回的hasLyric并非一个list而是一个string
                return (lyric, lrcPath, isScroll)
            else:
                isScroll = True
                lrcDict = dict(lrcList)
                if tLyric:
                    lrcDict = procTLyric(lrcDict, tLyric)
                lrcList = sortLyric(lrcDict)
        else:
            #无歌词，解析不能
            if 'nolyric' in lyricResult and lyricResult['nolyric']:
                lrcList = '纯音乐，请欣赏'
            else:
                lrcList = '暂时没有歌词'
        self.logs.info(u'End Analyse Lyric')
        
        return (lrcList, lrcPath, isScroll)
        
    def getCurrLyric(self):
        #微秒转毫秒
        #如果是非滚动歌词，直接return 错误码-2
        if not self.isScroll:
            return -2
        if self.player.state() == audio.EPlaying:
            currPos = self.player.current_position() / 1000
        else:
            if self.currPos != -1:
                currPos = self.currPos / 1000
            else:
                return -1
        #currLI: 当前的歌词句子的索引i，为[0,1,2,3,...歌词句子数-1]中
        #currLT: 当前的歌词句子应对应的时间（毫秒数）
        currLI = -1
        for i, t in enumerate(self.lrcList):
            if currPos >= t[0]:
                currLI = i
        return currLI
            
    def fetchPic(self, size = -1):
        if size == -1:
            size = self.picSize
        self.logs.info('Start Fetching Pic')
        #根据当前播放的歌曲，返回专辑图片的路径，有必要时下载
        
        picPath = self.picPathFormat % neapi.getItem(self.listFunc, self.listdetail[self.songIndex], "songAlbumID")
        picPath = os.path.abspath(picPath)

        if not os.path.exists(picPath):
            picUrl = neapi.getItem(self.listFunc, self.listdetail[self.songIndex], "songAlbumCoverURL") + '?param=%iy%i' % (size, size)
            self.logs.info('Start Downloading Pic at %s to %s' % (picUrl, picPath))
            strList = [ s('下载专辑图片 ') + s(neapi.getItem(self.listFunc, self.listdetail[self.songIndex], "songAlbumName")) , s('目标: ') + s(picPath.split('\\')[-1]) ]
            strList2 = [ s('写入文件') ]
            download(picUrl, picPath, self.downCallbackWrapper(strList), self.errCallback, self.writeCallbackWrapper(strList2))
        self.logs.info( 'End Fetching Pic' )
        return picPath
        
    def fetchPicImage(self):
        picImage = 1
        try:
            picImage = graphics.Image.open(self.fetchPic())
            return picImage
        except Exception, e:
            del picImage
            self.logs.error("%s: %s", e.__class__, e.args)
            try:
                if os.path.exists(self.picPathFormat):
                    os.remove(self.picPathFormat)
            except Exception, e:
                self.logs.error("%s: %s", e.__class__, e.args)
            return graphics.Image.open(os.path.abspath('.\\pic\\pic.bmp')).resize((self.picSize,self.picSize))
        
    def fetchSong(self):
        #根据当前播放的歌曲，返回音频文件的路径，有必要时下载
        self.logs.info('Start Fetching Song')
        songPath = self.songPathFormat % (neapi.getItem(self.listFunc, self.listdetail[self.songIndex], "songID"), self.br)
        songPath = os.path.abspath(songPath)
        if not os.path.exists(songPath):
            strList = [s('下载歌曲 ') + s(neapi.getItem(self.listFunc, self.listdetail[self.songIndex], "songName") ), s('目标') + s(songPath.split('\\')[-1])]
            strList2 = [ s('写入文件') ]
            download(self.listdown[self.songIndex], songPath, self.downCallbackWrapper(strList), self.errCallback, self.writeCallbackWrapper(strList2))
        self.logs.info('End Fetching Song')
        return songPath
        
    def saveSong(self):
        try:
            songDict = self.listdetail[self.songIndex]
            prompt = s('')
            if not os.path.exists(self.songPath):
                self.songPath = self.fetchSong()
            
            if os.path.exists(self.songPath):
                desPath = self.saveSongPathFormat % (s(neapi.getItem(self.listFunc, songDict, "songName")), s(','.join(neapi.getItem(self.listFunc, self.listdetail[self.songIndex], "songArtistsID"))))
                desPath = s(desPath)
                orgPath = s(self.songPath)
                cfileman.FileMan().file_copy(orgPath, desPath, cfileman.EOverWrite)
                prompt += s('创建了') + s(os.path.abspath((desPath).encode("utf-8"))) + s('(') + s(str(dict(neapi.NEAPI_BRS)[self.br] / 1000)) + s('Kbps)')
            else:
                return False
            if self.lyric:
                desPath = self.saveLyricPathFormat % (s(neapi.getItem(self.listFunc, songDict, "songName")), s(','.join(neapi.getItem(self.listFunc, self.listdetail[self.songIndex], "songArtistsID"))))
                desPath = s(desPath).encode("utf-8")
                f = os.open(desPath , os.O_WRONLY|os.O_CREAT)
                os.write(f, s(self.lyric).encode("utf-8"))
                os.close(f)
                prompt += s('和') + s(os.path.basename(desPath))
            resp = out(prompt)
            self.logs.info(prompt)
            
        except Exception, e:
            try:
                os.close(f)
            except:
                pass
            raise e
            
        
    def play(self, songDict):
        #输入歌曲对应的json数据来执行播放
        lrcList, lrcPath, isScroll = self.fetchLyric(neapi.getItem(self.listFunc, songDict, "songID"))
        self.currPos = 0
        self.lrcList = lrcList
        self.lrcPath = lrcPath
        self.isScroll = isScroll
        
        try:
            self.picPathFormat = self.fetchPic()
            self.songPath = self.fetchSong()
            self.player = audio.Sound.open(self.songPath)
            self.player.set_volume(self.volume)
            self.player.play(callback=self.songCallback)
            self.logs.info(u'Max Volume: '+unicode(self.player.max_volume()))
        except Exception, e:
            self.logs.error("%s: %s", e.__class__, e.args)
            if self.player:
                self.player.close()
            try:
                if os.path.exists(self.songPath):
                    os.remove(self.songPath)
            except Exception, e:
                self.logs.error("%s: %s", e.__class__, e.args)
            raise e
            # appuifw.app.set_exit()

        self.playCallback()
        
    # def playDebug(self, songDict):
    #     #输入歌曲对应的json数据来执行播放
    #     lrcList, lrcPath, isScroll = self.fetchLyric(songDict['id'])
    #     self.currPos = 0
    #     self.lrcList = lrcList
    #     self.lrcPath = lrcPath
    #     self.isScroll = isScroll
        
    #     self.logs.info('Current PlayingList')
    #     self.logs.info(str(self.playingList))
    #     self.logs.info('Current SongList')
    #     self.logs.info(s(u', '.join([s(x['name']) for x in self.listdetail])))
    #     self.logs.info('playingIndex: ' + str(self.playingIndex))
    #     self.logs.info('songIndex: ' + str(self.songIndex))
    #     self.logs.info('Name: ' + s(songDict['name']))

    #     self.playCallback()
        
    def playIndex(self, songIndex):
        #输入歌曲在songList中的Index，调用play来执行播放
        self.logs.info('songIndex ' + str(songIndex))
        if self.debugMode:
            self.playDebug(self.listdetail[songIndex])
        else:
            self.play(self.listdetail[songIndex])
        
    def pickupPlay(self, songIndex):
        #在播放列表中挑取一首歌曲播放，目前没有看出和playIndex的区别
        
        self.songIndex = songIndex
        if self.order == 0 or self.order == 1:
            self.playingIndex = self.songIndex
        self.playIndex(self.songIndex)
        
    def firstSong(self):
        self.songIndex = self.playingList[self.playingIndex]
        # if self.order != 2:
            # self.mappedsongIndex=self.songIndex
        self.playIndex(self.songIndex)
        
    def next(self, manual=False):
        #切下一首歌，manual==True时，单曲循环也下一首
        if self.order == 0:
            #顺序播放时，只需在playingIndex操作就行了
            self.playingIndex = (self.playingIndex + 1) % len(self.playingList)
        elif self.order == 1:
            if manual:
                self.playingIndex = (self.playingIndex + 1) % len(self.playingList)
        elif self.order == 2:
            #随机播放，播完playingList的最后一首歌后，将重新生成一个随机的playingList_附加到原playingList后，实现循环
            #可以进一步优化该算法，实现同曲不靠近，例如每次播放按照权重附加一个index到playingList
            if (self.playingIndex + 1) == len(self.playingList):
                self.playingList_  = range(len(self.songList))
                random.shuffle(self.playingList_)
                self.playingList[len(self.playingList):] = self.playingList_
            self.playingIndex = self.playingIndex + 1
        self.logs.info('Next PlayingIndex: ' + str(self.playingIndex))
        self.songIndex = self.playingList[self.playingIndex]
        self.playIndex(self.songIndex)
    
    def previous(self): #默认肯定是manual
        if (self.order == 0) or (self.order == 1):
            self.playingIndex = self.playingIndex - 1
            if self.playingIndex < 0:
                self.playingIndex = len(self.playingList) - 1
        elif self.order == 2:
            self.playingIndex = self.playingIndex - 1
            if self.playingIndex < 0:
                self.playingIndex = 0
        self.logs.info('Prev PlayingIndex: ' + str(self.playingIndex))
        self.songIndex = self.playingList[self.playingIndex]
        self.playIndex(self.songIndex)
        
    def getCurrentInfo(self):
        if self.songList == []:return None
        return self.listdetail[self.songIndex], self.listFunc
        
    #用于私人FM。 API每次推三首歌，所以弃用playingList，直接用songList和songIndex(0~2)。于是不支持上一首功能（并且按下一首时没有调教曲库的行为）
    def initFM(self, limit = 3):
        self.reloadFM(limit)
        self.updateOrder(0)
        
    def reloadFM(self, limit = 3):
        self.logs.info('Reload FM')
        fmR, fmF = self.api.getFMSonglist(limit)
        self.updateListByDict(fmR['data'])
        self.songIndex = 0
        
    def nextFM(self, manual = False):
        if self.order == 1 and manual:
            pass
        else:
            if self.songIndex == len(self.songList) -1:
                self.reloadFM()
            else:
                self.playingIndex = self.playingIndex + 1
                self.songIndex = self.playingList[self.playingIndex]
        self.playIndex(self.songIndex)
        
    def insertSong(self, songIndex):
        #更换播放顺序后失效
        self.playingList[self.playingIndex+1:self.playingIndex+1] = [songIndex]
        
    def pauseCont(self):
        if self.player.state() == audio.EPlaying:
            self.pause()
        elif self.player.state() == audio.EOpen:
            self.cont()
            
    def pause(self):
        self.currPos = self.player.current_position()
        self.player.stop()
            
    def cont(self):
        self.player.set_position(self.currPos)
        self.player.play(callback=self.songCallback)
            
    def volumeAdjust(self, offset = 1):
        #offset正则加 负则减 音量从1到10
        if self.player:
            self.volume = self.player.current_volume()
            self.volume = self.volume + offset * self.player.max_volume()/10
            self.player.set_volume(self.volume)
            self.volume = self.player.current_volume()
    def volumeAdjustTo(self, num = 1):
        if self.player:
            self.volume = num
            self.player.set_volume(self.volume)
            self.volume = self.player.current_volume()
