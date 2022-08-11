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

    def __init__(self):
        self._cleverUrlReplacements:typing.List[typing.Tuple[
            typing.Pattern,
            typing.Union[str,None],
            int
            ]]=[]
        self.addCleverUrlInterpreter('[a-zA-Z][-a-zA-Z0-9_]+:.*',None) # skip over regular urls
        self.addCleverUrlInterpreter(r'[.]?[\/].*',None) # skip over file paths
        self.addCleverUrlInterpreter(r'[a-zA-Z]{1,2}:.*',None) # skip over windows paths
        self.addCleverUrlInterpreter(
            r'([a-zA-Z][a-zA-Z0-9-_.]*@[a-zA-Z][a-zA-z0-9-_]*[.][a-zA-Z]{2-3})',
            'mailto:$1') # email addresses - experimental
        self.addCleverUrlInterpreter(
            r'([+]?[1-9])?\s*[-]?\s*[(]?\s*([0-9]{3})\s*[\)]?\s*([0-9]{3})[-]([0-9]{4})',
            'tel:$1$2$3$4') # phone numbers - experimental

    def addCleverUrlInterpreter(self,
        pattern:typing.Union[str,typing.Pattern],
        repl:typing.Optional[str],
        count:int=1,
        flags:int=0):
        """
        What you add is the same thing you would pass to re.sub()
        """
        if isinstance(pattern,str):
            pattern=re.compile(pattern,flags)
        self._cleverUrlReplacements.append((pattern,repl,count))

    def _getCleverURL(self,
        url:str
        )->str:
        """
        This is a hook used to get cleverly get things as urls,
        for instance
        "sam@abc.com"->"mailto:sam@abc.com"
        "(800)555-1234"->"tel:+18005551234"
        """
        for pattern,repl,count in self._cleverUrlReplacements:
            m=pattern.match(url)
            if m is not None:
                if repl is None:
                    return url
                return pattern.sub(repl,count)
        raise MalformedURL(str(url),'unable to coerce into a url')