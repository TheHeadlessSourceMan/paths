"""
all http method verbs
"""
import typing
from enum import Enum


class HttpMethod(Enum):
    """
    all http method verbs
    """
    GET="GET" # used to get data
    POST="POST" # used to create data
    UPDATE="UPDATE" # used to modify data
    DELETE="DELETE" # used to delete data
    OPTIONS="OPTIONS" # used to ask what the interface supports


HttpMethodCompatible=typing.Union[str,HttpMethod]


def asHttpMethod(method:HttpMethodCompatible)->HttpMethod:
    """
    Always get as an http method
    """
    if isinstance(method,HttpMethod):
        return method
    return HttpMethod(str(method).upper())
