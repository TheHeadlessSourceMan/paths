"""
a file with advanced, but easily configurable,
caching/watching/polling
"""
import typing
import datetime
from paths import URLCompatible,URL


class CacheEntry:
    """
    A single entry in a data cache
    """
    def __init__(self,url:URL,data:str,cacheTime:datetime.datetime):
        self.url=url
        self.data=data
        self.cacheTime=cacheTime

    def __hash__(self) -> int:
        return self.url.__hash__()

class LiveFilePool:
    """
    Global object shared between LiveFile objects
    to support communal buffering
    """
    def __init__(self)->None:
        self.data:typing.Dict[URL,CacheEntry]={}

    def getCacheEntry(self,url:URLCompatible)->CacheEntry:
        """
        Get the entry in the cache
        """
        url=URL(url)
        data=self.data.get(url)
        if data is None:
            data=CacheEntry(url,url.read(),datetime.datetime.now())
            self.data[url]=data
        return data

    def getData(self,url:URLCompatible)->str:
        """
        Get the file data
        """
        return self.getCacheEntry(url).data

    def __getitem__(self,idx:URLCompatible)->str:
        """
        Access this like a dict, eg
        html=liveFilePool["http://www.toshistation.com"]
        """
        return self.getData(idx)


class LiveFile:
    """
    a file with advanced, but easily configurable,
    caching/watching/polling
    """

    POOL=LiveFilePool()

    LiveFileCallback=typing.Callable[["LiveFile"],None]

    def __init__(self,url:URLCompatible):
        self.url=URL(url)
        self.watchChanges=True # only works on certain filesystems
        self.pollingInterval=90 # only used if polling is needed
        self.garbageCollectAfter=1200 # free up memory after this long of inactivity # noqa: E501 # pylint: disable=line-too-long
        self.preload=False # load the data immediately rather than waiting until it is needed # noqa: E501 # pylint: disable=line-too-long
        self.callOnChange:typing.List[LiveFileCallback]=[] # whenever external data change is detected, call these functions # noqa: E501 # pylint: disable=line-too-long

    @property
    def data(self)->str:
        """
        Get the file data
        """
        return self.POOL.getData(self.url)
