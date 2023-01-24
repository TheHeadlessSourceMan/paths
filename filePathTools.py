"""
tools for working with file paths
"""
import typing
import paths


def illegalCharsForOs(osName:typing.Optional[str]=None)->str:
    """
    get all characters that are illegal to use in a filename

    osName: if not given, use the current os

    TODO: need to research this!!!
    """
    if osName is None:
        import sys
        osName=sys.platform
    if osName=='nt':
        return r'*"/;|=,'
    return r'*":;|=,\\'


def enquoteFilePath(filePath:str)->str:
    """
    Place a file path in quotes if necessary.
    """
    if filePath.find(' ')>=0:
        filePath=filePath.replace('"',r'\"')
        return f'"{filePath}"'
    return filePath


def encodeFilePath(
    filePath:str,
    enquote:bool=True,
    illegalChars:typing.Optional[str]=None,
    osName:typing.Optional[str]=None,
    errors:str='exception'
    )->str:
    """
    Encodes a file path's special characters.
    By default, this will also call self.enquoteFilePath() when done.

    enquote: whether to call enquoteFilePath() default=True
    illegalChars: a string of illegal filename characters - if None, use os alone
    osName: os type to obtain illegalChars from (compatible with sys.name)
        if not specified, use just illegalChars
        if neither is specified, use os=sys.name
    errors: works similarly to str.encode("",errors="ignore")
        can be "ignore" or "exception"(default) or something else to replace the chars with
    """
    if illegalChars is None:
        illegalChars=illegalCharsForOs(osName)
    elif osName is not None:
        illegalChars=illegalChars+illegalCharsForOs(osName)
    if errors=='exception':
        for c in illegalChars:
            if c in filePath:
                msg='"%s" encountered illegal character "%s"'%(filePath,c)
                raise paths.DecodeError(msg)
        if enquote:
            return enquoteFilePath(filePath)
        return filePath
    if errors=='ignore':
        errors=''
    for c in illegalChars:
        filePath=filePath.replace(c,errors)
    if enquote:
        return enquoteFilePath(filePath)
    return filePath


def filenameFixer(
    filename:str,
    replaceWith='_',osName:typing.Optional[str]=None
    )->str:
    """
    Attempt to fix up a filename by removing illegal characters

    NOTE: be sure to ONLY include the filename, not a path
    """
    for i in illegalCharsForOs(osName):
        if filename.find(i)>0:
            filename=filename.replace(i,replaceWith)
    return filename