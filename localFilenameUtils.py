"""
Tools to make working with local filenames easier
"""
import typing
import os
import re
from pathlib import Path
from .urlTyping import UrlCompatible,asUrl


filenameSymbolToName={
    ';':'SEMICOLON',
    '&':'AMPRESAND',
    '(':'OPENPAREN',
    ')':'CLOSEPAREN',
    '{':'OPENBRACKET',
    '}':'CLOSEBRACKET',
    '$':'DOLLARSIGN',
    '`':'TICK',
    '~':'TILDE',
    '#':'POUND',
    '!':'EXCLAMATIONPOINT',
    '^':'CARET',
    '<':'LESSTHAN',
    '>':'GREATERTHAN',
    ':':'COLON',
    '"':'QUOTE',
    '/':'FORWARDSLASH',
    '\\':'BACKSLASH',
    '|':'PIPE',
    '?':'QUESTIONMARK',
    '*':'ASTERISK',
    '.':'DOT',
    '\x7F':'Ox7F',
    '_vti_':'UNDERSCOREVTI'
}
filenameNameToSymbol=dict([(v,k) for k,v in filenameSymbolToName.items()])


invalidWindowsFilenameCharactersRe=re.compile(
    r'[<>:"/\\|?*\x00-\x1F\x7F]|_vti_')
invalidWindowsFilenamesRe=re.compile(
    r'CON|PRN|AUX|NUL|COM[0-9]+|LPT[0-9]+|\.lock')
def sanitizeWindowsFilename(
    filename:str,
    delimiter:typing.Optional[str]=None,
    replacement:typing.Optional[str]=None,
    expandEnvironment:typing.Optional[bool]=True
    )->str:
    r"""
    Sanitize a windows filename

    :delimiter: if specified, use this string as a delimiter, such that
        1) exsisting delimiters in string are replaced with
            delimiter*2
        2) delimited characters in string are replaced with
            delimiter+CODE+delimiter
        NOTE: replacing by delimiter is reversable, but replacing by
        replacement is not
        NOTE: If neihter replacement nor delimiter is specified,
        assumes delimiter='_'
    :replacement: instead of a full delimiter, perform a simple replacement

    NOTE: this function is intended for just a single filename
    or directory, so saying "/home/file.txt" will become "_home_file.txt"
    If this is not what you want, you may need to split it before sending in.

    In Windows, certain characters are not permitted in filenames due
    to their special functions within the operating system.
    These restricted characters are:
        \/:*?"<>|

    Additionally, filenames cannot contain control characters with
    ASCII codes ranging from 0 to 31.
    See:
    https://learn.microsoft.com/en-us/dotnet/api/system.io.path.getinvalidfilenamechars?view=net-9.0

    Furthermore, Windows reserves certain specific filenames including:
        "CON","PRN","AUX","NUL","COM0"-"COM9","LPT0"-"LPT9"
    These reserved names are used by the system for specific purposes
    and cannot be used as filenames.
    See:
    https://support.microsoft.com/en-us/office/restrictions-and-limitations-in-onedrive-and-sharepoint-64883a5d-228e-48f5-b3d2-eb39e07630fa

    See also:
    https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file
    """
    filename=str(filename)
    if expandEnvironment:
        filename=os.path.expandvars(filename)
    if replacement is None:
        if delimiter is None:
            delimiter='_'
        # replace the delimiter character by doubling it up
        filename=filename.replace(delimiter,delimiter+delimiter)
        # replace all tokens anywhere in the string
        ret=[]
        lastpos=0
        for m in invalidWindowsFilenameCharactersRe.finditer(filename):
            if lastpos!=m.start():
                ret.append(filename[lastpos:m.start()])
            found=m.group(0)
            # first need to handle some special cases that don't lend
            # themselves well to a dict structure
            if len(found)==1 and found[0]<='\x1F':
                ret.append('0x%02X'%found.decode('ascii',errors='ignore')[0])
            else:
                ret.append(filenameSymbolToName[found])
        if lastpos<len(found)-1:
            ret.append(filename[lastpos:])
        filename=''.join(ret)
        # replace a ~$ thing at the beginning of the string
        if filename.startswith('~$'):
            filename=f"{replacement}{filenameSymbolToName['!']}{replacement}{delimiter}{filenameSymbolToName['$']}{delimiter}" # noqa: E501 # pylint: disable=line-too-long
        else:
            # replace any whole filenames the system needs
            m=invalidWindowsFilenamesRe.match(filename)
            if m is not None:
                filename=f"{replacement}{m.group()}{replacement}"
    else: # we are doing a simple replacement
        # just use simple regex replacement
        filename=invalidWindowsFilenameCharactersRe.sub(replacement,filename)
        if filename.startswith('~$'):
            filename=replacement+filename[2:]
        m=invalidWindowsFilenamesRe.match(filename)
        if m is not None:
            filename='_'+filename
    return filename
escapeWindowsFilename=sanitizeWindowsFilename


invalidPosixFilenameCharactersRe=re.compile(
    r'[;&|<>(){}$"\`~#!^\\/\0]')
invalidLinuxFilenameCharactersRe=invalidPosixFilenameCharactersRe
def sanitizePosixFilename(
    filename:str,
    delimiter:typing.Optional[str]=None,
    replacement:typing.Optional[str]=None,
    expandEnvironment:typing.Optional[bool]=True)->str:
    """
    Sanitize a posix (aka Linux) filename

    :delimiter: if specified, use this string as a delimiter, such that
        1) exsisting delimiters in string are replaced with
            delimiter*2
        2) delimited characters in string are replaced with
            delimiter+CODE+delimiter
        NOTE: replacing by delimiter is reversable, but replacing by
        replacement is not
        NOTE: If neihter replacement nor delimiter is specified,
        assumes delimiter='_'
    :replacement: instead of a full delimiter, perform a simple replacement

    NOTE: this function is intended for just a single filename
    or directory, so saying "/home/file.txt" will become "_home_file.txt"
    If this is not what you want, you may need to split it before sending in.

    NOTE: technically only the / character is disallowed,
    but this will also remove shell characters which could
    cause unintended execution, eg "filename.txt; rm /home"

    See also:
    https://stackoverflow.com/questions/1311037/are-there-any-invalid-linux-filenames
    https://superuser.com/questions/1499950/what-are-invalid-names-for-a-directory-under-linux
    """
    filename=str(filename)
    if expandEnvironment:
        filename=os.path.expandvars(filename)
    if replacement is None:
        if delimiter is None:
            delimiter='_'
        # replace the delimiter character by doubling it up
        filename=filename.replace(delimiter,delimiter+delimiter)
        # replace all tokens anywhere in the string
        ret=[]
        lastpos=0
        for m in invalidWindowsFilenameCharactersRe.finditer(filename):
            if lastpos!=m.start():
                ret.append(filename[lastpos:m.start()])
            found=m.group(0)
            # first need to handle some special cases that don't lend
            # themselves well to a dict structure
            if len(found)==1 and found[0]<='\x1F':
                ret.append('0x%02X'%found.decode('ascii',errors='ignore')[0])
            else:
                ret.append(filenameSymbolToName[found])
        if lastpos<len(found)-1:
            ret.append(filename[lastpos:])
        filename=''.join(ret)
    else: # we are doing a simple replacement
        # just use simple regex replacement
        filename=invalidPosixFilenameCharactersRe.sub(replacement,filename)
    return filename
sanitizeLinuxFilename=sanitizePosixFilename
escapePosixFilename=sanitizePosixFilename
escapeLinuxFilename=sanitizeLinuxFilename


def sanitizePath(
    path:typing.Union[str,Path,UrlCompatible,typing.Iterable[str]],
    delimiter:typing.Optional[str]=None,
    replacement:typing.Optional[str]=None,
    useForwardSlashSeparator:typing.Optional[bool]=True,
    useBackSlashSeparator:typing.Optional[bool]=True,
    expandEnvironment:typing.Optional[bool]=True
    )->Path:
    r"""
    Sanitize every step in a path

    :delimiter: if specified, use this string as a delimiter, such that
        1) exsisting delimiters in string are replaced with
            delimiter*2
        2) delimited characters in string are replaced with
            delimiter+CODE+delimiter
        NOTE: replacing by delimiter is reversable, but replacing by
        replacement is not
        NOTE: If neihter replacement nor delimiter is specified,
        assumes delimiter='_'
    :replacement: instead of a full delimiter, perform a simple replacement
    :useForwardSlashSeparator: when decoding string, use / as the separator
        default=True
    :useBackSlashSeparator: when decoding string, use \ as the separator
        default=True
    :expandEnvironment: expand environment variables
        default=True

    Always returns an absolute path that could exist on the system
    """
    if not isinstance(path,str) and hasattr(path,"__iter__"):
        elements=path
    else:
        path=str(path)
        if expandEnvironment:
            path=os.path.expandvars(path)
        if useBackSlashSeparator:
            if useForwardSlashSeparator:
                path=path.replace('/','\\')
            elements=path.split('\\')
        elif useBackSlashSeparator:
            elements=path.split('/')
        else:
            elements=[path]
    elements=[
        sanitizeFilename(element,delimiter,replacement,expandEnvironment=False)
        for element in elements]
    return Path(os.sep.join(elements)).absolute
sanitizeWindowsPath=sanitizePath
sanitizePosixPath=sanitizePath
sanitizeLinuxPath=sanitizePath
escapeWindowsPath=sanitizeWindowsPath
escapePosixPath=sanitizePosixPath
escapeLinuxPath=sanitizeLinuxPath


def deSanitizePath(
    path:typing.Union[str,Path,UrlCompatible],
    delimiter:typing.Optional[str]=None,
    useForwardSlashSeparator:typing.Optional[bool]=True,
    useBackSlashSeparator:typing.Optional[bool]=True,
    expandEnvironment:typing.Optional[bool]=True
    )->typing.Iterable[str]:
    r"""
    deSanitize every step in a path

    In order to ensure that an unescaped element (eg "/")
    is not misinterpreted, will return an array of path elements
    """
    path=str(path)
    if expandEnvironment:
        path=os.path.expandvars(path)
    if useBackSlashSeparator:
        if useForwardSlashSeparator:
            path=path.replace('/','\\')
        elements=path.split('\\')
    elif useBackSlashSeparator:
        elements=path.split('/')
    else:
        elements=[path]
    elements=[
        deSanitizeFilename(element,delimiter)
        for element in elements]
    return elements
deSanitizeWindowsPath=deSanitizePath
deSanitizePosixPath=deSanitizePath
deSanitizeLinuxPath=deSanitizePath
unescapeWindowsPath=deSanitizeWindowsPath
unescapePosixPath=deSanitizePosixPath
unescapeLinuxPath=deSanitizeLinuxPath


def sanitizeLocalFilename(
    filename:str,
    delimiter:typing.Optional[str]=None,
    replacement:typing.Optional[str]=None,
    expandEnvironment:typing.Optional[bool]=True
    )->str:
    """
    Sanitize a filename for the local operating system.

    :delimiter: if specified, use this string as a delimiter, such that
        1) exsisting delimiters in string are replaced with
            delimiter*2
        2) delimited characters in string are replaced with
            delimiter+CODE+delimiter
        NOTE: replacing by delimiter is reversable, but replacing by
        replacement is not
        NOTE: If neihter replacement nor delimiter is specified,
        assumes delimiter='_'
    :replacement: instead of a full delimiter, perform a simple replacement

    :expandEnvironment: expand environment variables
        default=True

    NOTE: this function is intended for just a single filename
    or directory, so saying "/home/file.txt" will become "_home_file.txt"
    If this is not what you want, you may need to split it before sending in.
    """
    if os.name=='nt':
        return sanitizeWindowsFilename(
            filename,delimiter,replacement,expandEnvironment)
    return sanitizePosixFilename(
        filename,delimiter,replacement,expandEnvironment)
sanitizeFilename=sanitizeLocalFilename
escapeLocalFilename=sanitizeLocalFilename
escapeFilename=sanitizeLocalFilename


def deSanitizeLocalFilename(filename:str,delimiter:str='_')->str:
    """
    Reverse the operation of a sanatizeFilename by delimiter.
    Used as a pair, these functions can be useful for
    encoding/decoding any string as a filename

    If there are instances of delimiter that we cannot interpret,
    assume that the whole filename is not delimited at all.
    (This is to mitigate modifying non-delimited filenames that
    just so happen to have the delimiter we are looking for.)

    NOTE: this function is intended for just a single filename
    or directory, so saying "/home/file.txt" will become "_home_file.txt"
    If this is not what you want, you may need to split it before sending in.

    NOTE: deSanitize is portable so filenames sanitized on one os
    can be deSanitized on another
    """
    # first check to see if the whole thing is a special filename
    if filename.startswith(delimiter) and filename.endswith(delimiter):
        wholeFilename=filename[len(delimiter),-len(delimiter)]
        if invalidWindowsFilenamesRe.match(wholeFilename) is not None:
            return wholeFilename
    # now split apart by delimiter
    done=False
    lastIdx=0
    isInsideDelimiter=False
    ret=[]
    while not done:
        idx=filename.find(delimiter,lastIdx)
        if idx<0:
            done=True
            idx=len(filename)-1 # be sure to eat the remainder
        if isInsideDelimiter: # we are leaving a delimiter section
            # decode it
            if idx-lastIdx==1:
                # it was a double-delimiter with nothing inside
                ret.append(delimiter)
            else:
                symbol=filenameNameToSymbol.get(filename[lastIdx:idx])
                if symbol is None:
                    # found an unrecognized symbol, so accept
                    # full filename as-is
                    return filename
                ret.append(symbol)
            isInsideDelimiter=False
        else: # we are entering a delimiter section
            # append plain text
            ret.append(filename[lastIdx:idx])
            isInsideDelimiter=True
        lastIdx=idx
    return ''.join(ret)
deSanitizeFilename=deSanitizeLocalFilename
deSanitizeWindowsFilename=deSanitizeLocalFilename
deSanitizePosixFilename=deSanitizeLocalFilename
deSanitizeLinuxFilename=deSanitizeLocalFilename
unescapeLocalFilename=deSanitizeLocalFilename
unescapeFilename=deSanitizeFilename
unescapeWindowsFilename=deSanitizeWindowsFilename
unescapePosixFilename=deSanitizePosixFilename
unescapeLinuxFilename=deSanitizeLinuxFilename


def asPathlibPath(urlOrPath:typing.Union[str,Path,UrlCompatible])->Path:
    """
    Always return as a pathlib Path on the local filesystem.

    If this is a url and not file:// will raise FileNotFoundError
    """
    if isinstance(urlOrPath,Path):
        # if it's a path, we do want to create a duplicate
        # to make it immutable
        return Path(urlOrPath)
    urlOrPathUrl=asUrl(urlOrPath).filePath
    if urlOrPathUrl is None:
        raise FileNotFoundError(f'Path must be local "{urlOrPath}"')
    return urlOrPathUrl


def asLocalPath(urlOrPath:typing.Union[str,Path,UrlCompatible])->Path:
    """
    Always return as a path string on the local filesystem.

    If this is a url and not file:// will raise FileNotFoundError
    """
    return str(asPathlibPath(urlOrPath))
