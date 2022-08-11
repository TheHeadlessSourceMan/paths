"""
Simple wrapper to distinguish a MIME type from a regular old string
"""
import typing


class IsFileWithMime(typing.Protocol):
    """
    a file object with a .mime member
    """
    mime:"MimeTypeCompatible"

class IsFileWithMimeType(typing.Protocol):
    """
    a file object with a .mimeType member
    """
    mimeType:"MimeTypeCompatible"


MimeTypeCompatible=typing.Union[str,"MimeType",IsFileWithMime,IsFileWithMimeType]


def asMimeType(mime:MimeTypeCompatible)->"MimeType":
    """
    Always returns a MimeType.  Will either return mime as-is
    or create a new MimeType if there is not one already.
    """
    if isinstance(mime,MimeType):
        return mime
    return MimeType(mime)


class MimeType:
    """
    Simple wrapper to distinguish a MIME type from a regular old string
    """
    def __init__(self,mimeType:MimeTypeCompatible):
        self._mimeType:str=''
        self.assign(mimeType)

    def assign(self,mimeType:MimeTypeCompatible)->None:
        """
        assign the value of this mimetype
        """
        mm:typing.Any=mimeType
        if isinstance(mimeType,str):
            self._mimeType=mimeType
        elif hasattr(mm,'mime'):
            self.assign(mm.mime)
        elif hasattr(mm,'mimeType'):
            self.assign(mm.mimeType)
        else:
            self._mimeType=str(mimeType)

    def __eq__(self,other:typing.Any)->bool:
        if not isinstance(other,MimeType):
            if isinstance(other,str):
                return self._mimeType==other
            elif hasattr(other,'mime'):
                return self==other.mime
            elif hasattr(other,'mimeType'):
                return self==other.mimeType
            else:
                return False
        return other._mimeType==self._mimeType

    def __repr__(self)->str:
        return self._mimeType