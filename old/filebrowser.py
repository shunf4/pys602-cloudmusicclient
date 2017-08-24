#
# filebrowser.py
#
# A very simple file browser script to demonstrate the power of Python
# on Series 60.
#      
# Copyright (c) 2004 Nokia. All rights reserved.
#

import os
import appuifw
import e32
import sys
import time

class Directory_iter:
    def __init__( self, drive_list):
        self.drives     = [((unicode(i), u"Drive")) for i in drive_list]
        self.path       = u'\\'

    def pop( self):
        if os.path.splitdrive( self.path)[1] == u'\\':
            # at the root of a drive, go to the system root (or stay there)
            self.path = u'\\'
        else:
            # drop the last path level
            self.path = os.path.split( self.path)[0]

    def add( self, i):
        if self.path == u'\\':
            # at system root, go into one of the drives
            self.path = self.drives[i][0]+u'\\'
        else:
            # descend into entry i
            self.path = self.entry( i )

    def list_repr( self):
        if self.path == u'\\':
            return self.drives
        else:
            def item_format(i):
                full_name = os.path.join( self.path, i)
                s = os.stat( full_name )
                time_field = time.strftime("%d.%m.%Y %H:%M", time.localtime( s.st_mtime ));
                info_field = time_field+"  %db" % s.st_size
                if os.path.isdir( full_name ):
                    name_field = "["+i+"]"
                else:
                    name_field = i
                return (unicode(name_field), unicode(info_field))
            try:
                l = map(item_format, os.listdir( self.path))
            except:
                l = []
            return [(u"..", u"")] + l

    def entry( self, i):
        return os.path.join( self.path, os.listdir( self.path)[i])


class Filebrowser:
    def __init__( self ):
        self.script_lock = e32.Ao_lock()
        self.dir_stack = [] # index of focus item, store when descending, pop when ascending
        self.current_dir = Directory_iter(e32.drive_list())

    def run( self ):
        from key_codes import EKeyLeftArrow
        entries = self.current_dir.list_repr()
        self.lb = appuifw.Listbox(entries, self.lbox_observe)
        # pop up one level with left arrow
        self.lb.bind(EKeyLeftArrow, lambda: self.lbox_observe(-1))
        old_title = appuifw.app.title
        self.refresh()
        # go into main UI loop
        self.script_lock.wait()
        # done, cleanup
        appuifw.app.title = old_title
        appuifw.app.body  = None
        self.lb           = None

    def refresh( self ):
        appuifw.app.exit_key_handler = self.exit_key_handler
        appuifw.app.title = u"File browser"
        appuifw.app.body  = self.lb
        appuifw.app.menu = [(u"Delete", self.do_delete),
                            (u"Rename", self.do_rename),
                            (u"Move",   self.do_move),
                            ]

    def do_exit( self ):
        self.exit_key_handler()

    def exit_key_handler( self ):
        appuifw.app.exit_key_handler = None
        self.script_lock.signal()

    def lbox_observe( self, index=None ):
        if index == None:
            index = self.lb.current()
        focused_item = 0

        if self.current_dir.path == u'\\':
            # at system root, go into drive
            if index != -1:
                # that is, if didn't select left click
                self.dir_stack.append( index )
                self.current_dir.add( index )
        elif index == 0 or index == -1:
            # ".." selected or left click, pop up
            focused_item = self.dir_stack.pop()
            self.current_dir.pop()
        elif os.path.isdir( self.current_dir.entry(index-1)):
            # directory entry, go into directory
            self.dir_stack.append( index )
            self.current_dir.add( index-1 )
        else:
            # file entry, deal with the file
            item = self.current_dir.entry( index-1 )
            is_pyfile = os.path.splitext(item)[1].lower() == u'.py'
            if is_pyfile:
                i = appuifw.popup_menu([u"execfile()", u"Delete"])
            else:
                i = appuifw.popup_menu([u"Open", u"Delete"])
            if i == 0:
                if is_pyfile:
                    execfile(item, globals())
                    self.refresh()
                    #appuifw.Content_handler().open_standalone(item)
                else:
                    try:
                        appuifw.Content_handler().open(item)
                    except:
                        import sys
                        type, value = sys.exc_info() [:2]
                        appuifw.note(unicode(str(type)+'\n'+str(value)), "info")
                return
            elif i == 1:
                os.remove( item )
                focused_item = index - 1

        entries = self.current_dir.list_repr()
        self.lb.set_list( entries, focused_item )

    def do_delete( self ):
        index = self.lb.current()
        if self.current_dir.path == u'\\' or index == 0:
            # at system root or '..', can't delete those
            return
        item = self.current_dir.entry( index-1 )
        if os.path.isdir( item ):
            # currently can't delete directory
            return
        else:
            # a file, delete it
            os.remove( item )
            entries = self.current_dir.list_repr()
            self.lb.set_list( entries, index-1 )

    def do_rename( self ):
        pass

    def do_move( self ):
        pass
        

if __name__ == '__main__':
    Filebrowser().run()
