"""
Format of a .url file
"""
import typing
import datetime
import configparser
import PIL
from .urlTyping import UrlCompatible,asUrl
from ._url import Url


def windowsFiletimeToDatetime(filetime:bytes):
    """
    Convert a Windows FILETIME to a datetime object.

    Args:
        filetime (bytes): The FILETIME value as bytes.

    Returns:
        datetime.datetime: The corresponding datetime.
    """
    filetime=filetime[-8:]
    filetime=int.from_bytes(filetime,byteorder='little',signed=False)
    offset=datetime.timedelta(microseconds=filetime/10)
    return datetime.datetime(1601,1,1)+offset


def isUrlFileData(data:str)->bool:
    """
    Check if the given data is in the format of a .url file.

    Args:
        data (str): The data to check.

    Returns:
        bool: True if the data is in .url file format, False otherwise.
    """
    data=data.strip()
    return data.lower().find("[internetshortcut]")>=0


class UrlFileFormat:
    """
    Format of a .url file

    See also:
    https://www.cyanwerks.com/formats/file-format-url.html
    """
    def __init__(self,filenameOrContents:UrlCompatible):
        self._filename:typing.Optional[Url]=None
        self._ini:typing.Optional[configparser.ConfigParser]=None
        self.load(filenameOrContents)

    def load(self,filenameOrContents:typing.Optional[UrlCompatible]=None):
        """
        If filenameOrContents is data, decode it.
        Otherwise, load it from file.
        """
        if filenameOrContents is None:
            if self._filename is not None:
                filenameOrContents=self._filename
            else:
                raise Exception("No filename to load")
        contents=None
        if isinstance(filenameOrContents,bytes):
            filenameOrContents=filenameOrContents.decode(
                "utf-8",errors="ignore")
        if isinstance(filenameOrContents,str):
            filenameOrContents=filenameOrContents.strip()
            if filenameOrContents.find('\n') \
                and filenameOrContents.lower().find("[internetshortcut]")>=0:
                contents=filenameOrContents
        if contents is None:
            self._filename=Url(filenameOrContents)
            contents=self._filename.read()
        self.decode(contents)
    assign=load

    def decode(self,contents:str):
        """
        Decode the URL file contents from a string.

        Args:
            contents (str): The contents of the URL file as a string.
        """
        self._ini=configparser.ConfigParser()
        self._ini.read_string(contents)

    def save(self,filename:typing.Optional[UrlCompatible]=None):
        """
        save the url file
        """
        if filename is None:
            if self._filename is None:
                self._filename=asUrl("untitled.url")
        else:
            self._filename=asUrl(filename)
        self._filename.write(self.encode())

    def encode(self)->str:
        """
        Encode the URL file contents as a string.
        """
        if self._ini is None:
            return "[InternetShortcut]\n"
        from io import StringIO
        data=StringIO()
        self._ini.write(data)
        return data.getvalue()

    @property
    def url(self)->Url:
        """
        The URL of the internet shortcut
        """
        if self._ini is None:
            s=""
        else:
            s=self._ini.get('InternetShortcut',{}).get('URL',"")
        return Url(s)

    @property
    def icon(self)->typing.Optional[PIL.Image.Image]:
        """
        The icon for this url
        """
        if self._ini is None:
            return None
        filename=self._ini.get('InternetShortcut',{}).get('IconFile',"")
        idx=self._ini.get('InternetShortcut',{}).get('IconIndex',"")
        img=PIL.Image.open(filename)
        if idx and filename.suffix.lower() in ('.dll','.exe'):
            img=img.ico[int(idx)]
        return img

    @property
    def modifiedTime(self)->typing.Optional[datetime.datetime]:
        """
        The last time the webpage was modified
        """
        if self._ini is None:
            return None
        t=self._ini.get('InternetShortcut',{}).get('Modified',"")
        if not t:
            return None
        return windowsFiletimeToDatetime(bytes.fromhex(t))

    def __repr__(self)->str:
        return str(self.url)
