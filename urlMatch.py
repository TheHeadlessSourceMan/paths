"""
Tools to match urls against lists of urls and/or regex patterns
"""
import typing
import os
import re
from paths._url import Url
from paths.urlTyping import URLCompatible,asURL


UrlMatchable=typing.Union[
    None,URLCompatible,typing.Pattern[str],
    typing.Iterable[typing.Union[URLCompatible,typing.Pattern[str]]]]
MatchFilter=typing.Iterable[typing.Union[str,typing.Pattern[str]]]


def _createMatchFilter(matches:UrlMatchable,ignoreCase:bool)->MatchFilter:
    """
    Convert to a simple list of exact strings and regex patterns
    """
    if isinstance(matches,str) or not hasattr(matches,'__iter__'):
        matches=typing.cast(
            typing.Iterable[typing.Union[URLCompatible,typing.Pattern[str]]],
            [matches])
    results:MatchFilter=[]
    for m in typing.cast(
        typing.Iterable[typing.Union[URLCompatible,typing.Pattern[str]]],
        matches):
        #
        if not isinstance(m,re.Pattern):
            m=str(asURL(m))
            if ignoreCase:
                m=m.lower()
        results.append(m)
    return results


def urlMatches(
    url:URLCompatible,
    matches:UrlMatchable,
    ignoreCase:typing.Optional[bool]=None
    )->bool:
    """
    Check if a url matches one or more url's and/or patterns

    :url: url to match
    :matches: url(s) and/or regex pattern(s) to match
        if None, always returns False
    :ignoreCase: do not be case sensitive None (default) means
        best-guess based upon the url protocol and
        (this only applies to other url's as it is assumed
        if you have a regex you compiled it the way you want)

    returns True if it matches any of the matches

    NOTE: if you do this on more than one url with
    the same set of matches, it may be more efficient
    to call allUrlMatches()
    """
    if not matches:
        return False
    url=asURL(url)
    if ignoreCase is None:
        ignoreCase=url.protocol=='file' and os.name=='nt'
    if ignoreCase:
        url=str(url).lower()
    else:
        url=str(url)
    matches=_createMatchFilter(matches,ignoreCase)
    for m in matches:
        if isinstance(m,re.Pattern):
            if m.match(url) is not None:
                return True
        else:
            if m==url:
                return True
    return False
fileMatches=urlMatches


def allUrlMatches(
    urls:typing.Iterable[URLCompatible],
    matches:UrlMatchable,
    ignoreCase:typing.Optional[bool]=None
    )->typing.Iterable[Url]:
    """
    Check if a url matches one or more url's and/or patterns

    :url: url to match
    :matches: url(s) and/or regex pattern(s) to match
        if None, always returns False
    :ignoreCase: do not be case sensitive None (default) means
        best-guess based upon the url protocol and
        (this only applies to other url's as it is assumed
        if you have a regex you compiled it the way you want)

    returns True if it matches any of the matches
    """
    if not matches:
        return
    first=True
    for url in urls:
        url=asURL(url)
        if first:
            if ignoreCase is None:
                ignoreCase=url.protocol=='file' and os.name=='nt'
            matches=_createMatchFilter(matches,ignoreCase)
            first=False
        if ignoreCase:
            urlStr=str(url).lower()
        else:
            urlStr=str(url)
        for m in typing.cast(MatchFilter,matches):
            if isinstance(m,re.Pattern):
                if m.match(urlStr) is not None:
                    yield url
            else:
                if m==urlStr:
                    yield url
allFileMatches=allUrlMatches
