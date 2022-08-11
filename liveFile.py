import typing
from paths import URLCompatible,URL


class LiveFilePool:
    """
    Global object shared between LiveFile objects
    to support communal buffering
    """
    def __init__(self):
        self.data={}
        self.lastCheckTime={}

    def getData(self,filename:URLCompatible):
        filename=URL(filename)
        data=self.data.get(filename)
        if data is None:
            with open(data,'r') as f:
                data=f.read()
                self.data[filename]=data
            

class LiveFile:
    """
    a file with advanced, but easily configurable,
    caching/watching/polling
    """
    
    POOL=LiveFilePool()
    
    def __init__(self,filename:URLCompatible):
        self.filename=URL(filename)
        self.watchChanges=True # only works on certain filesystems
        self.pollingInterval=90 # only used if polling is needed
        self.garbageCollectAfter=1200 # free up memory after this long of inactivity
        self.preload=False # load the data immediateley rather than waiting until it is needed
        self.callOnChange:typing.List[typing.Callable]=[] # whenever external data change is detected, call these functions
        
    @property
    def data(self):
        return self.POOL.getData(self.filename)