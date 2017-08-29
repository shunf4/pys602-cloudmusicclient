# Copyright (c) 2008 - 2009 Nokia Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os
import series60_console
import appuifw

MAIN_ON_PC = False
MAIN_ON_PYCON = True
MAIN_ON_SIS = False

if MAIN_ON_PYCON:
    os.chdir("e:\\python")

sys.path.insert(0, os.path.join(os.getcwd(), 'lib.zip'))
sys.path.insert(0, os.getcwd())
default_namespace = {'__builtins__': __builtins__, '__name__': '__main__', 'SYS_STDERR': sys.stderr, 'MAIN_ON_PC' : MAIN_ON_PC,
                       'MAIN_ON_PYCON': MAIN_ON_PYCON, 'MAIN_ON_SIS': MAIN_ON_SIS }

my_console = series60_console.Console()
saved_exit_key_handler = appuifw.app.exit_key_handler


def restore_defaults():
    appuifw.app.body = my_console.text
    sys.stderr = sys.stdout = my_console
    appuifw.app.screen = 'large'
    appuifw.app.menu = []

# restore_defaults()


def display_traceback():
    import traceback
    sys.stderr.write(traceback.format_exc() + '\n')

from util import getNewStdErrForLauncher
sys.stderr = getNewStdErrForLauncher(sys.stderr)


try:
    execfile('default.py', default_namespace)
except Exception, e:
    display_traceback()
finally:
    sys.stderr = sys.stderr.originalStderr
    default_namespace.clear()
    
# try:
    
# except SystemExit, err:
#     # Check whether it is a successful or an abnormal termination. '' is also
#     # checked as not passing any arguments in the sys.exit() call evaluates to
#     # `None`.
#     if str(err) not in [str(0), '']:
#         display_traceback()
#     else:
#         appuifw.app.set_exit()
# except:
#     display_traceback()
# else:
#     # If nothing was written onto the text widget, exit immediately
#     if not appuifw.app.body.len():
#         appuifw.app.set_exit()
