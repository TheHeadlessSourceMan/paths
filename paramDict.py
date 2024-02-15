"""
has a .cgi member and acts like a dict

this is specific to the needs of URL object and
is not intended for public consumption.
"""
import typing
from collections.abc import Iterable
import urllib


PARAM_VAL_TYPE=typing.Union[str,typing.List[str]]
class ParamDict(typing.Dict[str,PARAM_VAL_TYPE]):
    """
    Manages cgi-like url parameters and acts like a dict
    """

    def __init__(self,
        otherDict:typing.Union[
            None,
            "ParamDict",
            typing.Iterable[typing.Tuple[str,PARAM_VAL_TYPE]]
            ]=None):
        """
        """
        self._params:typing.Dict[str,PARAM_VAL_TYPE]={}
        if otherDict is not None:
            self.assign(otherDict)

    def __len__(self)->int:
        """
        access like a dict
        """
        return len(self._params)

    def __iter__(self)->typing.Iterable[typing.Tuple[str,PARAM_VAL_TYPE]]:
        """
        access like a list

        NOTE: I like this behavior better than dict's iter
        """
        return self._params.items().__iter__()

    def set(self,k:str,v:typing.Any)->None:
        """
        Set a parameter's value
        """
        if isinstance(v,Iterable) and not isinstance(v,str):
            self._params[k]=[str(vv) for vv in v]
        else:
            self._params[k]=str(v)
    def __setitem__(self,k:str,v:typing.Any)->None:
        """
        access like a dict
        """
        self.set(k,v)
    def get(self,k:str,default:typing.Any=None)->typing.Any:
        return self._params.get(k,default)
    def __getitem__(self,k:str)->PARAM_VAL_TYPE:
        """
        access like a dict
        """
        if isinstance(k,int):
            return list(self._params.values())[k]
        return self._params[k]

    def copy(self)->'ParamDict':
        """
        duplicate this object
        """
        return ParamDict(self)

    def clear(self)->None:
        """
        access like a dict
        """
        self._params.clear()

    def update(self,otherDict:typing.Union[ # type: ignore
        "ParamDict",
        typing.Iterable[typing.Tuple[str,PARAM_VAL_TYPE]]]
        )->None:
        """
        access like a dict
        """
        if isinstance(otherDict,ParamDict):
            otherDict=otherDict.items()
        self._params.update(otherDict)

    def assign(self,otherDict:typing.Union[ # type: ignore
        None,
        "ParamDict",
        typing.Iterable[typing.Tuple[str,PARAM_VAL_TYPE]]]
        )->None:
        """
        Exactly the same thing as a clear() followed by an update()
        """
        self.clear()
        if otherDict is not None:
            self.update(otherDict)

    def __delitem__(self,k:str)->None:
        """
        access like a dict
        """
        del self._params[k]

    def items(self)->typing.ItemsView[str,PARAM_VAL_TYPE]: # type: ignore
        """
        access like a dict
        """
        return self._params.items()

    def keys(self)->typing.KeysView[str]: # type: ignore
        """
        access like a dict
        """
        return self._params.keys()

    def values(self)->typing.ValuesView[PARAM_VAL_TYPE]: # type: ignore
        """
        access like a dict
        """
        return self._params.values()

    @property
    def query(self)->str:
        """
        the query as a string

        NOTE: the self.cgi[x] dict is safer, easier, and simpler
        """
        if not self._params:
            return ''
        return urllib.parse.urlencode(self._params)
    @query.setter
    def query(self,query:typing.Optional[str]):
        self._params={}
        if query is not None:
            queryDict=urllib.parse.parse_qs(query,keep_blank_values=True)
            for k,vv in queryDict.items():
                self._params[k]=vv[-1]

    @property
    def queryString(self)->str:
        """
        possibly better than self.query
        """
        vals=[]
        for k,v in self._params.items():
            if isinstance(v,Iterable) and not isinstance(v,str):
                for vv in v:
                    s=f'{urllib.parse.quote(k)}={urllib.parse.quote(vv)}'
                    vals.append(s)
            else:
                vals.append(f'{urllib.parse.quote(k)}={urllib.parse.quote(v)}')
        if vals:
            return '?'+('&'.join(vals))
        return ''

    def __repr__(self)->str:
        return self.queryString
