"""
Handy way of adding loading/saving to any data type.

Simply derive class MyClass(LoadAndSave) and then implement
_encode(self)->data and _decode(self,data)

This will let you load not only local files, but also
more advanced stuff like html and ftp.

If ezFs is installed, it gets even more wild, allowing access into
online file stores, compressed files, and more!
"""
import typing
from .urlTyping import URLCompatible


def defaultLoader(f:URLCompatible)->bytes:
    """
    load from a file-like object, filename, or url of type
        file://
        ftp://
        http://
        ** sftp://
        ** https://

    if a file-like object is passed in, will simply read it

    If EzFs is installed, it can load any installed filesystem including
        dropbox,google drive,zipped files,... you name it!
    """
    import paths
    if not isinstance(f,paths.URL):
        if hasattr(f,'read') and callable(f.read): # type: ignore
            return f.read()  # type: ignore
        f=paths.URL(f)
    #try:
    #    from ezFs import EzFs
    #    return EzFs(f).read() # type: ignore
    #except ImportError:
    #    pass
    f=paths.asURL(f)
    if f.protocol!='file':
        import urllib.request
        headers={'User-Agent':'Mozilla 5.10'} # some servers only like "real browsers" # noqa: E501 # pylint: disable=line-too-long
        request=urllib.request.Request(str(f.url),None,headers)
        response=urllib.request.urlopen(request)
        return response.read()
    with open(f.filePath,'rb') as f: # type: ignore
        return f.read() # type: ignore

def defaultSaver(f:URLCompatible,data:bytes)->None:
    """
    save to a file-like object, filename, or url of type
        file://
        ftp://
        http://
        ** sftp://
        ** https://

    if a file-like object is passed in, will simply write it

    If EzFs is installed, it can save any installed filesystem including
        dropbox,google drive,zipped files,... you name it!
    """
    import paths
    if not isinstance(f,paths.URL):
        if hasattr(f,'write'):
            f.write(data) # type: ignore
            return
        f=paths.URL(f)
    #try:
    #    from ezFs import EzFs
    #    EzFs(f).write(data)  # type: ignore
    #    return
    #except ImportError:
    #    pass
    if f.protocol!='file':
        import urllib.request
        headers={'User-Agent':'Mozilla 5.10'} # some servers only like "real browsers" # noqa: E501 # pylint: disable=line-too-long
        request=urllib.request.Request(str(f.url),data,headers,method='PUT')
        _=urllib.request.urlopen(request)
        return
    f.write(data)
    f.close()


ParamsDict=typing.Dict[str,typing.Any]


class LoadAndSaveBytes:
    """
    Handy way of adding loading/saving to any data type.

    Simply derive class MyClass(LoadAndSave) and then implement
    _encode(self)->data and/or _decode(self,data)
    (by not implementing one or the other, then LoadAndSave
    knows it cannot do that)

    This will let you load not only local files, but more advanced stuff
    like html and ftp.

    If ezFs is installed, it gets even more wild, allowing access into online
    file stores, compressed files, and more!
    """
    if typing.TYPE_CHECKING:
        from paths import URL

    DefaultFilename:str='UNDEFINED.dat'

    _encodeBytes:typing.Optional[typing.Callable[[],bytes]]=None
    _decodeBytes:typing.Optional[typing.Callable[[bytes],None]]=None
    _encodeStr:typing.Optional[typing.Callable[[],str]]=None
    _decodeStr:typing.Optional[typing.Callable[[str],None]]=None

    def __init__(self,
        filename:typing.Optional[URLCompatible]=None,
        data:typing.Optional[bytes]=None):
        """ """
        import paths
        self._filename:typing.Optional[paths.URL]=None
        if data is not None:
            self.decode(data)
            if filename is not None:
                self._filename=paths.URL(filename)
        elif filename is not None:
            self.load(filename)

    def decode(self,data:bytes)->None:
        """
        same as decodeBytes
        """
        self.decodeBytes(data)
    @typing.final
    def decodeBytes(self,data:bytes)->None:
        """
        Decode from raw bytes

        Will raise an error if there is no decoder for this type
        (you can check with self.canLoad)

        :param data: [description]
        :type data: bytes
        :raises Exception: [description]
        """
        if self._decodeBytes is None:
            if self._decodeStr is None:
                raise Exception('Cannot load this kind of data')
            self._decodeStr(data.decode('utf-8',errors='ignore')) # pylint: disable=not-callable
        else:
            self._decodeBytes(data) # pylint: disable=not-callable

    def encode(self)->bytes:
        """
        same as encodeBytes
        """
        return self.encodeBytes()
    @typing.final
    def encodeBytes(self)->bytes:
        """
        Encode to raw bytes

        Will raise an error if there is no encoder for this type
        (you can check with self.canSave)

        :param data: [description]
        :type data: bytes
        :raises Exception: [description]
        """
        if self._encodeBytes is None:
            if self._encodeStr is None:
                raise Exception('Cannot save this kind of data')
            return self._encodeStr().encode('utf-8',errors='ignore') # pylint: disable=not-callable
        return self._encodeBytes() # pylint: disable=not-callable

    @property
    def filename(self)->typing.Optional["URL"]:
        """
        Setting this is the same as saying load(filename)
        """
        return self._filename
    @filename.setter
    def filename(self,filename:URLCompatible):
        self.load(filename)
    @property
    def url(self)->typing.Union["URL",None]:
        """
        same as filename
        """
        return self._filename
    @url.setter
    def url(self,url:URLCompatible):
        self.load(url)

    def canLoad(self)->bool:
        """
        can this load files?
        """
        return self._decodeBytes is not None

    def canSave(self)->bool:
        """
        can this save files?
        """
        return self._encodeBytes is not None

    def load(self,
        filename:typing.Optional[URLCompatible]=None,
        altDecoder:typing.Optional[typing.Callable[[bytes],None]]=None,
        altDecoderParams:typing.Optional[ParamsDict]=None
        )->None:
        """
        load from a file-like object, filename, or url of type
            file://
            ftp://
            http://
            ** sftp://
            ** https://

        if a file-like object is passed in, will simply read it

        If EzFs is installed, it can load any installed filesystem including
            dropbox,google drive,zipped files,... you name it!

        if no filename, will reload the current file

        :param filename: url to load, defaults to None
        :type filename: paths.URLCompatible, optional
        :param altDecoder: alternative decoder as opposed to self._decode
            (used to circumvent normal loading. usually you won't need this)
            defaults to None
        :type altDecoder: Callable[[bytes,...],None], optional
        :param altDecoderParams: extra params dict to pass to altDecoder
            defaults to None
        :type altDecoderParams: Dict[str,Any], optional
        """
        import paths
        if filename is None:
            if self._filename is None:
                return
            filename=self._filename
        else:
            self._filename=paths.URL(filename)
        data=defaultLoader(filename)
        if altDecoder is not None:
            if altDecoderParams is not None:
                altDecoder(data,**altDecoderParams) # type: ignore
            else:
                altDecoder(data)
        elif self._decodeBytes is None:
            raise Exception('Cannot load this kind of data')
        else:
            self._decodeBytes(data)

    def save(self,
        filename:typing.Optional[URLCompatible]=None,
        altEncoder:typing.Optional[typing.Callable[...,bytes]]=None,
        altEncoderParams:typing.Optional[ParamsDict]=None
        )->None:
        """
        save to a file-like object, filename, or url of type
            file://
            ftp://
            http://
            ** sftp://
            ** https://

        if a file-like object is passed in, will simply write it

        If EzFs is installed, it can save any installed filesystem including
            dropbox,google drive,zipped files,... you name it!

        if no filename, save over the current filename
            (and if there is no current filename will
            save as self.DefaultFilename)

        :param filename: filename to save as, defaults to None
        :type filename: paths.URLCompatible, optional
        :param altEncoder: alternative decoder as opposed to self._decode
            (used to circumvent normal loading. usually you won't need this)
            defaults to None
        :type altEncoder: Callable[[...],bytes], optional
        :param altEncoderParams:  extra params dict to pass to altEncoder
            defaults to None
        :type altEncoderParams: Dict[str,Any], optional
        """
        import paths
        if filename is None:
            if self._filename is None:
                filename=self.DefaultFilename
            else:
                filename=self._filename
        else:
            self._filename=paths.asURL(filename)
        if altEncoder is not None:
            if altEncoderParams is not None:
                data=altEncoder(**altEncoderParams)
            else:
                data=altEncoder()
        elif self._encodeBytes is None:
            raise Exception('Cannot save this kind of data')
        else:
            data=self._encodeBytes()
        defaultSaver(filename,data)

    def __repr__(self)->str:
        return str(self._filename)


class LoadAndSave(LoadAndSaveBytes):
    """
    Handy way of adding loading/saving to any data type.

    Simply derive class MyClass(LoadAndSave) and then implement
    _encode(self)->data and/or _decode(self,data)
    (by not implementing one or the other, then LoadAndSave
    knows it cannot do that)

    This will let you load not only local files, but more advanced stuff
    like html and ftp.

    If ezFs is installed, it gets even more wild, allowing access into online
    file stores, compressed files, and more!

    RECOMMENDED:
        Auto text decoding gets better if chardet and/or
        BeautifulSoup are installed
        pip install chardet bs4
    """

    DefaultFilename:str='UNDEFINED.txt'
    def _encode(self)->bytes:
        return bytes()
    _encode=None # noqa: F811 # type: ignore
    def _decode(self,data:bytes)->None:
        _=data
    _decode=None # noqa: F811 # type: ignore

    def __init__(self,
        filename:typing.Optional[URLCompatible]=None,
        data:typing.Optional[str]=None,
        encoding:typing.Optional[str]=None):
        """ """
        self.encoding:typing.Optional[str]=encoding
        if data is not None:
            self.decode(data)
            LoadAndSaveBytes.__init__(self)
        else:
            LoadAndSaveBytes.__init__(self,filename)

    def _detectEncoding(self,data:bytes)->str:
        """
        detect the best encoding for a block of bytes

        RECOMMENDED:
            Auto text decoding gets better if chardet and/or
            BeautifulSoup are installed
            pip install chardet bs4

        :param data: a block of bytes
        :type data: bytes
        :return: encoding type
        :rtype: str
        """
        try:
            from bs4 import UnicodeDammit
            ud=UnicodeDammit(data) # also uses chardet if installed
            if ud.original_encoding is not None:
                return ud.original_encoding
        except ImportError:
            pass
        try:
            import chardet  # type: ignore
            result=chardet.detect(data)
            if result is not None and 'encoding' in result:
                return result['encoding']
        except ImportError:
            pass
        return 'UTF-8'

    def _decodeBytes(self, # pylint: disable=arguments-differ # type: ignore
        data:bytes,
        errors:str='ignore',
        altDecoder:typing.Optional[typing.Callable[[str],str]]=None,
        altDecoderParams:typing.Optional[ParamsDict]=None
        )->None:
        """
        Decode this data from bytes using self.encoding.

        If encoding is not specified, will attempt to guess.

        :param data: data to decode
        :type data: bytes
        """
        if not self.canLoad() and altDecoder is None:
            raise Exception('Cannot load this kind of data')
        encoding=self.encoding
        if encoding is None:
            encoding=self._detectEncoding(data)
            self.encoding=encoding
        textData=data.decode(encoding,errors=errors)
        if altDecoder is not None:
            if altDecoderParams is not None:
                altDecoder(textData,**altDecoderParams) # type: ignore
            else:
                altDecoder(textData)
        else:
            self.decode(textData)

    def _encodeBytes(self, # pylint: disable=arguments-differ # type: ignore
        altEncoder:typing.Optional[typing.Callable[[str],str]]=None,
        altEncoderParams:typing.Optional[ParamsDict]=None
        )->bytes:
        """
        Decode this data from bytes using self.encoding.

        If encoding is not specified, will attempt to guess.

        :param data: data to decode
        :type data: bytes
        """
        if self._encode is None and altEncoder is None:
            raise Exception('Cannot save this kind of data')
        textData=''
        encoding=self.encoding
        if encoding is None:
            encoding='UTF-8' # when in doubt, save as the old reliable
            self.encoding=encoding
        if altEncoder is not None:
            if altEncoderParams is not None:
                textData=altEncoder(textData,**altEncoderParams) # type: ignore
            else:
                textData=altEncoder(textData)
        elif self._encode is None:
            raise Exception('Cannot save this kind of data')
        else:
            textData=self._encode()
        if isinstance(textData,str):
            textData=textData.encode(encoding)
        return textData

    def decode(self,data:typing.Union[bytes,str])->None:
        """
        Decode from text or raw bytes

        Will raise an error if there is no decoder for this type
        (you can check with self.canLoad)

        :param data: [description]
        :type data: bytes
        :raises Exception: [description]
        """
        if isinstance(data,bytes):
            self._decodeBytes(data)
        else:
            if self._decode is None:
                raise Exception('Cannot load this kind of data')
            self._decodeStr(data) # type: ignore # pylint: disable=not-callable

    def encode(self)->str:
        """
        Encode to text

        Will raise an error if there is no encoder for this type
        (you can check with self.canSave)

        :param data: [description]
        :type data: bytes
        :raises Exception: [description]
        """
        if self._encode is None:
            raise Exception('Cannot save this kind of data')
        return self._encodeStr() # type: ignore # pylint: disable=not-callable

    def load(self,  # type: ignore
        filename:typing.Optional[URLCompatible]=None,
        altDecoder:typing.Optional[typing.Callable[[str],str]]=None,
        altDecoderParams:typing.Optional[ParamsDict]=None
        )->None:
        """
        load from a file-like object, filename, or url of type
            file://
            ftp://
            http://
            ** sftp://
            ** https://

        if a file-like object is passed in, will simply read it

        If EzFs is installed, it can load any installed filesystem including
            dropbox,google drive,zipped files,... you name it!

        if no filename, will reload the current file

        :param filename: url to load, defaults to None
        :type filename: paths.URLCompatible, optional
        :param altDecoder: alternative decoder as opposed to self._decode
            (used to circumvent normal loading. usually you won't need this)
            defaults to None
        :type altDecoder: Callable[[bytes,...],None], optional
        :param altDecoderParams: extra params dict to pass to altDecoder
            defaults to typing.Optional[typing.Dict[str,typing.Any]]=None
        :type altDecoderParams: Dict[str,Any], optional
        """
        if not self.canLoad() and altDecoder is None:
            raise Exception('Cannot load this kind of data')
        LoadAndSaveBytes.load(self,filename,
            altDecoder=self._decodeBytes,altDecoderParams=altDecoderParams)

    def save(self, # type: ignore
        filename:typing.Optional[URLCompatible]=None,
        altEncoder:typing.Optional[typing.Callable[...,str]]=None,
        altEncoderParams:typing.Optional[ParamsDict]=None
        )->None:
        """
        save to a file-like object, filename, or url of type
            file://
            ftp://
            http://
            ** sftp://
            ** https://

        if a file-like object is passed in, will simply write it

        If EzFs is installed, it can save any installed filesystem including
            dropbox,google drive,zipped files,... you name it!

        if no filename, save over the current filename
            (and if there is no current filename will
            save as self.DefaultFilename)

        :param filename: filename to save as, defaults to None
        :type filename: paths.URLCompatible, optional
        :param altEncoder: alternative decoder as opposed to self._decode
            (used to circumvent normal loading. usually you won't need this)
            defaults to None
        :type altEncoder: Callable[[...],str], optional
        :param altEncoderParams:  extra params dict to pass to altEncoder
            defaults to typing.Optional[typing.Dict[str,typing.Any]]=None
        :type altEncoderParams: Dict[str,Any], optional
        """
        import paths
        if not self.canSave() and altEncoder is None:
            raise Exception('Cannot save this kind of data')
        if filename is None:
            if self._filename is None:
                filename=self.DefaultFilename
            else:
                filename=self._filename
        else:
            self._filename=paths.asURL(filename)
        if altEncoder is not None:
            if altEncoderParams is not None:
                data=altEncoder(**altEncoderParams)
            else:
                data=altEncoder()
        elif self._encode is None:
            raise Exception('Cannot save this kind of data')
        else:
            data=self._encode() # pylint: disable=not-callable
        if isinstance(data,str):
            encoding=self.encoding
            if encoding is None:
                encoding="utf-8"
            data=data.encode(encoding,errors="ignore")
        defaultSaver(filename,data)

    def __repr__(self)->str:
        return str(self._filename)
