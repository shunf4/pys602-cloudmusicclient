import imp
import os
print os.path.exists("e:\\python\\lib\\kf__ujson.PYD")
_ujson = imp.load_dynamic("ujson", "e:\\python\\lib\\GCCAES.PYD")
from _ujson import *