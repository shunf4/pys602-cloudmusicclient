"""
phcomm.py

Phone - PC communication module

Right now only Bluetooth communication supported

Create a simple protocol where commands are newline-terminated strings,
not checked for correctness of transmission, and binary data is sent
preceded by a header that allows checking for transmission errors (with crc32).
"""

# Copyright (c) 2006 Nokia Corporation
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

# Created by Kari Pulli


import os
import sys
import socket
import binascii
import marshal
import struct

def data_checksum( data ):
    return binascii.crc32( data )

def file_checksum( filename ):
    try: 
        return binascii.crc32( open( filename, 'rb' ).read() )
    except IOError, (errno, strerror):
        if errno != 2:
            # errno == 2 is the file doesn't exist, that's OK
            # other errors should be printed
            print 'IOError in file_checksum( %s ): %s' % (filename, strerror)
        return None

def file_checksums( filelist ):
    retval={}
    for fname in filelist:
        retval[ fname ] = file_checksum( fname )
    return retval

# def int2hexstring( i ):
#     if i < 0:
#         # negative
#         # 4294967296L == 1<<32
#         return ('%08x' % (i + 4294967296L))[-8:]
#     else:
#         # positive
#         return ('%08x' % i)[-8:]

# def hexstring2int( s ):
#     if s[0] < '8':
#         # positive
#         return int( s, 16 )
#     else:
#         # negative
#         # 4294967296L == 1<<32
#         return int( long( s, 16 ) - 4294967296L )

def discover_address( config_file, interactive = True ):
    """ discover_address( config_file, interactive = True )
    called on the phone side
    config_file stores the address and port of previous connection
    if interactive == False that address is used, otherwise
    the user is prompted to select device and service
    """
    import appuifw

    CONFIG_DIR  = 'c:/system/apps/python'
    CONFIG_FILE = os.path.join( CONFIG_DIR, config_file )
    try:        
        config = eval( open(CONFIG_FILE, 'r').read() )
    except:
        config = {}

    address = config.get( 'target', '' )

    if address and not interactive:
        return address

    if address:
        choice = appuifw.popup_menu( [u'Default host', u'Other...'],
                                     u'Connect to:' )
        if choice == 0:
            return address
        if choice == None:
            return None # popup menu was cancelled

    # address not stored, or want a new host
    print "Discovering..."
    addr, services = socket.bt_discover()
    print "Discovered: %s, %s" % ( addr, services )
    if len(services) > 1:
        choices = services.keys()
        choices.sort()
        def dropendzero(x):
            # this is to overcome a bug of choice strings
            # having a terminating zero...
            if ord(x[-1]) == 0:
                return unicode( x[:-1] )
            else:
                return unicode( x )
        #l = [(unicode(services[x]), dropendzero(x)) for x in choices]
        #choice  = appuifw.popup_menu( l, u'Choose port (scroll):' )
        l = [ dropendzero(x) for x in choices ]
        choice  = appuifw.popup_menu( l, u'Choose port:' )
        if choice == None:
            print 'no choice'
            return None
        port = services[choices[choice]]
    else:
        port = services.values()[0]
    address = ( addr, port )
    config['target'] = address
    # make sure the configuration file exists
    if not os.path.isdir( CONFIG_DIR ):
        os.makedirs( CONFIG_DIR )
    # store the configuration file
    open( CONFIG_FILE, 'wt' ).write( repr( config ) )
    return address


def connect_PC2phone( com_port, verbose=0 ):
    """com_port 1 == COM1, etc."""
    class filesocket:
        """Give a socket API to an object that otherwise has a file API
        """
        def __init__( self, file ):
            self.file = file
        def recv( self, n=1 ):
            return self.file.read( n )
        def send( self, msg ):
            self.file.write( msg )
            self.file.flush()
            return len( msg )
        def close( self ):
            pass
    try:
        import serial
        import types
        # pyserial module http://sourceforge.net/projects/pyserial/
        if type(com_port) == types.IntType:
            c_port = com_port - 1
        elif type(com_port) == types.StringType:
            c_port = com_port
        else:
            print "Wrong type of com_port in config file"
            sys.exit()
        try:
            ser = serial.Serial( c_port, timeout = 2 )
        except serial.serialutil.SerialException, e:
            print "Opening COM port failed (maybe it's already in use?)"
            print '    ', e
            sys.exit( 1 )
        print 'Connecting to serial port', ser.portstr
        return filesocket( ser )
    except ImportError:
        print 'need pyserial module'
        raise 


def connect_phone2PC( config_file, interactive = True ):
    addr = discover_address( config_file, interactive)
    if addr:
        s = socket.socket( socket.AF_BT, socket.SOCK_STREAM )
        #print "Connecting to "+`addr`
        s.connect( addr )
        #print "Connected to "+`addr`
        return s
    else:
        print 'Failed to connect.'
        return None


class SvrCli:
    """ base class for Server and Client
    """
    def __init__( self, sock, verbose=0 ):
        self.sock    = sock
        self.line    = []
        if not verbose:
            self.log = lambda x:0

    def log( self, s ):
        sys.stdout.write( s + '\n' )
        sys.stdout.flush()

    def check_timeout( self, secs = 5 ):
        rd = True
        try:
            # on the phone side, check for timeout
            import appuifw  # on PC this should fail, so no timeout check
            import select
            rd, wr_dummy, ex_dummy = select.select( [self.sock], [], [], secs )
            while rd == []:
                if appuifw.query( u'Timeout on BT, exit?', 'query' ):
                    self.close()
                    raise 'Timeout'
                rd, wr_dummy, ex_dummy = select.select( [self.sock], [], [], timeout )
        except:
            pass
        
    def recv_data( self ): 
        #self.log("Waiting for content length..."
        self.check_timeout( 3 )
#         s1, s2 = self.sock.recv(8), self.sock.recv(8)
#         #print 'recv', s1, s2
#         content_length, crc32 = hexstring2int( s1 ), hexstring2int( s2 )
#         #print content_length, crc32
        content_length, crc32 = tuple( [int(s) for s in self.readline().split()] )
        self.log("Content-Length: %d\n" % content_length)
        recvbytes      = 0
        content        = []
        #self.log("Receiving data...")
        while recvbytes < content_length:
            recvstring = self.sock.recv( min(content_length-recvbytes,2048) )
            recvbytes  += len(recvstring)
            self.log("Received: %d bytes (%3.1f%%)\r"%(recvbytes,(100.*recvbytes/content_length)))
            content.append( recvstring )
        self.log("Received: %d bytes.        "%(recvbytes)+"\n")
        content = ''.join(content)
        if crc32 != binascii.crc32(content):
            str = """\
            expected crc %d, calculated crc %d
            expected content length %d, content length %d
            """ % (crc32, binascii.crc32(content), content_length, len(content))
            raise IOError("CRC error while receiving data:\n"+str)
        return content
    
    def recv_data_to_file( self, filename ):
        # deprecated, don't use
        print 'using a deprecated function: phcomm.recv_data_to_file()'
        print 'instead use phcomm.recv_file()'
        self.recv_file( filename )
        
    def recv_file( self, filename ):
        # the reason for this function is to store everything into a file and not have
        # the whole content in the memory at the same time
        # recv_data() actually has to content twice in the memory at the same time!
        self.check_timeout( 3 )
        f = open( filename, 'wb' )
        content_length, crc32 = tuple( [int(s) for s in self.readline().split()] )
        self.log("Content-Length: %d\n" % content_length)
        recvbytes      = 0
        content        = []
        #self.log("Receiving data...")
        recvstring = self.sock.recv( min(content_length-recvbytes,2048) )
        recvbytes  += len(recvstring)
        f.write( recvstring )
        crc = binascii.crc32( recvstring )
        while recvbytes < content_length:
            recvstring = self.sock.recv( min(content_length-recvbytes,2048) )
            recvbytes  += len(recvstring)
            f.write( recvstring )
            crc = binascii.crc32( recvstring, crc )
        f.close()
        self.log("Received: %d bytes.        "%(recvbytes)+"\n")
        if crc32 != crc:
            str = """\
            expected crc %d, calculated crc %d
            expected content length %d, content length %d
            """ % (crc32, crc, content_length, recvbytes)
            raise IOError("CRC error while receiving data:\n"+str)

    def send_file( self, filename ):
        # Send the data in little bits because the Bluetooth serial
        # connection may lose data on large sends.
        # Also want to conserve RAM consumption.
        MAX_SEND  = 2048
        # first, read file in chunks to get data length and crc
        f = open( filename, 'rb' )
        data = f.read( MAX_SEND )
        crc, datalen = 0, 0
        while data:
            datalen += len( data )
            crc = binascii.crc32( data, crc )
            data = f.read( MAX_SEND )
        # now we know what to send
        self.log( "Content-Length: %d\n" % datalen )
        self.write( '%d %d\n' % (datalen, crc) )
        # rewind the file
        f.seek( 0 )
        sentbytes = 0
        while sentbytes < datalen:
            n = min( datalen-sentbytes, MAX_SEND )
            self.write( f.read( n ) )
            sentbytes += n
            self.log( "Sent: %d bytes (%3.1f%%)\r" % ( sentbytes, (100.*sentbytes/datalen) ) )
        ## TODO: send in 2kB blocks
        #f = open( filename, 'rb' )
        #self.send_data( f.read() )
        f.close()
        
    def send_data( self, data ):
        self.log("Content-Length: %d\n" % len(data))
        self.write( '%d %d\n' % (len(data), binascii.crc32(data) ) )
        sentbytes = 0        
        # Send the data in little bits because the Bluetooth serial
        # connection may lose data on large sends.
        MAX_SEND  = 2048
        while sentbytes < len(data):
            n = min( len(data)-sentbytes, MAX_SEND )
            self.write( data[sentbytes:sentbytes+n] )
            sentbytes += n
            self.log( "Sent: %d bytes (%3.1f%%)\r" % ( sentbytes, (100.*sentbytes/len(data)) ) )

    def send_pyobj( self, obj ):
        """ send a python object, e.g., a unicode string """
        self.log( 'sent ' + `obj` )
        self.send_data( marshal.dumps( obj ) )
        
    def recv_pyobj( self ):
        """ receive a python object, e.g., a unicode string """
        data = self.recv_data()
        #print 'hip', repr(data)
        obj = marshal.loads( data )
        #print 'hop', repr(obj)
        self.log( 'received ' + `obj` )
        return obj
        
    def send( self, cmd, data = '' ):
        """ send a command line, with optional binary data """
        cmd = cmd.strip() + '\n'
        self.log( cmd )
        self.write( cmd )
        if data:
            self.send_data( data )
            
    def readline( self ):
        c = ''
        while c != '\n':
            c = self.sock.recv(1)
            #self.log( 'Got ' + c + '\n' )
            if c:
                self.line.append(c)
                #self.log( 'Buffer: ' + ''.join(s) )
        line = ''.join( self.line )
        self.line = []
        return line
    
    def readline_dontblock( self ):
        c = self.sock.recv(1)
        if c:
            self.line.append(c)
        if c == '\n':
            line = ''.join( self.line )
            self.line = []
            return line
        else:
            return ''
    
    def write( self, msg ):
        self.sock.send(msg)

    def close( self ):
        if self.sock:
            try:
                # workaround for the bug where select on phone keeps a pointer
                # in C++ when at timeout
                self.sock._sock.close()
            except:
                pass
            self.sock.close()
            self.sock = None


class Server( SvrCli ):
    """ code for server, extend this class in your application
    """
    def __init__( self, sock, verbose=0 ):
        SvrCli.__init__( self, sock, verbose )

    def cmd_quit( self, line ):
        self.finished = True

    def cmd_invalid( self, line ):
        self.log( 'Invalid command ' + line )
        self.finished = True

    def cmd_exec( self, cmdline ):
        command = eval( self.recv_data() )
        self.log( "exec " + command )
        try:
            exec command in globals()
            result = ( 0, '' )
        except:
            import traceback
            result = ( 1, apply(traceback.format_exception, sys.exc_info()) )
        self.send_data( repr(result) )

    def cmd_eval( self, cmdline ):
        expr = eval( self.recv_data() )
        self.log( "eval " + expr )
        # two eval's because we need to first get rid of one level of quoting
        result = ''
        try:
            value = eval(expr,globals())
            result = ( 0, value )
        except:
            import traceback
            result = ( 1, apply(traceback.format_exception, sys.exc_info()) )
        self.send_data( repr(result) )

    def run( self ):
        self.log( 'Running...' )
        self.finished = False
        while not self.finished:
            cmdline = self.readline().rstrip()
            #self.log("Received: "+cmdline)
            words = cmdline.split()
            if len(words):
                cmd = 'cmd_' + words[0]
                self.log( "Running command: " + cmdline )
                if not cmd in dir(self):
                    self.cmd_invalid( cmdline )
                else:
                    exec 'self.%s( cmdline )' % cmd
        self.close()

            
class Client( SvrCli ):
    """ code for client, extend this in your application
    """
    def __init__( self, sock, verbose=0 ):
        SvrCli.__init__( self, sock, verbose )

    def sendexpr( self, cmd, expr ):
        self.send( '%s %s\n' % (cmd, expr), repr(expr) )
        result = eval( self.recv_data() )
        if result[0]!=0:
            raise "Exception on server side: " + ''.join(result[1])
        else:
            return result[1]
        
    def execute( self, expr ):
        self.sendexpr( 'exec', expr )

    def evaluate( self, expr ):
        return self.sendexpr( 'eval', expr )
        
    def killserver( self ):
        self.send( 'quit' )

    def readline( self ):
        self.check_timeout( 10 )
        return SvrCli.readline( self )
