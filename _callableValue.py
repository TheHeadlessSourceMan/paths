"""
A CallableValue acts like the value it wraps, but also allows you to
call it to get the original value back.

This is useful for cases where you want to wrap a callable object
(like a function or a class) and still be able to access the
original object when needed.

For instance, overriding a base class function that
you want to make more pythonic, by chaning it into a seamless
getter, eg "pathlib.Path.exists" instead of "pathlib.Path.exists()".
"""
import typing

_CallableType=typing.TypeVar('_CallableType')


class CallableValue(typing.Generic[_CallableType]):
    """
    A CallableValue acts like the value it wraps, but also allows you to
    call it to get the original value back.

    This is useful for cases where you want to wrap a callable object
    (like a function or a class) and still be able to access the
    original object when needed.
    
    For instance, overriding a base class function that
    you want to make more pythonic, by chaning it into a seamless
    getter, eg "pathlib.Path.exists" instead of "pathlib.Path.exists()".
    """
    def __init__(self,value:_CallableType):
        self._callable_value=value
        for k,v in value.__dict__.items():
            if hasattr(v,'__call__'):
                proxy=lambda *args,**kwargs: v(*args,**kwargs)
            else:
                proxy=v
            setattr(self,k,proxy)

    def __call__(self)->_CallableType:
        return self._callable_value
