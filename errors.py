"""
Errors to go with this class
"""
import typing
from .iFileLocation import IFileLocation
from .iUrl import IURL


class DecodeError(Exception):
    """
    General purpose error when attempting to decode some data
    """
    def __init__(self,occouredIn:typing.Union[None,str,IFileLocation,IURL]):
        self.occouredIn=occouredIn # save a copy to provide info to catchers
        if occouredIn is None:
            occouredIn=''
        msg=f'Error while attempting to decode {occouredIn}'
        Exception.__init__(self,msg)


class EncodeError(Exception):
    """
    General purpose error when attempting to encode some data
    """
    def __init__(self,occouredIn:typing.Union[None,str,IFileLocation,IURL]):
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
        Exception.__init__(self,'Malformed URL "'+url+'"\n('+reason+')')
