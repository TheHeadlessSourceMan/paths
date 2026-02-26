"""
Errors to go with this class
"""
import typing


class DecodeError(Exception):
    """
    General purpose error when attempting to decode some data
    """
    if typing.TYPE_CHECKING:
        from paths import URL,UrlWithFileLocation

    def __init__(self,
        occurredIn:typing.Union[None,str,"UrlWithFileLocation","URL"]):
        """ """
        self.occurredIn=occurredIn # save a copy to provide info to catchers
        if occurredIn is None:
            occurredIn=''
        msg=f'Error while attempting to decode {occurredIn}'
        Exception.__init__(self,msg)


class EncodeError(Exception):
    """
    General purpose error when attempting to encode some data
    """
    if typing.TYPE_CHECKING:
        from paths import URL,UrlWithFileLocation

    def __init__(self,
        occurredIn:typing.Union[None,str,"UrlWithFileLocation","URL"]):
        """ """
        self.occurredIn=occurredIn # save a copy to provide info to catchers
        if occurredIn is None:
            occurredIn=''
        msg=f'Error while attempting to encode {occurredIn}'
        Exception.__init__(self,msg)


class NonIterableDirectory(Exception):
    """
    For urls like http:// you cannot (usually) get a directory listing
    """
    if typing.TYPE_CHECKING:
        from paths import URL,UrlWithFileLocation

    def __init__(self,
        occurredIn:typing.Union[None,str,"UrlWithFileLocation","URL"]):
        """ """
        self.occurredIn=occurredIn # save a copy to provide info to catchers
        if occurredIn is None:
            occurredIn=''
        msg=f'Unable to iterate directory for {occurredIn}'
        Exception.__init__(self,msg)


class UnknownBaseDirectory(Exception):
    """
    For urls where it is impossible to figure out what the base directory is
    """
    if typing.TYPE_CHECKING:
        from paths import URL,UrlWithFileLocation

    def __init__(self,
        occurredIn:typing.Union[None,str,"UrlWithFileLocation","URL"]):
        """ """
        self.occurredIn=occurredIn # save a copy to provide info to catchers
        if occurredIn is None:
            occurredIn=''
        msg=f'Unable to determine base directory for {occurredIn}'
        Exception.__init__(self,msg)


class MalformedURL(Exception):
    """
    This is thrown when a url is in bad form
    """

    def __init__(self,url:str,reason:str,altMessage:typing.Optional[str]=None):
        if altMessage:
            Exception.__init__(self,altMessage)
        else:
            Exception.__init__(self,f'Malformed URL "{url}"\n({reason})')


class MalformedFilename(MalformedURL):
    """
    This is thrown when a filename is in bad form
    """

    def __init__(self,filename:str,reason:str,altMessage:typing.Optional[str]=None):
        if altMessage:
            MalformedURL.__init__(self,'','',altMessage)
        else:
            MalformedURL.__init__(self,'','',f'Malformed Filename "{filename}"\n({reason})')
