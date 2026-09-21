"""
tools for splitting a url and assigning to a URL object

Since this is arguably the most important part of URL objects
it made sense to give it its own module.
"""
import typing
import os
import urllib.parse
import paths


def urlAssign(
    self:paths.URL,
    url:typing.Optional[paths.URLCompatible],
    relativeTo:typing.Optional[paths.URLCompatible]='file:///./',
    maxParentLevels:typing.Optional[int]=None,
    maxChildLevels:typing.Optional[int]=None,
    _isDirectory:typing.Optional[bool]=None
    )->None:
    """
    Assign this url to something

    Raises MalformedURL exception if it doesn't work.

    NOTE: unlike many things like asURL(), relativeTo has no default
        (which means file://[current directory]).
        This is because in most cases you probably want to be
        relative to the current location
            eg myUrl.assign(url,myUrl)
        Removing the default was intended to force the caller
        to be specific in their intent.

    :param url: Can be:
        * another URL object
        * a properly-formatted URL string
        * any object with a (Url,url, or URL) data member
            or (filename,path) like it is referring to a file
            or even (href,src,location,rel) like in html-ish objects
        * a file object with a .name member
        * a system path+file where the path exists
        * the contents of a .url file
    :type url: URLCompatible
    :param relativeTo: the url parameter is relative to this.
        eg asUrl('about.htm','http://fooblatz.com')
            gives "http://fooblatz.com/about.htm"
        if relativeTo is a simple string ending in ":"
            it suffices as a default protocol
            eg asURL('bob@mailbox.com','mailto:')
        if NONE, relativeTo is treated as "file:///[current directory]"
            eg asUrl("readme.txt") gives "file:///./readme.txt"
    :type relativeTo: URLCompatible
    :maxParentLevels: the maximum number of parent levels to allow
        in a relative path - for security, recommend setting this to 0
    :maxChildLevels: the maximum number of child levels to allow
        in a relative path
    """
    self.clear()
    self._isDirectory=_isDirectory # type: ignore # noqa: E501 # pylint: disable=protected-access
    if url is None:
        return
    if isinstance(url,paths.URL):
        self.scheme=url.scheme
        self.username=url.username
        self.password=url.password
        self.host=url.host
        self.port=url.port
        self.path=url.path
        self.isUNC=url.isUNC
        self.resource=url.resource
        self._fragment=url.fragment # pylint: disable=protected-access
        self.fragments=url.fragments.copy()
        self.cgi=url.cgi.copy()
        return
    # make it ALWAYS a simple url string for processing
    url=self._getUrlString(url) # pylint: disable=protected-access
    if url is None:
        return # it was already cleared above
    # check for possibly malformed file://
    #    technically file://foo/bar means foo=host, though most people assume
    #    foo is directory the "correct" way of foo as a directory
    #    is file:///foo/bar
    #    this section  guesses what they really meant and correct as necessary
    #    the algorithm used to determine to treat foo is a local file:
    #        * if self.filesUrlPreferLocal is True
    #        * if there is no more to the path assume they meant
    #          file://file not file://host
    #        * if first dir ends with a :, assume they meant
    #          file://c: not host named c
    #    result of this stage is url is modified with triple slash if necessary
    if url.startswith('file://') and not url.startswith('file:///'):
        if os.sep!='/':
            url=url.replace(os.sep,'/')
        parts=url.split('/',4)
        if self.filesUrlPreferLocal or len(parts)<3 or parts[2].endswith(':'):
            parts.insert(1,'')
            url='/'.join(parts)
    # check for UNC paths
    if url.startswith('\\\\'):
        # the format is different than url, so it makes
        # more sense to do this manually
        self.isUNC=True
        s=url.split('\\')
        self.scheme='file'
        self.host=s[2]
        if len(s)>2:
            if len(s)>3:
                self.path='/'.join(s[3:-1])
            self.filename=s[-1]
        return
    if url.startswith('file://///'):
        # the format is different than url, so it makes
        # more sense to do this manually
        self.isUNC=True
        s=url.split('/')[3:]
        self.host=s[2]
        self.scheme='file'
        if len(s)>2:
            if len(s)>3:
                self.path='/'.join(s[3:-1])
            self.filename=s[-1]
        return
    # check for dos/windows absolute paths
    isWindowsAbsolutePath=False
    if len(url)<2 or url[1]==':':
        # windows-like filename (eg c:\something)
        isWindowsAbsolutePath=True
        url='file:///'+url.replace('\\','/')
    elif os.sep!='/':
        url=url.replace(os.sep,'/')
    # url is always using '/' as the separator from here on out
    #isAbsolutePath=url[0]=='/' or isWindowsAbsolutePath
    # check for things that should be transformed to fragments, specifically,
    # file.txt:10-11 should be handled by RFC-5147
    # https://datatracker.ietf.org/doc/html/rfc5147
    resourceAndFrag=url.rsplit('/',1)[-1].split(':',1)
    if len(resourceAndFrag)>1:
        fileFrag=resourceAndFrag[-1]\
            .replace(',',' ')\
            .replace(':',' ')\
            .replace(';',' ')\
            .split()
        urlFrag=[]
        if len(fileFrag)>0:
            urlFrag.append(f"line={fileFrag[0].replace('-',',')}")
            if len(fileFrag)>1:
                urlFrag.append(f"char={fileFrag[1].replace('-',',')}")
        frag=';'.join(urlFrag)
        url=f"{url.rsplit('/',1)[0]}/{resourceAndFrag[0]}#{frag}"
    # let the standard parser have a go at it
    parsed=urllib.parse.urlparse(url)
    ret=paths.URL(None)
    ret.scheme=parsed.scheme
    ret.username=parsed.username
    ret.password=parsed.password
    ret.host=parsed.hostname
    if ret.host is None or ret.host=='':
        ret.host='localhost'
    ret.port=parsed.port
    path=parsed.path
    if isWindowsAbsolutePath:
        path.replace('%3A',self.windowsDriveSeparator,1) # url decode where they encoded the ':' # noqa: E501 # pylint: disable=line-too-long
        ret.scheme='file'
    if path.startswith('/'):
        path=path[1:]
    ret.fullPath=path
    ret._fragment=parsed.fragment # pylint: disable=protected-access
    ret.fragments=dict(urllib.parse.parse_qsl(
        parsed.fragment.replace(';','&'),keep_blank_values=True))
    ret.cgi.clear()
    ret.cgi.query=parsed.query
    if not ret.protocol and relativeTo is not None:
        from .urlTyping import asUrl
        relativeTo=asUrl(relativeTo,None)
        r2=relativeTo.getRelativeUrl(ret,maxParentLevels,maxChildLevels)
        if r2 is None:
            raise paths.MalformedURL(url,'relative url broke')
        else:
            ret=r2
    if ret.host is None and ret.protocol!='file':
        raise paths.MalformedURL(url,'missing host')
    if ret.protocol!='file' and ret.path is not None:
        # remove any leading / from path
        if path.startswith('/'):
            path=path[1:]
    self.assign(ret,None)
