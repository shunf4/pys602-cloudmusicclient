#coding=utf-8

import sys
import os
import appuifw

MAIN_ON_PC = False
MAIN_ON_PYCON = False
MAIN_ON_SIS = True

if MAIN_ON_PYCON:
    os.chdir("e:\\python")

sys.path.insert(0, os.path.join(os.getcwd(), 'lib.zip'))
sys.path.insert(0, os.getcwd())
sys.path.insert(0, "c:\\sys\\bin")
sys.path.insert(0, "e:\\sys\\bin")


#my_console = series60_console.Console()
#saved_exit_key_handler = appuifw.app.exit_key_handler


def restore_defaults():
    appuifw.app.body = my_console.text
    sys.stderr = sys.stdout = my_console
    appuifw.app.screen = 'large'
    appuifw.app.menu = []

# restore_defaults()


def display_traceback():
    import traceback
    sys.stderr.write(traceback.format_exc() + '\n')

import progressnotes


globalProg = progressnotes.ProgressNote()

globalProg.wait()
globalProg.update(0, "正在加载…".decode("utf-8"))

def globalProgUpdate(sth):
    globalProg.update(0, sth.decode("utf-8"))    

default_namespace = {'__builtins__': __builtins__, '__name__': '__main__', 'SYS_STDERR': sys.stderr, 'MAIN_ON_PC' : MAIN_ON_PC,
                       'MAIN_ON_PYCON': MAIN_ON_PYCON, 'MAIN_ON_SIS': MAIN_ON_SIS, 'globalProg' : globalProg, 'globalProgUpdate' : globalProgUpdate }

globalProgUpdate("设置错误输出")
from util import getNewStdErrForLauncher
sys.stderr = getNewStdErrForLauncher(sys.stderr)


try:
    globalProgUpdate("启动主程序")
    execfile('default.py', default_namespace)
except Exception, e:
    globalProgUpdate("出现错误！")
    globalProg.finish()
    display_traceback()
finally:
    globalProg.finish()
    sys.stderr = sys.stderr.originalStderr
    default_namespace.clear()
 