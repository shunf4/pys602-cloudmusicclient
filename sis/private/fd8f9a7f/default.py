import sys,e32
sys.path.insert(0, "e:\\python\\lib")
import audio_compatible as audio
#import audio
import appuifw
import graphics_compatible as graphics
print graphics


def g(a, b, c):
    print "a"
    sys.stdout.flush()
    u = graphics.Image.open("e:\\python\\pic\\pic.bmp")
    u = u.resize((81,81), None)
    print u.size
    
player = audio.Sound.open("E:\\test.mp3")
player.set_volume(1)
player.play(callback = g)