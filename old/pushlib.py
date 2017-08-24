
__all__ = [ 'cat', 'cd', 'less', 'ls', 'man', 'mkdir', 'more', 'pwd', 'quit',
            'reset', 'rm', 'run', 'snap', 'sync', 'syncl', 'view' ]

import os, sys, glob

if os.path.exists('c:/system/apps/python/python.app'):
    HOME = 'c:/system/apps/python'
elif os.path.exists('e:/system/apps/python/python.app'):
    HOME = 'e:/system/apps/python'
elif os.path.exists('e:/Python'):
    HOME = 'e:/Python'
else:
    os.makedirs( 'e:/Python/lib' )
    HOME = 'e:/Python'
    raise 'Cannot find python home directory, created e:/Python to be it. Please try again.'

run_globals = dict( globals() )
run_globals['__name__'] = '__main__'

def init_globals( d ):
    """create a dictionary that is used as global dictionary with the run command
    so the run works as expected (with fairly clean namespace, __name__ = __main__, etc.
    """
    global run_globals
    run_globals = dict( d )
    run_globals['__name__'] = '__main__'
    

def trace( msg = '' ):
    import traceback
    for l in traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback):
        print l
    if msg:
        print msg    

def gohome():
    os.chdir( HOME )    

def cat( line = '' ):
    """
    NAME
       cat - concatenate files and print on the standard output

    SYNOPSIS
       cat [FILE]...

    DESCRIPTION
       Really only reads a single file and sends the content to output.
       Currently less and more are synonyms for cat.
    """
    l = line.split( ' ', 1 )
    try:
        if os.path.isfile( l[1] ):
            print open( l[1], 'r' ).read()
        else:
            print '"%s" is not a file' % l[1]
    except:
        trace( l[0]+' failed' )
        
less = cat
more = cat

def cd( line = '' ):
    """
    NAME
       cd - change directory

    SYNOPSIS
       cd [DIRECTORY]

    DESCRIPTION
       Change current directory to DIRECTORY.
       If no DIRECTORY is given, goes to HOME (the Python installation directory).
       Currently also calls ls at the new directory.
    """
    l = line.split( ' ', 1 )
    try:
        if len(l) > 1:
            os.chdir( l[1] )
        else:
            gohome()
        print 'current directory:', os.getcwd()
        print
        ls()
    except:
        trace( 'cd failed' )

def printdir( d, files ):

    if d:
        print '%s:' % d

    if files:
        # add a slash to all directories
        for i in range(len(files)):
            if os.path.isdir(files[i]):
                files[i] += '/'
        # how wide columns?
        n = max( [ len(f) for f in files ] ) + 2
        # how many columns?
        ncols = 80 / n
        # how many rows per column?
        nrows = (len(files)+ncols-1) / ncols
        files.extend( ['']*(nrows*ncols - len(files)) )

        # split entries into columns
        cols = []
        while files:
            cols.append( files[:nrows] )
            files = files[nrows:]

        # find out how long each column should be
        colwidth = []
        for col in cols:
            colwidth.append( max( [len(f) for f in col] ) + 1 )

        # print one row at a time
        for i in range(nrows):
            for j in range(ncols):
                print cols[j][i].ljust( colwidth[j] ),
            print
        print
    else:
        print '<empty directory>' 


def glob_entries( str ):
    """ str may contain several entries with wild cards, return two lists,
    the first being files and second directories matched by the entries
    """
    # glob all the entries
    entries = []
    for e in str.split( ' ' ):
        entries.extend( glob.glob(e) )
    # sort them to files vs. dirs
    files = []
    dirs = []
    for e in entries:
        if os.path.isdir( e ):
            dirs.append( e )
        elif os.path.isfile( e ):
            files.append( e )
    return files, dirs

    
def ls( line = '' ):
    """
    NAME
       ls - list directory contents

    SYNOPSIS
       ls [FILE]...

    DESCRIPTION
       List files in a path. Wildcards (*, ?) are allowed.
       If no arguments are given, lists the content of the current directory.
    """
    try:
        # get the files
        l = line.split(' ', 1)
        if len(l) == 1:
            # just ls
            printdir( '', os.listdir( '.' ) )
        else:
            files, dirs = glob_entries( l[1] )
            if files:
                # show the files
                files.sort()
                printdir( '', files )
            if dirs:
                if files or len( dirs ) > 1:
                    # not just a single directory, show directory name and contents
                    dirs.sort()
                    for d in dirs:
                        printdir( d, os.listdir( d ) )
                else:
                    # just a single directory, list it
                    printdir( '', os.listdir( dirs[0] ) )

    except:
        trace( 'ls failed' )

def man( line = '' ):
    """
    NAME
       man - format and display on-line manual pages

    SYNOPSIS
       man NAME

    DESCRIPTION
       man displays and formats the on-line manual pages
    """
    try:
        l = line.split(' ', 1)
        if len(l) == 2:
            if globals().has_key( l[1] ) and globals()[l[1]].__doc__:
                print globals()[l[1]].__doc__
            else:
                print l[1], 'does not have a man entry'
                available_commands()
        else:
            print man.__doc__
            available_commands()
    except:
        trace( 'man failed' )

def mkdir( line = '' ):
    """
    NAME
       mkdir - make directories

    SYNOPSIS
       mkdir DIRECTORY...

    DESCRIPTION
       Create the DIRECTORY(ies), if they do not already exist.
    """
    try:
        dirs = line.split()[1:]
        for d in dirs:
            if os.path.exists( d ):
                if os.path.isdir( d ):
                    print "mkdir: cannot create directory '%s': File exists" % d
                else:
                    print "mkdir: '%s' exists but is not a directory" % d
            else:
                os.mkdir( d )
    except:
        trace( 'mkdir failed' )

def available_commands():
    print 
    print 'The following commands are available'
    for c in __all__: 
        print '    ', c

def pwd( line = '' ):
    """
    NAME
       pwd - print name of current/working directory

    SYNOPSIS
       pwd

    DESCRIPTION
       Print name of working directory.
    """
    print os.getcwd()

def quit():
    """
    NAME
       quit - quits push and phpush

    SYNOPSIS
       quit

    DESCRIPTION
       quit - quits push and phpush
    """
    pass

def reset():
    """
    NAME
       reset - resets the Python interpreter

    SYNOPSIS
       reset

    DESCRIPTION
       Cleans up the namespace by creating a new instance of the Python
       interpreter for push.
    """
    pass

def rm( line = '' ):
    """
    NAME
       rm - remove files or directories

    SYNOPSIS
       rm FILE...

    DESCRIPTION
       Remove files and empty directories. Wildcards (*, ?) are allowed.
    """
    try:
        l = line.split(' ', 1)
        files, dirs = glob_entries( l[1] )
        for f in files:
            os.unlink( f )
        for d in dirs:
            if os.listdir( d ):
                print d, 'is not empty, can only delete empty directories'
            else:
                # it's an empty directory
                os.rmdir( d )
    except:
        trace( 'rm failed' )


def run( line = '' ):
    """
    NAME
       run - execute a python file

    SYNOPSIS
       run FILE

    DESCRIPTION
       Executes a python file.
       Example: run hello.py
                run hello
    """
    try:
        l = line.split(' ', 1)
        if not l[1]:
            print 'give me something to run!'
            return
        file = ''
        if os.path.isfile( l[1] ):
            file = l[1]
        elif os.path.isfile( l[1]+'.py' ):
            file = l[1]+'.py'
        if file:
            execfile( file, run_globals, run_globals )
        else:
            print "can't find %s or %s.py" % (l[1], l[1])
    except:
        trace( 'run failed' )

def snap():
    """
    NAME
       snap - takes a snapshot of phone screen and displays on PC

    SYNOPSIS
       snap [FILE]

    DESCRIPTION
       snap - takes a snapshot of phone screen and displays on PC
       If you give the optional file argument, the snapshot will
       be saved in that file. If the filename does not end with .jpg,
       the ending will be added to the filename.
       On the snapshot window on PC hitting + enlarges the window,
       - reduces the window size, q hides the window.
    """
    pass

def sync():
    """
    NAME
       sync - synchronizes files between PC and the phone

    SYNOPSIS
       sync

    DESCRIPTION
       Synchronizes files between PC and phone based on the information
       in the sync.config file on PC.
    """
    pass

def syncl():
    """
    NAME
       syncl - synchronizes files between PC and the phone

    SYNOPSIS
       syncl

    DESCRIPTION
       Synchronizes files between PC and phone based on the information
       in the sync.config file on PC.
       Also reloads a modules if they are currently loaded in.
    """
    pass

def view():
    """
    NAME
       view - send a jpg or png file on the phone to PC and display

    SYNOPSIS
       view FILE

    DESCRIPTION
       Send a jpg or png file on the phone to PC and display.
       If FILE has wild cards and matches more than one file, only the
       first jpg or png file is displayed.       
    """
    pass
