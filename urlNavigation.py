"""
navigate around a url, like with
    root,parent,children,siblings,...

this is specific to the needs of URL object and
is not intended for public consumption.
"""
import typing
from abc import abstractmethod
from paths.urlTyping import URLCompatible
if typing.TYPE_CHECKING:
    from paths import URL


class UrlNavigation:
    """
    navigate around a url, like with
        root,parent,children,siblings,...

    this is specific to the needs of URL object and
    is not intended for public consumption.
    """
    if typing.TYPE_CHECKING:
        from paths import URL

    def __init__(self):
        pass

    @property
    @abstractmethod
    def isDirectory(self)->bool:
        """
        Is the current location a directory
        """

    @property
    @abstractmethod
    def url(self)->str:
        """
        The current url as a string
        """

    @property
    def parent(self)->"URL":
        """
        parent directory
        """
        return self.relative('..')

    @property
    def root(self)->"URL":
        """
        domain root directory
        """
        return self.relative('/')

    def subdir(self,
        url:typing.Optional[URLCompatible]
        )->"URL":
        r"""
        creates a new url based on this url+subdir eg
            given
            "http://zod@kneelbefore.com/path/things?q=hello".subdir("thing11")
            gives
            "http://zod@kneelbefore.com/path/things/thing11"

        NOTE: this is different that getSibling() because
            "c:\this\that".getChild("x.htm") => "c:\this\that\x.htm"
            but
            "c:\this\that".getSibling("x.htm") => "c:\this\x.htm"

        NOTE: if subPath is a full url (eg 'http://whatever')
            then there is no resolving. It will simply return it.
        """
        import paths
        if url is None:
            return self # type: ignore
        if isinstance(url,paths.URL):
            # assume it is fully qualified, whatever it is
            return url
        if not isinstance(url,str):
            url=str(url)
        if not self.isDirectory:
            raise NotADirectoryError(str(self))
        ret=paths.URL(self) # type: ignore
        ret.path=f'{ret.path}/{ret.resource}'
        ret.resource=url
        ret.cgi.clear()
        ret.fragment=None
        return ret
    getSubUrl=subdir
    subDir=subdir
    child=subdir
    getChild=subdir

    def getRelativeUrl(self,
        url:typing.Optional[URLCompatible]
        )->"URL":
        """
        Turns a relative url (eg href="./about") to its full form.

        Example:
            u=Url("http://something.com/foo/bar/app?q=1")
            u.relative('images/img1.jpeg')
            # "http://something.com/foo/bar/images/img1.jpeg"
            u.relative('/images/img1.jpeg')
            # "http://something.com/images/img1.jpeg"
            u.relative('../images/img1.jpeg')
            # "http://something.com/foo/images/img1.jpeg"
            u.relative('../../../images/img1.jpeg')
            # big fat exception

        TODO: open up a browser and verify this gives the same answer
            (getRelativeUrl may need to be a switching mechanism
            between getSibling and getChild)
        """
        return self.getSibling(url)
    unRelativeUrl=getRelativeUrl
    relative=getRelativeUrl

    def location(self)->str:
        """
        Gets the working location of the url
        (useful for deciphering relative urls)

        Always contains trailing '/' for convenience
        """
        url=self.url.split('?',1)[0] # no cgi
        components=url.split('://',1)
        components[-1]=components[-1].split('/')
        # trim off the file
        if not components[-1]:
            components[-1].append('')
        else:
            components[-1][-1]=''
        # put it back together
        components[-1]='/'.join(components[-1])
        return '://'.join(components)

    def getSibling(self,
        url:typing.Optional[URLCompatible]
        )->"URL":
        r"""
        Gets a sibling location in reference to this one

        NOTE: this is different thatn getChild because
            "c:\this\that".getChild("x.htm") => "c:\this\that\x.htm"
            but
            "c:\this\that".getSibling("x.htm") => "c:\this\x.htm"

        NOTE: if subPath is a full url (eg 'http://whatever')
            then there is no resolving. It will simply return it.
        """
        import paths
        if url is None:
            return self
        if isinstance(url,URL):
            # assume it is fully qualified, whatever it is
            return url
        if not isinstance(url,str):
            url=str(url)
        urlStr=str(url)
        currentLocation=self.location()
        if currentLocation=='':
            return paths.asURL(urlStr)

        while currentLocation[-1]=='/':
            currentLocation=currentLocation[0:-1]
        protoPos=urlStr.find('://')
        if (protoPos>0 and protoPos<6):# or getDomain(currentLocation)==getDomain(urlStr): # noqa: E501 # pylint: disable=line-too-long
            return paths.asURL(urlStr)
        currentParts=currentLocation.split('/')
        lastEmpty=False
        for step in urlStr.split('/'):
            if step in ('','.'):
                lastEmpty=True
            elif step=='..':
                lastEmpty=False
                # check if we are navigating past root
                # or if windows file, we are trying to navigate past c:/
                if len(currentParts)<5:
                    if len(currentParts)<4 or currentParts[3].endswith(':'):
                        raise paths.MalformedURL(urlStr,
                            'Attempt to navigate past root in "%s"'%
                            currentLocation)
                # go up a level
                currentParts.pop()
            else:
                lastEmpty=False
                currentParts.append(step)
        if lastEmpty: # special case where we end in a /
            currentParts.append('')
        urlStr='/'.join(currentParts)
        return paths.asURL(urlStr)
    sibling=getSibling
    getSiblingUrl=getSibling
    peer=getSibling
