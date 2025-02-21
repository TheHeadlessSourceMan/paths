"""
Tools to make working with pathlib paths easier
"""
import typing
from pathlib import Path
from .urlTyping import UrlCompatible,asUrl


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
