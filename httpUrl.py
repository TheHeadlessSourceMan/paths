"""
A URL that is specifically http or https

This allows for specialty additions such
as http methods and http header
"""
import typing
import datetime
from ._url import Url,URLCompatible


def asHttpUrl(url:URLCompatible)->"HttpUrl":
    """
    Create an HttpUrl from anything.
    If it is already one, simply return it
    """
    if isinstance(url,HttpUrl):
        return url
    return HttpUrl(url)


class NotHttpException(Exception):
    """
    Thrown when attempting to create an HttpUrl off
    of something that is not http or https
    """
    def __init__(self,url:typing.Optional[URLCompatible]):
        Exception.__init__(self,f'Unable to create HTTP url from: {url}')


class HttpRequest:
    """
    An http request in a bottle
    """
    def __init__(self,
        httpUrl:URLCompatible,
        method:str,
        content:typing.Optional[bytes],
        headers:typing.Optional[typing.Dict[str,typing.Any]]
        ):
        self.httpUrl=HttpUrl(httpUrl)
        self.method=method
        self.content=content
        self.headers=headers

    @property
    def url(self)->"HttpUrl":
        """
        The url of the request
        """
        return self.httpUrl

    def run(self)->"HttpResponse":
        """
        Perform the request now and wait for response.
        """
        import requests
        response=requests.get(str(self.httpUrl),timeout=5.0)
        return HttpResponse(
            response.status_code,
            response.content,
            self)
    __call__=run


class HttpResponse:
    """
    Response from an HttpRequest
    """

    def __init__(self,
        responseCode:int,
        content:bytes,
        originalRequest:typing.Optional[HttpRequest]=None,
        timestamp:typing.Optional[datetime.datetime]=None):
        """ """
        self.responseCode=responseCode
        self.content=content
        self.originalRequest=originalRequest
        if timestamp is None:
            timestamp=datetime.datetime.now()
        self.timestamp=timestamp

    @property
    def success(self)->bool:
        """
        Any responseCode in the 200 range is considered success
        """
        return self.responseCode>=200 and self.responseCode<300

    def retry(self)->"HttpResponse":
        """
        Retry the original request
        """
        if self.originalRequest is None:
            raise Exception('Original request unknown. Unable to retry.')
        return self.originalRequest()

    @property
    def contentStr(self)->str:
        """
        interpret content as a utf-8 string
        """
        return self.content.decode('utf-8',errors='ignore')

    def __str__(self)->str:
        return self.contentStr


class HttpUrl(Url):
    """
    A URL that is specifically http or https

    This allows for specialty additions such
    as http methods and http header
    """

    def __init__(self,
        url:typing.Optional[URLCompatible],
        relativeTo:typing.Optional[URLCompatible]=None,
        maxParentLevels:typing.Optional[int]=None,
        maxChildLevels:typing.Optional[int]=None,
        _useRelTo:bool=True):
        """ """
        Url.__init__(self,url,relativeTo,maxParentLevels,maxChildLevels,_useRelTo)
        if self.protocol not in ('http','https'):
            raise NotHttpException(self)

    def createHttpRequest(self,
        method:str,
        contents:typing.Optional[typing.Any],
        headers:typing.Optional[typing.Dict[str,typing.Any]]
        )->HttpRequest:
        """
        Create an http request but do not run it
        """
        return HttpRequest(self,method,contents,headers)

    def performHttpRequest(self,
        method:str,
        contents:typing.Optional[typing.Any],
        headers:typing.Optional[typing.Dict[str,typing.Any]]
        )->HttpResponse:
        """
        Perform an http request
        """
        request=self.createHttpRequest(method,contents,headers)
        return request()
    httpRequest=performHttpRequest

    def performHttpGet(self,
        contents:typing.Optional[typing.Any],
        headers:typing.Optional[typing.Dict[str,typing.Any]]):
        """
        Perform an http GET request
        """
        return self.performHttpRequest('GET',contents,headers)
    httpGet=performHttpGet

    def performHttpPut(self,
        contents:typing.Optional[typing.Any],
        headers:typing.Optional[typing.Dict[str,typing.Any]]):
        """
        Perform an http PUT request
        """
        return self.performHttpRequest('GET',contents,headers)
    httpGet=performHttpPut
