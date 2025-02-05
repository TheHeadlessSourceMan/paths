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
        occouredIn:typing.Union[None,str,"UrlWithFileLocation","URL"]):
        """ """
        self.occouredIn=occouredIn # save a copy to provide info to catchers
        if occouredIn is None:
            occouredIn=''
        msg=f'Error while attempting to decode {occouredIn}'
        Exception.__init__(self,msg)


class EncodeError(Exception):
    """
    General purpose error when attempting to encode some data
    """
    if typing.TYPE_CHECKING:
        from paths import URL,UrlWithFileLocation

    def __init__(self,
        occouredIn:typing.Union[None,str,"UrlWithFileLocation","URL"]):
        """ """
        self.occouredIn=occouredIn # save a copy to provide info to catchers
        if occouredIn is None:
            occouredIn=''
        msg=f'Error while attempting to encode {occouredIn}'
        Exception.__init__(self,msg)


class MalformedURL(Exception):
    """
    This is thrown when a url is in bad form
    """

    def __init__(self,url:str,reason:str):
        Exception.__init__(self,f'Malformed URL "{url}"\n({reason})')
