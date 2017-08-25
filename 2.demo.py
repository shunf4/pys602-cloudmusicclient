import logging
import sys
class Stderr:
    def __init__(self, originalStderr, logger):
        self.originalStderr = originalStderr
        self.logger = logger
        
    def bind(self):
        sys.stderr = self

    def release(self):
        sys.stderr = self.originalStderr

    def write(self, sth):
        self.logger.error(sth.replace("\n",""))
        self.originalStderr.write(sth)



import sys
print sys.path
import appuifw2
appuifw2.app.body = appuifw2.Text_display(text=u"Wow",skinned=True)
appuifw2.note(u"")