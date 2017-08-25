# phpush.py
#

import appuifw
import phcomm
import os
import sys
import glob
import code
import thread
import pushlib
import graphics
import e32

class socket_stdio:
    def __init__(self, server):
        self.server = server
        self.writebuf = []
        self.readbuf  = []
        #self.snap = e32.ao_callgate( self.__snap )
        #self.show_imgfile = e32.ao_callgate( self.__show_imgfile ) 
        #self.show_img = e32.ao_callgate( self.__show_img )
        #self.flush = e32.ao_callgate( self.__flush )
        #self.write = e32.ao_callgate( self.__write )
        #self.read = e32.ao_callgate( self.__read )
        #self.readline = e32.ao_callgate( self.__readline )
        #self.synchronize = e32.ao_callgate( self.__synchronize )
        self.snapping = False
        self.redo = False
        
    def read(self,n=1):
        #print >> self.server.orig_stdout, 'calling read', n
        if not self.readbuf:
            self.readbuf = self.readline()
        readchars, self.readbuf = self.readbuf[0:n], self.readbuf[n:]
        return readchars
    def write(self,str):
        #print >> self.server.orig_stdout, 'calling write', str
        #print >> self.server.orig_stdout, self.writebuf, len(self.writebuf)
        if str:
            self.writebuf.append(str)
        #print >> self.server.orig_stdout, self.writebuf, len(self.writebuf)
        if '\n' in self.writebuf:
        #if '\n' in str:
            #print >> self.server.orig_stdout, 'flushing'
            self.flush()
        #else:
        #    print >> self.server.orig_stdout, 'not flushing'
    def flush(self):
    #def flush(self):
        #print >> self.server.orig_stdout, 'calling flush'
        if self.writebuf:
            self.server.send( 'output', ''.join(self.writebuf) )
            self.writebuf = []
    def snap(self):
    #def snap(self):
        """ send a snapshot of the phone screen to PC push which displays it """
        if self.snapping:
            self.redo = True
            return
        self.snapping = True
        # grab a snapshot, store to file
        filename = os.path.join( os.getcwd(), 'snap.jpg' )
        graphics.screenshot().save( filename )
        # send the file to PC
        self.server.send( 'snap snapshot' )
        self.server.send_file( filename )
        while self.redo:
            self.redo = False
            graphics.screenshot().save( filename )
            # send the file to PC
            self.server.send( 'snap snapshot' )
            self.server.send_file( filename )
        # clean up
        #os.remove( filename )
        self.snapping = False
    def show_imgfile( self, filename ):
        """ send a jpg or png image stored in a file to PC push which displays it """
        self.server.send( 'snap ' + os.path.split( filename )[1] )
        self.server.send_file( filename )
    def show_img( self, img, title='image' ):
        """ send an image to PC push which displays it """
        filename = os.path.join( os.getcwd(), 'snap.jpg' )
        img.save( filename )
        self.server.send( 'snap ' + title )
        self.server.send_file( filename )
        os.remove( filename )
    def readline(self):
        #print >> self.server.orig_stdout, 'calling readline'
        if self.readbuf:
            # if buffer has content, return it (and clear)
            buf, self.readbuf = self.readbuf[:], []
            return buf
        # else read the next line
        line = self.server.readline().rstrip()
        #print >> self.server.orig_stdout, 'line:', line        
        # parse the command, this is connected to PC shell
        # interface that sends commands
        head = line.split( ' ', 1 )[0]
        if head == 'cmdline':
            #return self.server.recv_data()
            line = self.server.recv_pyobj()
            head = line.split( ' ', 1 )[0]
            if head in pushlib.__all__:
                self.server.interpreter.runsource( 'pushlib.%s( "%s" )' % (head, line) )
                return ''
            else:
                return line            
        elif head == 'quit':
            self.server.quit()
            return ''
        elif head == 'reset':
            self.server.reset()
            return self.readline()
        elif head == 'sync':
            self.synchronize()
            return self.readline()
        elif head == 'syncl':
            self.synchronize( with_reload = True )
            return self.readline()
        elif head == 'snapshot':
            # grab a snapshot, store to file
            filename = os.path.join( os.getcwd(), 'snap.jpg' )
            graphics.screenshot().save( filename )
            # send the file to PC
            self.server.send_file( filename )
            # clean up
            os.remove( filename )
            # phone end just continues reading input...
            return self.readline()
        elif head == 'view':
            # use the first matching filename
            for filename in glob.glob( line.split( ' ' )[1] ):
                if ( os.path.splitext( filename )[1].lower() in ['.jpg', '.png']
                     and
                     os.path.isfile( filename ) ):
                    # tell it was OK, send the file
                    self.server.send( '1' )
                    self.server.send( filename )
                    self.server.send_file( filename )
                    return self.readline()
            # did not find a single matching image
            self.server.send( '0' )
            # phone end just continues reading input...
            return self.readline()
        elif head == 'runstartup':
            STARTUPFILE='c:\\startup.py'
            if os.path.exists( STARTUPFILE ):
                self.server.send( 'output', 'Running %s...' % STARTUPFILE )
                self.server.interpreter.runsource( 'execfile( "%s", globals(), locals() )' % STARTUPFILE )
            return ''
        return line

    def synchronize( self, with_reload = False ):

        # change current directory to Python home
        cwd = os.getcwd()
        if os.path.exists( 'c:/system/apps/python/python.app' ):
            os.chdir( 'c:/system/apps/python' )
        elif os.path.exists( 'e:/system/apps/python/python.app' ):
            os.chdir( 'e:/system/apps/python' )

        # ask for file names, checksums
        try:
            pc_offering = eval(self.server.recv_data())
        except 'Timeout':
            print >> self.server.orig_stdout, 'BT connection timed out.'
            print >> self.server.orig_stdout, 'Are you sure sync demon is running on PC?'
            return
        pc_demand   = eval(self.server.recv_data())

        # check whether some of the files should be retrieved
        for ph_file, pc_file, checksum in pc_offering:
            if checksum != phcomm.file_checksum( ph_file ):
                # checksums differ, get the file
                self.server.send( 'getfile', pc_file )
                # create / overwrite the file
                dirpath = os.path.split( ph_file )[0]
                if not os.path.exists( dirpath ):
                    os.makedirs( dirpath ) 
                self.server.recv_file( ph_file )
                print >> self.server.orig_stdout, 'received', ph_file

                if with_reload:
                    # reload a module if it appears in sys.modules
                    modpath, ext = os.path.splitext( ph_file )
                    modname = os.path.split(modpath)[1].lower()
                    if modname in sys.modules.keys():
                        reload( sys.modules[modname] )
                        print >> self.server.orig_stdout, 'reloaded module: ', modname

        # check which files the pc wants, whether some should be sent
        for targetdir, phone_patterns in pc_demand:
            # force patterns to be a sequence
            if not isinstance(phone_patterns, tuple) and not isinstance(phone_patterns, list):
                phone_patterns = [ phone_patterns ]
            for patt in phone_patterns:
                for fname in glob.glob( patt ):
                    try:
                        # read in the data
                        f = open( fname, 'rb' )
                        data = f.read()
                        f.close()
                        # calculate checksum
                        crc = phcomm.data_checksum( data )
                        # offer the file (with checksum and target filename)
                        print >> self.server.orig_stdout, 'offering', fname
                        self.server.send( 'offerfile %d' % crc,
                                          os.path.join(targetdir, os.path.split(fname)[1]) )
                        # does the pc want the file?
                        if int(self.server.readline()):
                            # yes, the pc wants this file
                            self.server.send_data( data )
                            print >> self.server.orig_stdout, '         SENT.'
                        else:
                            # no, skip this file
                            print >> self.server.orig_stdout, '         NOT sent.'
                        del data # help in memory cleanup
                    except:
                        pass
        print >> self.server.orig_stdout, 'sync done'
        print 'sync done.'

        # restore cwd
        os.chdir( cwd )

class wxshell_server( phcomm.SvrCli ):
    def __init__( self, sock, verbose=0 ):
        phcomm.SvrCli.__init__( self, sock, verbose )
        # At first I tried to write this like btconsole.py
        # and create a rawinput function, etc., but that just won't work.
        # That's why raw_input things are commented out.
        # On the pc end phone is called from the runsource method,
        # and the protocol is that phone can return outputs in the middle
        # of execution (inputs in the middle of execution don't currently
        # work either right now), and in the end phone must return the
        # 'more' status of the runsource(). PyShell automates things,
        # and that comes at a price of some assumptions.
#         self.real_rawinput = __builtins__.raw_input
#         __builtins__.raw_input = self._readfunc
        self.orig_stdin  = sys.stdin
        self.orig_stdout = sys.stdout
        self.orig_stderr = sys.stderr
        self.reset()
        sys.stdout = socket_stdio(self)
        sys.stderr = socket_stdio(self)
        sys.stdin  = socket_stdio(self)
        self.finished = False
        pushlib.init_globals( globals() )
        try:
            while not self.finished:
                line = sys.stdin.readline()
                more = self.interpreter.runsource( line )
                if more:
                    self.send('more')
                else:
                    self.send('nomore')
        except:
            sys.stdout = self.orig_stdout
            sys.stderr = self.orig_stderr
            sys.stdin  = self.orig_stdin
            print "Interpreter threw an exception:"
            import traceback
            traceback.print_exc()
        # either finished or caught an exception
#         __builtins__.raw_input = self.real_rawinput
        self.close()
        sys.stdout = self.orig_stdout
        sys.stderr = self.orig_stderr
        sys.stdin  = self.orig_stdin
            
#     def _readfunc( self, prompt="" ):
#         print >> self.orig_stdout, '_readfunc'
#         sys.stdout.write(prompt)
#         sys.stdout.flush()
#         return sys.stdin.readline().rstrip()
 
    def quit( self ):
        self.finished = True
        
    def interpr_write( self, data ):
        # stderr messages are relayed to pc from here
        self.send( 'output', data )
        
    def reset( self ):
        # restart the whole interpreter
        d = { '__name__' : '__console__',
              '__doc__' : None,
              'pushlib' : pushlib }
        self.interpreter = code.InteractiveInterpreter( d )
        self.interpreter.write = self.interpr_write
        self.interpreter.runsource( 'pushlib.gohome()' )
        
            
def main( interactive = True ):
    sock = phcomm.connect_phone2PC( 'phonecrust_conf.txt',
                                    interactive = interactive )
    if sock:
        try:
            wxshell_server( sock )
        except:
            print 'crust_server run failed'
            import traceback
            traceback.print_exc()
        print "crust_server done."
    else:
        print 'Did not connect, exiting.'


if __name__ == '__main__':
    main()
else:
    main( False ) # for faster debugging, use the default host
