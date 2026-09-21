"""
Format of a .url file
"""
import pathlib
import typing
import datetime
import configparser
try:
    import PIL.Image
    hasPIL=True
    ImageType=PIL.Image.Image
except ImportError:
    hasPIL=False
    ImageType=None
from .urlTyping import UrlCompatible,asUrl
from ._url import URL, Url


def windowsFiletimeToDatetime(filetime:bytes):
    """
    Convert a Windows FILETIME to a datetime object.

    Args:
        filetime (bytes): The FILETIME value as bytes.

    Returns:
        datetime.datetime: The corresponding datetime.
    """
    filetime=filetime[-8:]
    t=int.from_bytes(filetime,byteorder='little',signed=False)
    offset=datetime.timedelta(microseconds=t/10)
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
        self._filename:typing.Optional[URL]=None
        self._ini:typing.Optional[configparser.ConfigParser]=None
        self.load(filenameOrContents)

    def load(self,filenameOrContents:typing.Optional[UrlCompatible]=None):
        """
        If filenameOrContents is data, decode it.
        Otherwise, load it from file.
        """
        if filenameOrContents is None:
            if self._filename is not None:
                filenameOrContents=self._filename # type: ignore
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
            self._filename=URL(
                filenameOrContents) # type: ignore
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
                self._filename=typing.cast(URL,asUrl("untitled.url"))
        else:
            self._filename=typing.cast(URL,asUrl(filename))
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

    def getFileStr(self,
        name:str,
        sectionName:str="InternetShortcut"
        )->str:
        """
        Get a string value from the ini file.

        Args:
            name (str): The name of the value to retrieve.
            sectionName (str): The section in the ini file.
                Defaults to "InternetShortcut".

        Returns:
            str: The value as a string, or an empty string if not found.
        """
        if self._ini is None:
            return ""
        section:typing.Dict[str,str]=\
            self._ini.get(sectionName,{}) # type: ignore
        return section.get(name,"")

    @property
    def url(self)->Url:
        """
        The URL of the internet shortcut
        """
        return Url(self.getFileStr('URL'))

    @property
    def icon(self)->typing.Optional[ImageType]: # type: ignore
        """
        The icon for this url
        """
        if not hasPIL:
            return None
        if self._ini is None:
            return None
        filename=pathlib.Path(self.getFileStr('IconFile'))
        idx=self.getFileStr('IconIndex')
        img=PIL.Image.open(str(filename)) # type: ignore
        if idx and filename.suffix.lower() in ('.dll','.exe'):
            img=img.ico[int(idx)] # type: ignore
        return img # type: ignore

    @property
    def modifiedTime(self)->typing.Optional[datetime.datetime]:
        """
        The last time the webpage was modified
        """
        if self._ini is None:
            return None
        t=self.getFileStr('Modified',"InternetShortcut")
        if not t:
            return None
        return windowsFiletimeToDatetime(bytes.fromhex(t))

    def __repr__(self)->str:
        return str(self.url)
