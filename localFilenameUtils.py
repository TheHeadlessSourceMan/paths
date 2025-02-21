"""
Tools to make working with local filenames easier
"""
import typing
import os
import re
from pathlib import Path
from .urlTyping import UrlCompatible,asUrl


invalidWindowsFilenameCharactersRe=re.compile(r'[<>:"/\\|?*\x00-\x1F\x7F]')
def sanitizeWindowsFilename(filename:str,replacement:str='_')->str:
    r"""
    Sanitize a windows filename

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
    return invalidWindowsFilenameCharactersRe.sub(replacement,filename)


invalidPosixFilenameCharactersRe=re.compile(r'[;&|<>(){}$"\`~#!^\\/\0]')
invalidLinuxFilenameCharactersRe=invalidPosixFilenameCharactersRe
def sanitizePosixFilename(filename:str,replacement:str='_')->str:
    """
    Sanitize a posix (aka Linux) filename

    NOTE: technically only the / character is disallowed,
    but this will also remove shell characters which could
    cause unintended execution, eg "filename.txt; rm /home"

    See also:
    https://stackoverflow.com/questions/1311037/are-there-any-invalid-linux-filenames
    https://superuser.com/questions/1499950/what-are-invalid-names-for-a-directory-under-linux
    """
    return invalidPosixFilenameCharactersRe.sub(replacement,filename)
sanitizeLinuxFilename=sanitizePosixFilename


def sanitizeLocalFilename(filename:str,replacement:str='_')->str:
    """
    Sanitize a filename for the local operating system
    """
    if os.name=='nt':
        return sanitizeWindowsFilename(filename,replacement)
    return sanitizePosixFilename(filename,replacement)
sanitizFilename=sanitizeLocalFilename


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
