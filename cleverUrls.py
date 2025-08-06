"""
support for clever urls, eg
    bob@gmail.com -> mailto:bob@gmail.com
    1-800-555-1234 -> tel:18005551234
    ...

this is specific to the needs of URL object and
is not intended for public consumption.
"""
import typing
import re
from .errors import MalformedURL


class CleverUrls:
    """
    support for clever urls, eg
        bob@gmail.com -> mailto:bob@gmail.com
        1-800-555-1234 -> tel:18005551234
        ...

    this is specific to the needs of URL object and
    is not intended for public consumption.
    """

    # do not access directly, but instead use
    # _getCleverUrlReplacements() and addCleverUrlInterpreter()
    _CLEVER_URL_REPLACEMENTS:typing.List[typing.Tuple[
        typing.Pattern[str],
        typing.Union[str,None],
        int
        ]]=[]

    @classmethod
    def _getCleverUrlReplacements(cls
        )->typing.List[typing.Tuple[
            typing.Pattern[str],
            typing.Union[str,None],
            int
            ]]:
        """ """
        if not cls._CLEVER_URL_REPLACEMENTS:
            cls.addCleverUrlInterpreter(
                '[a-zA-Z][-a-zA-Z0-9_]+:.*',None) # skip over regular urls
            cls.addCleverUrlInterpreter(
                r'[.]?[\/].*',None) # skip over file paths
            cls.addCleverUrlInterpreter(
                r'[a-zA-Z]{1,2}:.*',None) # skip over windows paths
            cls.addCleverUrlInterpreter(
                r'([a-zA-Z][a-zA-Z0-9-_.]*@[a-zA-Z][a-zA-z0-9-_]*[.][a-zA-Z]{2-3})', # noqa: E501 # pylint: disable=line-too-long
                'mailto:$1') # email addresses - experimental
            cls.addCleverUrlInterpreter(
                r'([+]?[1-9])?\s*[-]?\s*[(]?\s*([0-9]{3})\s*[\)]?\s*([0-9]{3})[-]([0-9]{4})', # noqa: E501 # pylint: disable=line-too-long
                'tel:$1$2$3$4') # phone numbers - experimental
        return cls._CLEVER_URL_REPLACEMENTS

    @classmethod
    def addCleverUrlInterpreter(cls,
        pattern:typing.Union[str,typing.Pattern],
        repl:typing.Optional[str],
        count:int=1,
        flags:int=0
        )->None:
        """
        What you add is the same thing you would pass to re.sub()
        """
        if isinstance(pattern,str):
            pattern=re.compile(pattern,flags)
        cls._CLEVER_URL_REPLACEMENTS.append((pattern,repl,count))

    @classmethod
    def _getCleverURL(cls,
        url:str
        )->str:
        """
        This is a hook used to get cleverly get things as urls,
        for instance
        "sam@abc.com"->"mailto:sam@abc.com"
        "(800)555-1234"->"tel:+18005551234"
        """
        for pattern,repl,count in cls._getCleverUrlReplacements():
            m=pattern.match(url)
            if m is not None:
                if repl is None:
                    return url
                return pattern.sub(str(m),repl,count)
        raise MalformedURL(str(url),'unable to coerce data into a url')
