import typing

#class BytesDecoder(typing.Protocol):
#    def __call__(self,data:bytes)->None: ...

BytesDecoder=typing.Callable[[bytes],None]

class BaseClass:

    def _decodeBytes(self,data:bytes)->None: ...
    _decodeBytes=None # type: ignore

    def canDecode(self):
        return self._decodeBytes is not None

    def decode(self,data:bytes):
        if self._decodeBytes is not None:
            self._decodeBytes(data)

class DerivedClass(BaseClass):

    def _decodeBytes(self,data:bytes,x:int=1)->None:
        print("derived")


bc=BaseClass()
dc=DerivedClass()
print(bc.canDecode())
print(dc.canDecode())