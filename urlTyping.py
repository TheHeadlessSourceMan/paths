"""
typing shenanigans to make URL objects more easy and enjoyable
"""
import typing
import pathlib
if typing.TYPE_CHECKING:
    from paths import URL


class HasURL(typing.Protocol):
    """
    Duck typing for any object that has a .URL member
    """
    url:typing.Union['URLCompatible',typing.Callable[[],'URLCompatible']]
    #def getUrl(self) -> typing.Union["URL",str]:
    #   ...  # Empty method body (explicit '...')

class DictLike(typing.Protocol):
    """
    Duck typing for a dict-like object
    """
    def keys(self)->typing.Iterable[str]:
        """
        get keys
        """
        return []
    def __getitem__(self,idx:str)->typing.Any:
        ...

class IsFileWithName(typing.Protocol):
    """
    a file object with a .name member, pointing to an
    existing filename on the system
    """
    fileno:int
    name:str

URLCompatibleStrict=typing.Union["URL",HasURL,IsFileWithName,pathlib.Path]
URLCompatible=typing.Union[URLCompatibleStrict,str,bytes,DictLike]
UrlCompatibleStrict=URLCompatibleStrict
UrlCompatible=URLCompatible

def isUrlCompatible(obj:typing.Any,strict:bool=False)->bool:
    """
    Utility to check if something is considered compatible
    with a URL object.
    """
    if isinstance(obj,(str,bytes)):
        if not strict:
            return True
        if isinstance(obj,bytes):
            obj=obj.decode('utf-8',errors='ignore')
        if len(obj)>=2:
            if obj[1]==':':
                return True
            firstColon=obj.find(':')
            if firstColon>0:
                firstSlash=obj.find('/')
                if firstSlash>0 and firstColon<firstSlash:
                    proto=obj[:firstColon]
                    if ' ' not in proto:
                        return True
    import paths
    return isinstance(obj,paths.URL) \
        or hasattr(obj,'url') \
        or (hasattr(obj,"fileno") and hasattr(obj,"name"))
isURLCompatible=isUrlCompatible # alias name

@typing.overload
def asURL(url:None,
    relativeTo:typing.Optional[URLCompatible]='file://./',
    maxParentLevels:typing.Optional[int]=None,
    maxChildLevels:typing.Optional[int]=None
    )->None:
    ...
@typing.overload
def asURL(url:URLCompatible,
    relativeTo:typing.Optional[URLCompatible]='file://./',
    maxParentLevels:typing.Optional[int]=None,
    maxChildLevels:typing.Optional[int]=None
    )->"URL":
    ...
def asURL(url:typing.Optional[URLCompatible],
    relativeTo:typing.Optional[URLCompatible]='file://./',
    maxParentLevels:typing.Optional[int]=None,
    maxChildLevels:typing.Optional[int]=None
    )->typing.Optional["URL"]:
    r"""
    Gets the url always as a URL object or None if it is None or "".
    If url is a URL object, WILL NOT create a new one, otherwise, it will.
    If you would rather always have a new URL object, simply create
        an instance of URL(url)
        (because this supports passing a URL object as the initialization)

    Raises MalformedURL exception if it doesn't work.

    NOTE: This can be a good efficiency boost, but also can lead to mutability
        troubles when sharing the same URL.  For instance, if
        somebody else changes it!

        A good rule is: if you are assigning a url object member, use URL(x)
        not asURL(x) so you keep a copy to what you expect.

    See also:
        https://www.ietf.org/rfc/rfc3986.html

    TODO:
        what about re, for instance
        ^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?
        or something from https://regexpattern.com/

    :url: Can be:
        * another URL object
        * a properly-formatted URL string
        * any object with a (Url,url, or URL) data member
            or (filename,path) like it is referring to a file
            or even (href,src,location,rel) like in html-ish objects
        * a file object with a .name member
        * a system path+file where the path exists
    :relativeTo: the url parameter is relative to this.
        eg asUrl('about.htm','http://fooblatz.com') gives
            "http://fooblatz.com/about.htm"
        if relativeTo is a simple string ending in ":"
            it suffices as a default protocol
            eg asURL('bob@mailbox.com','mailto:')
        if NONE, relativeTo is treated as "file://[current directory]"
            eg asUrl("readme.txt") gives "file://./readme.txt"
    :maxParentLevels: the maximum number of parent levels to allow
        in a relative path - for security, recommend setting this to 0
    :maxChildLevels: the maximum number of child levels to allow
        in a relative path
    :return: A URL object of url
    :rtype: URL
    """
    if url is None:
        return None
    import paths
    if isinstance(url,paths.URL):
        return url
    return paths.URL(url,relativeTo,maxParentLevels,maxChildLevels)
asUrl=asURL # alias name


URLListCompatible=typing.Union[
    None,URLCompatible,typing.Iterable[URLCompatible]]
UrlListCompatible=URLListCompatible

def toURLList(urls:URLListCompatible
    )->typing.List["URL"]:
    """
    Create a list of URL's from one or more URLCompatible items

    :param urls: one or more URLCompatible items (if None, returns empty list)
    :type urls: typing.Union[None,URLCompatible,typing.Iterable[URLCompatible]]
    :return: the urls
    :rtype: typing.List[URL]
    """
    import paths
    if urls is None:
        return []
    if isURLCompatible(urls):
        return [paths.URL(typing.cast(URLCompatible,urls))]
    return [paths.URL(url)
        for url in typing.cast(typing.Iterable[URLCompatible],urls)]
toUrlList=toURLList
asURLList=toURLList
asUrlList=toURLList
