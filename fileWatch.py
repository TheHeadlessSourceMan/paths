"""
Watch a file for changes
"""
import typing
from enum import Enum
import datetime
import os
from pathlib import Path
import threading
import win32con # type: ignore
import win32file # type: ignore


class FileChangeType(Enum):
    """
    What type of change occurred on a file
    """
    CREATE=0
    READ=1
    UPDATE=2
    DELETE=3


class FileChange:
    """
    Record of a single file change
    """

    def __init__(self,
        changeType:FileChangeType,
        filename:Path,
        timestamp:typing.Optional[datetime.datetime]=None):
        """ """
        if timestamp is None:
            timestamp=datetime.datetime.now()
        self.filename=filename
        self.changeType=changeType
        self.timestamp=timestamp

    def __repr__(self):
        return f'{self.timestamp} {self.changeType} {self.filename}'


FileChangeFilename=typing.Union[str,Path]
FileChangeCallback=typing.Callable[[FileChange],typing.Optional[bool]]


def waitForFileChange(
    filename:FileChangeFilename,
    onChange:typing.Optional[FileChangeCallback]=None,
    _changeWatcherContext:typing.Optional[typing.Any]=None
    )->typing.Optional[bool]:
    """
    Watch a file or directory for changes.
    This will block until the file changes.

    :filename:
        if this is a file, will call onChange
        with the full path whenever it changes
        if this is a directory, will call onChange
        with the full path to the file in the directory that changes
    :onChange: if this returns True, it means the function
        found what it was looking for and we should exit
        If there is no onChange, simply exits on the first change
    :return: the onChange() result that caused exit

    NOTE: Windows only.

    SEE ALSO:
        https://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html
    """
    # Get the directory and file name
    filename=Path(os.path.abspath(os.path.expandvars(str(filename))))
    if filename.is_dir():
        directoryToWatch=filename
        watchingWholeDirectory=True
    else:
        directoryToWatch=filename.parent
        watchingWholeDirectory=False
    # Open the directory
    hDirectory=win32file.CreateFile( # pylint: disable=c-extension-no-member
        str(directoryToWatch),
        win32con.GENERIC_READ,
        win32con.FILE_SHARE_READ| \
        win32con.FILE_SHARE_WRITE| \
        win32con.FILE_SHARE_DELETE,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_FLAG_BACKUP_SEMANTICS,
        None
    )
    result=None
    if _changeWatcherContext is None:
        _changeWatcherContext=type('',(),{'keepGoing':True})()
    setattr(_changeWatcherContext,'keepGoing',True)
    while _changeWatcherContext.keepGoing:
        # Watch for file modifications within the directory
        results=win32file.ReadDirectoryChangesW( # noqa: E501 # pylint: disable=c-extension-no-member # type: ignore
            hDirectory,
            1024,
            False,
            win32con.FILE_NOTIFY_CHANGE_LAST_WRITE | \
            win32con.FILE_NOTIFY_CHANGE_FILE_NAME | \
            win32con.FILE_NOTIFY_CHANGE_SIZE,
            None,
            None # type: ignore
        )
        results=typing.cast(typing.List[typing.Tuple[int,str]],results)
        for action,actionFilename in results:
            if watchingWholeDirectory or filename.name==actionFilename:
                changeTarget:Path=directoryToWatch/actionFilename
                if onChange is None:
                    _changeWatcherContext.keepGoing=False
                elif action==3:
                    change=FileChange(FileChangeType.UPDATE,changeTarget)
                    result=onChange(change)
                elif action==1:
                    change=FileChange(FileChangeType.CREATE,changeTarget)
                    result=onChange(change)
                elif action==2:
                    change=FileChange(FileChangeType.DELETE,changeTarget)
                    result=onChange(change)
                else:
                    result=None
                if result is not None and result is True:
                    _changeWatcherContext.keepGoing=False
    win32file.CloseHandle(hDirectory) # pylint: disable=c-extension-no-member # type: ignore # noqa: E501
    return result


def watchForFileChange(
    filename:FileChangeFilename,
    onChange:FileChangeCallback
    )->threading.Thread:
    """
    Watch a file or directory for changes.
    This will not block, but will kick off a thread
    and watch until onChange() returns True.

    :filename:
        if this is a file, will call onChange
        with the full path whenever it changes
        if this is a directory, will call onChange
        with the full path to the file in the directory that changes
    :onChange: if this returns True, it means the function
        found what it was looking for and we should exit
        If there is no onChange, simply exits on the first change
    :return: the new thread that is watching for changes
        (You can simply call stop() on when you want to stop watching)

    NOTE: Windows only.

    SEE ALSO:
        https://timgolden.me.uk/python/win32_how_do_i/watch_directory_for_changes.html
    """
    context=type('',(),{'keepGoing':True})()
    thread=threading.Thread(
        target=waitForFileChange,args=[filename,onChange,context])
    setattr(thread,'context',context)
    def stop(self:threading.Thread):
        self.context.keepGoing=False # type: ignore
        self.join()
    setattr(thread,'stop',stop)
    thread.start()
    return thread


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    import time
    exitOnChange=False
    printHelp=False
    filenames:typing.List[str]=[]
    for arg in args:
        if arg.startswith('-'):
            kw=arg.split('=',1)
            k=kw[0].lower()
            if k in ('-h','--help'):
                printHelp=True
            elif k in ('-x','--exitonchange'):
                exitOnChange=True
        else:
            filenames.append(arg)
    if not filenames:
        printHelp=True
    if printHelp:
        print("USAGE: fileWatch.py [flags] [filenames]")
        print("FLAGS:")
        print("  -h ................. print this help")
        print("  --help ............. print this help")
        print("  -x ................. stop watching when the file changes")
        print("                       (if not, watches forever)")
        print("  --exitOnChange ..... stop watching when the file changes")
        print("                       (if not, watches forever)")
        return 1
    def onFileChange(change:FileChange)->bool:
        print(change)
        return exitOnChange
    threads=[watchForFileChange(f,onFileChange) for f in filenames]
    keepGoing=True
    while keepGoing:
        time.sleep(0.250)
        keepGoing=False
        for t in threads:
            if t.context.keepGoing: # type: ignore
                keepGoing=True
                break
    return 0


if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))
