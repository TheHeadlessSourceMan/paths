"""
has a .cgi member and acts like a dict

this is specific to the needs of URL object and
is not intended for public consumption.
"""
import typing
import urllib


class HasCgiDict(typing.Dict[str,typing.Any]):
    """
    has a .cgi member and acts like a dict

    this is specific to the needs of URL object and
    is not intended for public consumption.
    """

    def __init__(self):
        self.cgi:typing.Dict[str,typing.Any]={}

    def __len__(self)->int:
        """
        access like a dict
        """
        return len(self.cgi)

    def __iter__(self)->typing.Iterable[typing.Tuple[str,typing.Any]]:
        """
        access like a list

        NOTE: I like this behavior better than dict's iter
        """
        return self.cgi.items().__iter__()

    def __setitem__(self,k:str,v:typing.Any)->None:
        """
        access like a dict
        """
        self.cgi[k]=str(v)

    def update(self,otherDict:typing.MutableMapping[str,typing.Any])->None:
        """
        access like a dict
        """
        self.cgi.update(otherDict)

    def __delitem__(self,k:str)->None:
        """
        access like a dict
        """
        del self.cgi[k]

    def __getitem__(self,k:typing.Union[str,int])->typing.Any:
        """
        access like a dict
        """
        if isinstance(k,int):
            return list(self.cgi.values())[k]
        return self.cgi.get(k)

    def items(self)->typing.ItemsView[str,typing.Any]:
        """
        access like a dict
        """
        return self.cgi.items()

    def keys(self)->typing.KeysView[str]:
        """
        access like a dict
        """
        return self.cgi.keys()

    def values(self)->typing.ValuesView[typing.Any]:
        """
        access like a dict
        """
        return self.cgi.values()

    def get(self,key:str,default:typing.Any=None)->typing.Any:
        """
        access like a dict
        """
        return self.cgi.get(key,default)

    @property
    def query(self)->str:
        """
        the query as a string

        NOTE: the self.cgi[x] dict is safer, easier, and simpler
        """
        if not self.cgi:
            return ''
        return urllib.parse.urlencode(self.cgi)
    @query.setter
    def query(self,query:typing.Optional[str]):
        self.cgi={}
        if query is not None:
            queryDict=urllib.parse.parse_qs(query,keep_blank_values=True)
            for k,vv in queryDict.items():
                self.cgi[k]=vv[-1]