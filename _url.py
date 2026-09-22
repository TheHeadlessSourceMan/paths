#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
This represents a url type
"""
import typing
import os
import urllib.parse
import pathlib
from paths._uri import URI
from paths.urlTyping import URLCompatible,asURL
from paths.loadAndSave import LoadAndSave
from paths.urlNavigation import UrlNavigation
from paths.dataReadWrite import DataReadWrite
from paths.paramDict import ParamDict
from paths.cleverUrls import CleverUrls
from paths.filePathTools import encodeFilePath,illegalCharsForOs
from paths.errors import MalformedURL,NonIterableDirectory,UnknownBaseDirectory
from paths.pathLike import PathLike
if typing.TYPE_CHECKING:
    from paths.urlMatch import UrlMatchable


class URL(
    URI,
    PathLike,
    DataReadWrite,
    UrlNavigation,
    CleverUrls,
    LoadAndSave
    ):
    r"""
    Any URL of the form:
    ```
    <protocol>://<user>:<pass>@<host>:<port>/<path>/<resource>[?<option=value>&<option=value..>]
    ```

    ## Features:
    * All members of this object are properly decoded automatically.

    * This includes local file paths, which are interpereted as `file://` urls

        see: https://en.wikipedia.org/wiki/File_URI_scheme
    * does handle Windows paths `c:\dir\file`
    * does handle Windows UNC paths `\\machine\dir\file`
    * does handle technically malformed paths
            (`file://filename` should actually be `file:///filename`)
    * This is directly compatible with urllib3
    and backwards-compatible to urllib.

    ## You can do things like:
    ```python
    u=Url('http://www.mysite.com/path/search?q=something&page=1')
    u['page']=2
    print(u)
    # prints "http://www.mysite.com/path/search?q=something&page=2"

    u['q']='this&that'
    print(u)
    # prints "http://www.mysite.com/path/search?q=this%26that&page=2"

    u=Url('http://www.mysite.com/path/search?q=this%26that&page=2')
    print(u['q'])
    # prints "this&that"
    # (meaning the url encode/decode is fully automatic!)

    u2=u.relative('/images/1.jpg')
    print(u2)
    # prints "http://www.mysite.com/path/images/1.jpg"
    ```

    ## Notes:
        NOTE: specifying password in the url is generally considered bad form

        NOTE: has EXPERIMENTAL file-like object access

        TODO: IPv6 hosts

        TODO: look into parsing by hand instead of present urllib workarounds

            https://www.ietf.org/rfc/rfc3986.html#section-3.1

            https://en.wikipedia.org/wiki/File_URI_scheme

        TODO: pull in default readers from imageTools
    """

    # object members that could likely contain a url. order is important
    URL_LIKE_MEMBERS=('url','URL','Url','filename',
        'path','href','src','location','rel')

    # to associate a Url-derived class with a particular protocol,
    # simply add it to this dict {protocolStr:UrlDerivedClass}
    URL_PROTOCOL_OBJECT_TYPES:typing.Dict[str,typing.Type["Url"]]={}

    DefaultFilename:str='Untitled.url'

    def __new__(cls,
        url:typing.Optional[URLCompatible],
        *args:typing.ParamSpecArgs,**kwargs:typing.ParamSpecKwargs):
        """
        Intercepting this allows us the stupid pet trick
        of creating derived types from one constructor,
        for example, you would think:
            type(Url('http://google.com'))
        would be "Url", but it is actually "HttpUrl"
        Or type(Url('file://d:/cheese')) a File
        """
        _=args
        _=kwargs
        actualClass=cls.determineUrlSubclass(url)
        return super().__new__(actualClass) # type: ignore

    @classmethod
    def determineUrlSubclass(cls,
        url:typing.Optional[URLCompatible]=""
        )->typing.Type["URL"]:
        """
        Determine which URL subclass should be used for a particular url.

        It will do this by looking up in URL.URL_PROTOCOL_OBJECT_TYPES[],
        so if you want to add a new one, add it there.

        This can raise TypeError if there is no matching URL type registered.
        """
        protocol:typing.Optional[str]=None
        if isinstance(url,Url):
            protocol=url.protocol
        else:
            px=cls._getUrlString(url)
            if px is None:
                px=''
            protoPath=px.split(':',1)
            if len(protoPath)>1 \
                and len(protoPath[0])>1 \
                and protoPath[0].find('/')<1:
                #
                protocol=protoPath[0]
            else:
                protocol='file'
        actualClass:typing.Optional[typing.Type[URL]]=\
            cls.URL_PROTOCOL_OBJECT_TYPES.get(protocol,URL)
        if actualClass is None or not issubclass(actualClass,URL): # type: ignore # noqa: E501
            raise TypeError(f'Unable to determine type of URL for "{url}"')
        return actualClass

    def __init__(self, # type: ignore
        url:typing.Optional[URLCompatible]="",
        relativeTo:typing.Optional[URLCompatible]=None,
        maxParentLevels:typing.Optional[int]=None,
        maxChildLevels:typing.Optional[int]=None):
        """
        Raises MalformedURL exception if url assignment doesn't work.

        :param url: Can be:
            * another URL object
            * a properly-formatted URL string
            * any object with a (Url,url, or URL) data member
                or (filename,path) like it is referring to a file
                or even (href,src,location,rel) like in html-ish objects
            * a file object with a .name member
            * a system path+file where the path exists
        :type url: URLCompatible
        :param relativeTo: the url parameter is relative to this.
            eg asUrl('about.htm','http://fooblatz.com')
            gives "http://fooblatz.com/about.htm"
            if relativeTo is a simple string ending in ":"
            it suffices as a default protocol
                eg asURL('bob@mailbox.com','mailto:')
            if NONE, relativeTo is treated as "file://[current directory]"
                eg asUrl("readme.txt") gives "file://./readme.txt"
        :type relativeTo: str, optional
        :maxParentLevels: the maximum number of parent levels to allow
            in a relative path - for security, recommend setting this to 0
        :maxChildLevels: the maximum number of child levels to allow
            in a relative path
        """
        LoadAndSave.__init__(self)
        DataReadWrite.__init__(self)
        UrlNavigation.__init__(self)
        CleverUrls.__init__(self)
        PathLike.__init__(self,None)
        self.cgi:ParamDict=ParamDict()
        self.windowsDriveSeparator:str=':' # drive indicator in urls, file://c:/ vs file://c|/ # noqa: E501 # pylint: disable=line-too-long
        self.scheme:str=''
        self.username:typing.Optional[str]=None
        self.password:typing.Optional[str]=None
        self.domain:str=''
        self.subdomain:typing.Optional[str]=None
        self.port:typing.Optional[int]=None
        self._path:typing.Optional[str]=None
        self._fragment:typing.Optional[str]=None
        self.fragments:typing.Dict[str,str]={}
        self.isUNC:bool=False
        self.cache:bool=True
        self.persist:bool=True
        self.ignoreAlreadyEncoded=True # do not attempt to re-encode % signs (eg no http://x.com/space%20bar => http://x.com/space%2520bar) # noqa: E501 # pylint: disable=line-too-long
        self.filesUrlPreferLocal:bool=True # given file://foo/bar assume foo is local # noqa: E501 # pylint: disable=line-too-long
        # as opposed to a host named foo
        # basically False is more standards-compliant,
        # but True is more used in practice
        self._isDirectory:typing.Optional[bool]=None
        if url is not None and (not isinstance(url,str) or url):
            self.assign(
                url,relativeTo,maxParentLevels,maxChildLevels)

    def __getitem__(self, # type: ignore
        idx:typing.Union[str,int,slice]):
        """
        Access query parameters by name or path steps by position.
        """
        if isinstance(idx,str):
            return self.cgi.get(idx)
        return PathLike.__getitem__(self,idx)

    def __setitem__(self,idx:typing.Any,value:typing.Any)->None:
        """
        Set a query parameter by name."""
        if not isinstance(idx,str):
            raise TypeError("URL indexes must be query parameter names")
        self.cgi[idx]=value

    def __delitem__(self,idx:typing.Any)->None:
        """
        Delete a query parameter by name.
        """
        if not isinstance(idx,str):
            raise TypeError("URL indexes must be query parameter names")
        del self.cgi[idx]

    def _encode(self)->bytes:
        """
        Return the encoded URL as bytes.
        """
        return f'[InternetShortcut]\nURL={self}\n'.encode('utf-8')

    def _decode(self,data:bytes)->None:
        """
        Decode the given URL bytes.

        :data: the URL bytes to decode
        """
        self.assign(data.decode('utf-8',errors='ignore'))

    def absolute(self)->"Url":
        """
        This as an absolute url
        """
        if self.isAbsolute:
            return self
        raise UnknownBaseDirectory(self) # type: ignore

    def iterdir(self)->typing.Generator["URL",None,None]:
        """
        iterate over the current directory
        """
        raise NonIterableDirectory(self) # type: ignore
    @property
    def children(self)->typing.Generator["URL",None,None]:
        """
        iterate over the current directory
        """
        return self.iterdir()

    @property
    def files(self)->typing.Iterator["URL"]:
        """
        All of the child files
        """
        for c in self.children:
            if not c.isDirectory:
                yield c

    @property
    def directories(self)->typing.Iterator["URL"]:
        """
        All of the child directories
        """
        for c in self.children:
            if c.isDir:
                yield c

    def findFilenamesOfType(
        self,
        extensions:typing.Union[None,str,typing.Iterable[str]]=None,
        recursive:bool=True
        )->typing.Generator["URL",None,None]:
        """
        Depth-first file search.

        Yields only files, never directories.

        :extensions: limit results to one or more extensions
            (extensions must include the dot, for instance [".c",".cpp"])
        :recursive: default=true
        """
        _=extensions,recursive
        raise NonIterableDirectory(self) # type: ignore

    def dir(
        self,
        globExpression:typing.Union[None,str,typing.Pattern[str]]=None,
        recursive:bool=True
        )->typing.Generator["URL",None,None]:
        """
        Act like the system dir or ls command
        """
        if globExpression is not None and isinstance(globExpression,str):
            from .search import globToRegex
            globExpression=globToRegex(globExpression)
        for result in self.findFilenamesOfType(recursive=recursive):
            if globExpression is not None:
                if not result.isAbsolute:
                    resultStr=str(result.absolute())
                else:
                    resultStr=str(result)
                if globExpression.match(resultStr) is not None:
                    yield result
            else:
                yield result
    ls=dir

    @classmethod
    def _from_parts(cls,*args:typing.ParamSpecArgs):
        """
        This is necessary to get __new__() working due to pathlib.Path
        """
        _=args

    class _flavour:
        """
        This is necessary to get __new__() working due to pathlib.Path
        """
        is_supported=True

    @property
    def fragment(self)->str:
        """
        get/set the fragment portion of the url
        """
        if self._fragment is None:
            return ''
        return self._fragment
    @fragment.setter
    def fragment(self,fragment:str):
        print("TODO: setting of fragment is experimental")
        self._fragment=fragment
        kv=fragment.split(':',1)
        if len(kv)<2:
            self.fragments[kv[0]]='true'
        else:
            self.fragments[kv[0]]=kv[1]

    @classmethod
    def fragValueToRange(cls,fragVal:str)->typing.Tuple[int,int]:
        """
        Convert a fragment value (eg row:10-20) into a range (eg (10,20))

        See also:
            https://datatracker.ietf.org/doc/html/rfc5147#section-2.1.2

        Returns a tuple of (fromInt,toInt), the default is (0,-1)
        """
        fromInt=0
        toInt=-1
        for val in fragVal.split(','):
            startEnd=[s.strip() for s in val.split('-',1)]
            if startEnd[0] and startEnd[0].isdigit():
                v=int(startEnd[0])
                if v>fromInt:
                    fromInt=v
            if len(startEnd)>1 and startEnd[1] and startEnd[1].isdigit():
                v=int(startEnd[1])
                if toInt==-1 or v>toInt:
                    toInt=v
        return fromInt,toInt

    @property
    def extension(self)->str:
        """
        The extension without the dot
        that is, "png", not ".png"

        NOTE: extensions are ALWAYS lower case,
        even if that's not how the url had it
        """
        if self.resource is not None:
            s=self.resource.rsplit('.',1)
            if len(s)>1:
                return s[1].lower()
        return ''
    @property
    def ext(self)->str:
        """
        The file extension if there is one
        """
        return self.extension
    @property
    def fileExtension(self)->str:
        """
        The file extension if there is one
        """
        return self.extension

    @property
    def dirPath(self)->str:
        """
        directory location path

        eg http://x.com/foo/bar/baz.htm
            dirpath=/foo/bar

        or in other words
            dirpath+'/'+filename is usually self.path
        """
        ret=''
        if self.path:
            if self.path.endswith('/'):
                ret=self.path[0:-1]
            else:
                p=self.path.split('/')
                if len(p)>1:
                    ret='/'.join(p[0:-1])
                else:
                    ret=p[0]
        return ret

    def openInBrowser(self,
        preferred:typing.Optional[str]=None,
        newWindow:bool=False,
        newTab:bool=False,
        autoRaise:bool=True
        )->typing.Any:
        """
        Open this url in the system browser

        Preferred can be whatever python's built-in webbrowser module supports
        For instance:
            'mozilla'
            'firefox'
            'netscape'
            'galeon'
            'epiphany'
            'skipstone'
            'kfmclient'
            'konqueror'
            'kfm'
            'mosaic'
            'opera'
            'grail'
            'links'
            'elinks'
            'lynx'
            'w3m'
            'windows-default'
            'macosx'
            'safari'
            'google-chrome'
            'chrome'
            'chromium'
            'chromium-browser'
        """
        import webbrowser
        new=0
        if newWindow:
            new=1
        elif newTab:
            new=2
        browser=webbrowser.get(preferred)
        browser.open(str(self),new,autoRaise)
        return browser

    @property
    def filename(self)->str: # type: ignore
        """
        Url.filename is ambiguous.  Use: Url.resource instead
        """
        raise NotImplementedError(
            "Url.filename is ambiguous.  Use: Url.resource instead")
    @filename.setter
    def filename(self,filename:str): # type: ignore
        _=filename
        raise NotImplementedError(
            "Url.filename is ambiguous.  Use: Url.resource instead")

    def clear(self)->None:
        """
        clean out existing data
        """
        self.scheme=''
        self.auth=''
        self.host=None
        self.port=None
        self.path=''
        self.isUNC=False
        if self.cgi:
            self.cgi.clear()
        self._fragment=None
        self.fragments.clear()
        self._isDirectory=None

    @property
    def url(self # type: ignore
        )->"URL":
        """
        create an identical copy
        """
        return URL(self) # type: ignore
    @url.setter
    def url(self,url:URLCompatible):
        self.assign(url)

    def copy(self)->"URL":
        """
        create an identical copy
        """
        return URL(self) # type: ignore

    def replace(self,
        replaceThis:typing.Union[str,typing.Pattern[str]],
        withThis:typing.Union[str,typing.Any]
        )->"URL":
        """
        Does everything that str.replace() does, so url.replace(x,y)
        is exactly the same as Url(str(url).replace(x,y))
        Also, if you pass in a compiled regex for replaceThis,
        it is smart enough to use the regex.sub() instead

        NOTE: if you are trying to replace something with path separators,
        always use "/"
        NOTE: if your replacement makes this an un-parsable Url(),
        that's on you!
        """
        s=str(self)
        if not isinstance(withThis,str):
            withThis=str(withThis)
        if isinstance(replaceThis,str):
            s=s.replace(replaceThis,withThis)
        else:
            s=replaceThis.sub(withThis,s)
        return URL(s)

    def call(self,**kwargs:typing.ParamSpecKwargs)->str:
        """
        If URL.read() is not advanced enough, you can use this
        to pass cgi parameters.

        You can pass in cgi arguments also!
        Thus:
            u=URL('https://fooblatz.com/something.cgi')
            u.call(name="fred flintstone")
        Constructs and fetches:
            'https://fooblatz.com/something.cgi?name=fred+flintstone')
        NOTE: this is also how you can call the class like a function
            u(name="fred flintstone")
        """
        if kwargs:
            url=self.copy()
            url.cgi.update(kwargs) # type: ignore
            return url.read()
        return self.read()
    __call__=call

    @property
    def auth(self)->str:
        """
        full authentication section of the url

        NOTE: it may be easier for you
        to set username and password individually
        """
        if self.username is None or not self.username:
            return ''
        if self.password is None or not self.password:
            return self.username
        return '%s:%s'%(self.username,self.password)
    @auth.setter
    def auth(self,auth:str):
        if not auth:
            self.username=None
            self.password=None
        else:
            kv=auth.split(':',1)
            self.username=kv[0].strip()
            if len(kv)>1:
                self.password=kv[1].strip()
            else:
                self.password=None

    def isLocalhost(self)->bool:
        """
        returns whether the host is referring to ourselves

        NOTE: presently only supports "localhost", "127.0.0.1", or "::1"
            may someday be expanded to do a lookup to match against other ip's
            but for now keeping it simple
        """
        return self.host in (None,'','localhost','127.0.0.1','::1')

    def getFilePath(self,
        enquote:bool=True,
        illegalChars:typing.Optional[str]=None,
        errors:str='exception'
        )->typing.Optional[str]:
        """
        for file:// urls, convert back into a native filesystem path
        (only works for host=localhost)

        (Other url schemes will return None!)

        enquote: whether to call enquoteFilePath() default=True
        illegalChars: a string of illegal filename characters
            if None, use os alone
        errors: works similarly to str.encode("",errors="ignore")
            can be "ignore" or "exception"(default)
            or something else to replace the chars with
        """
        osForPath:str='posix'
        if self.scheme!='file' or not (self.isUNC or self.isLocalhost()):
            return None
        path=self.urlString
        path=path.split('://',1)[-1].split('?',1)[0]
        if os.sep!='/':
            osForPath='nt'
            path=path.replace('/',os.sep)
            # assuming windows, root doesn't start with /
            while path and path[0]==os.sep:
                path=path[1:]
        if self.isUNC:
            osForPath='nt'
            path='\\\\'+path
        path=urllib.parse.unquote_plus(path)
        # NOTE: os for path is inferred from the path itself
        # the path separator and a drive-letter colon are structural,
        # not illegal file content, so they must not be flagged here
        pathIllegalChars=illegalChars
        if pathIllegalChars is None:
            pathIllegalChars=illegalCharsForOs(osForPath)
        pathIllegalChars=pathIllegalChars.replace(os.sep,'')
        if osForPath=='nt' and len(path)>1 and path[1]==':':
            pathIllegalChars=pathIllegalChars.replace(':','')
        path=encodeFilePath(path,enquote,pathIllegalChars,None,errors)
        return path

    @property
    def filePath(self)->typing.Optional[str]:
        """
        for file:// urls, convert back into a native filesystem path
        (only works for host=localhost)

        (Other url schemes will return None!)

        NOTE: reading this is the same as calling
            self.getFilePath(enquote=False,illegalChars=None,errors='exception')
        """
        return self.getFilePath(
            enquote=False,illegalChars=None,errors='exception')
    @filePath.setter
    def filePath(self,filepath:str):
        self.assign(filepath)

    @property
    def protocol(self)->str:
        """
        alias for self.scheme
        """
        return self.scheme
    @protocol.setter
    def protocol(self,protocol:str):
        self.scheme=protocol

    @property
    def isAbsolute(self)->bool: # type: ignore
        """
        A url is absolute if it has a host, or its path starts at the root
        """
        if self.host is not None:
            return True
        return bool(self._path) and self._path.startswith('/')

    @property
    def path(self)->str:
        """
        the path portion of the url
        """
        if self._path is None:
            return ''
        return self._path
    @path.setter
    def path(self,path:str):
        """
        fix a path by removing .. and . entries
            example
                /x//./y/..
            returns
                /x
        """
        if not path:
            self._path=None
            return
        ret:typing.List[str]=[]
        pathElements=path.replace('//','/').replace('//','/').split('/')
        if pathElements.count('C:')>1:
            raise Exception('Attempt to set two c:')
        d=False
        for item in pathElements:
            if item=='..':
                if not ret:
                    raise Exception('Path navigates up past root:\n   %s'%path)
                if len(ret)==1 and ret[0].endswith(':'):
                    # like c:
                    raise Exception('Path navigates up past root:\n   %s'%path)
                if len(ret)==2 \
                    and not ret[0] \
                    and (not ret[1] or ret[1].endswith(':')):
                    # like / or /c:
                    raise Exception('Path navigates up past root:\n   %s'%path)
                ret.pop()
                d=True
            elif item=='.':
                d=True
            else:
                ret.append(item)
                d=False
        if d:
            ret.append('')
        self._path=('/'.join(ret)).replace('//','/').replace('//','/')

    def __cmp__(self,other:URLCompatible)->int:
        """
        Oldschool compare
        """
        for a,b in zip(self.path,asURL(other).path):
            if a==b:
                continue
            if a<b:
                return -1
            return 1
        return 0
    # Implementing the new dunder methods using __cmp__
    def __lt__(self,other:URLCompatible):
        return self.__cmp__(other)<0
    def __le__(self,other:URLCompatible):
        return self.__cmp__(other)<=0
    def __eq__(self,other:URLCompatible): # type: ignore
        return self.__cmp__(other)==0
    def __ne__(self,other:URLCompatible): # type: ignore
        return self.__cmp__(other)!=0
    def __gt__(self, other:URLCompatible):
        return self.__cmp__(other)>0
    def __ge__(self,other:URLCompatible):
        return self.__cmp__(other)>=0

    def __hash__(self)->int:
        """
        Hashing function for adding to lookup dicts
        """
        return self.url.__hash__()

    def sameDomain(self,
        other:typing.Optional[URLCompatible]
        )->bool:
        """
        returns true if the given urls are of the same domain
            (disregarding the domain prefix)
        """
        if other is None:
            return False
        otherUrl=asURL(other)
        if not self.domain:
            return self.domain==otherUrl.domain
        if not otherUrl.domain:
            return False
        return self.domain.lower()==otherUrl.domain.lower()
    domainMatches=sameDomain

    @classmethod
    def urlencode(cls,s:str)->str:
        """
        General-purpose url encode tool
        """
        return urllib.parse.quote(s)
    @classmethod
    def urldecode(cls,s:str)->str:
        """
        General-purpose url decode tool
        """
        return urllib.parse.unquote(s)

    @property
    def urlString(self)->str: # type: ignore
        """
        the url in plain old string form
        """
        ret:typing.List[str]=[self.protocol,'://']
        if self.username is not None:
            ret.append(urllib.parse.quote(self.username))
            if self.password is not None:
                ret.append(':')
                ret.append(urllib.parse.quote(self.password))
            ret.append('@')
        if self.isUNC:
            ret.append('///')
        if self.protocol=='file' and self.port is None and self.isLocalhost():
            pass # leave host portion of the url blank
        else:
            if self.host is None:
                ret.append('')
            else:
                ret.append(urllib.parse.quote(self.host))
            if self.port is not None:
                ret.append(':')
                ret.append(str(self.port))
        if self.path:
            if self.host is not None:
                ret.append('/')
            allowColons=self.protocol=='file'
            px:typing.List[str]=[]
            for p in self.path.split('/'):
                if self.ignoreAlreadyEncoded:
                    p=p.replace(r'%',r'//%PCT%//')
                    p=urllib.parse.quote(p)
                    p=p.replace(r'//%25PCT%25//',r'%')
                else:
                    p=urllib.parse.quote(p)
                if allowColons:
                    # special case: when there's a colon in the first path
                    # segment such as windows files
                    px.append(p.replace('%3A',self.windowsDriveSeparator))
                else:
                    px.append(p)
            ret.append('/'.join(px))
        if (not self.path) or (self.host is not None):
            ret.append('/')
        if self.resource is not None:
            ret.append(urllib.parse.quote(self.resource))
        query=self.cgi.queryString
        if query:
            ret.append(query)
        return ''.join(ret)
    @urlString.setter
    def urlString(self,url:URLCompatible):
        self.assign(url)
    name=urlString
    def __repr__(self)->str:
        """
        string representation of the url
        """
        return self.urlString
    def __str__(self)->str:
        """
        string representation of the url
        """
        return self.urlString

    @property
    def shortName(self)->str:
        """
        for "/path/to/foo.html" return "foo"
        """
        return self.path

    @property
    def nameWithExtension(self)->str:
        """
        for "/path/to/foo.html" return "foo.html"
        """
        return self.path

    def _encodeStr(self)->str: # type: ignore
        """
        Encode this to a string
        (used for saving .url files)
        """
        from .urlFileFormat import UrlFileFormat
        f=UrlFileFormat(self.urlString)
        return f.encode()

    def _decodeStr(self,data:str)->None: # type: ignore
        """
        Decode this from a string
        (used for loading .url files)
        """
        from .urlFileFormat import UrlFileFormat,isUrlFileData
        if not isUrlFileData(data):
            self.assign(Url(data)) # type: ignore
            return
        f=UrlFileFormat("")
        f.assign(self) # type: ignore
        self.assign(f) # type: ignore

    @property
    def fullPath(self)->typing.Optional[str]:
        """
        path, including the resource
        """
        if not self.path:
            if self.resource is None:
                return None
            return self.resource
        if self.resource is None:
            return self.path
        return self.path+'/'+self.resource
    @fullPath.setter
    def fullPath(self,fullPath:typing.Optional[str]):
        if fullPath is None or not fullPath:
            self._path=None
            self.resource=None
            return
        pr=fullPath.rsplit('/',1)
        self.resource=pr[-1]
        if len(pr)>1:
            self.path=pr[0]
        else:
            self._path=None

    def hyperlink(self,caption:typing.Optional[str]=None)->str:
        """
        Get this url as a hyperlink <a href="">caption</a>
        """
        href=str(self)
        if caption is None:
            caption=href
        return f'<a href="{href}">{caption}</a>'
    @property
    def html(self)->str:
        """
        Get this url as a hyperlink <a href="">caption</a>
        """
        return self.hyperlink()

    @property
    def user(self)->typing.Optional[str]:
        """
        alias of self.username
        """
        return self.username
    @user.setter
    def user(self,user:typing.Optional[str]):
        self.username=user

    @property
    def host(self)->typing.Optional[str]:
        """
        NOTE: that is self.host = self.subdomain + self.domain
            eg "www.fooblatz.com"="www"+"."+"fooblatz.com"
        """
        if not self.domain:
            return None
        if self.subdomain is not None:
            return '%s.%s'%(self.subdomain,self.domain)
        return self.domain
    @host.setter
    def host(self,host:typing.Optional[str]):
        if host is None:
            self.domain=''
            self.subdomain=None
        else:
            ss=host.split('.')
            if len(ss)==4 and ss[-1].isdigit():
                # looks like ip address to me
                self.domain=host
                self.subdomain=None
            elif len(ss)>2:
                # split off subdomain like www.fooblatz.com
                # into www and fooblatz.com
                self.subdomain='.'.join(ss[0:len(ss)-2])
                self.domain='.'.join(ss[-2:])
            else:
                # this has no subdomain
                self.domain=host
                self.subdomain=None

    def urlMatches(
        self,
        matches:"UrlMatchable",
        ignoreCase:typing.Optional[bool]=None
        )->bool:
        """
        Check if this url matches one or more url's and/or patterns

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
        from paths.urlMatch import urlMatches
        return urlMatches(self,matches,ignoreCase) # type: ignore
    fileMatches=urlMatches
    matches=urlMatches

    @classmethod
    def _getUrlString(cls,
        url:typing.Optional[URLCompatible]
        )->typing.Optional[str]:
        """
        get the best(tm) possible url string from an object

        throws MalformedUrlException if it can't get anything reasonable.

        NOTE: the
        """
        if url is None:
            return None
        if isinstance(url,URL):
            return str(url)
        elif isinstance(url,pathlib.Path):
            url=str(url)
        if isinstance(url,bytes):
            url=url.decode('utf-8','ignore')
        if isinstance(url,str):
            url=url.lstrip()
            # handle if it looks like a .url file content
            if url.lower().startswith('[internetshortcut]'):
                found=False
                for line in url.splitlines():
                    line=line.lstrip()
                    if line.lower().startswith('url='):
                        url=line[4:].strip()
                        found=True
                        break
                if not found:
                    raise Exception('Malformed .url file: missing "URL=" line')
            # if it's blank, treat it the same as None
            if not url:
                return None
        else:
            # check its members for something url-like
            foundSomething=False
            for memberName in cls.URL_LIKE_MEMBERS:
                if hasattr(url,memberName):
                    foundSomething=True
                    url=getattr(url,memberName)
                    if callable(url):
                        url=url()
                    if isinstance(url,URL):
                        # in case the member was a URL obj
                        return str(url.url)
                    break
            if (not foundSomething) \
                and hasattr(url,'read') \
                and hasattr(url,'name'):
                # for file-like objects "name" can be considered a filename
                foundSomething=True
                url=getattr(url,'name')
            if (not foundSomething) and hasattr(url,'keys'):
                # it's a dict-like, so we can check that too
                keys:typing.Iterable[str]=url.keys() # type: ignore
                for memberName in cls.URL_LIKE_MEMBERS:
                    if memberName in keys:
                        foundSomething=True
                        url=url[memberName] # type: ignore
                        if callable(url):
                            url=url()
                        if isinstance(url,URL):
                            # in case the member was a URL obj
                            return str(url)
                        break
            if not isinstance(url,str):
                # couldn't figure out how that object translates into a URL
                typename=url.__class__.__name__
                raise MalformedURL(
                    str(url),f'incompatible type {typename} for assigning')
        try:
            url=cls._getCleverURL(url)
        except MalformedURL:
            # must be a filename I guess
            url=str(url).replace('\\','/')
            url='file://'+url
        return url

    @property
    def isFile(self)->bool:
        """
        This is deprecated because it is ambiguous.
        Use url.protocol=="file" or (url.exists and not url.isDirectory)
        instead
        """
        raise DeprecationWarning('isFile is ambiguious, use url.protocol=="file" or (url.exists and not url.isDirectory) instead') # noqa: E501 # pylint: disable=line-too-long

    @property
    def isBinaryFile(self)->bool:
        """
        Utility to check a file to see if it's "binary" or not

        This is very basic.  For more strategies, see:
        http://stackoverflow.com/questions/898669/how-can-i-detect-if-a-file-is-binary-non-text-in-python
        """
        if self.isDirectory:
            return False
        while True:
            character=self.readBytes(1) # the first byte of a short might be null if we're Unicode. # noqa: E501 # pylint: disable=line-too-long
            if character==b'':
                break
            character=self.readBytes(1)
            if character==b'':
                break
            elif character==b'\0':
                self.close()
                return True
        self.close()
        return False

    @property
    def isTextFile(self)->bool:
        """
        Utility to check a file to see if it's "binary" or not
        """
        if self.isDirectory:
            return False
        return not self.isBinaryFile

    @property
    def isDirectory(self)->bool:
        """
        NOTE: for file:// urls we can determine this,
        but for other types it is merely a guess unless
        explicitly assigned.

        Eg: is http://fooblatz.com/items going to be a
            directory or a webpage?  Or both (implied index.htm)?
        But you can always set url.isDirectory=True to track that

        NOTE: the algorithm for determining if url is a directory is:
            1) if there is cgi, it IS NOT a directory
            2)
        """
        if self._isDirectory is None:
            if self.protocol=='file':
                if not self.filePath:
                    self._isDirectory=True # / is a directory
                else:
                    self._isDirectory=os.path.isdir(self.filePath)
            else:
                q=self.path.rsplit('/')
                self._isDirectory=q[-1].find('.')<0
        return self._isDirectory
    @isDirectory.setter
    def isDirectory(self,isDirectory:bool):
        self._isDirectory=isDirectory
    @property
    def isDir(self)->bool:
        """
        NOTE: for file:// urls we can determine this,
        but for other types it is merely a guess unless
        explicitly assigned.

        Eg: is http://fooblatz.com/items going to be a
            directory or a webpage?  Or both (implied index.htm)?
        But you can always set url.isDirectory=True to track that

        NOTE: the algorithm for determining if url is a directory is:
            1) if there is cgi, it IS NOT a directory
            2)
        """
        return self.isDirectory
    @isDir.setter
    def isDir(self,isDir:bool):
        self.isDirectory=isDir

    def assign(self, # type: ignore # pylint: disable=arguments-renamed
        url:typing.Optional[URLCompatible],
        relativeTo:typing.Optional[URLCompatible]=None,
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
        from paths.urlSplitter import urlAssign
        urlAssign(self,url, # type: ignore
            relativeTo,maxParentLevels,maxChildLevels,_isDirectory)
    setUrl=assign

    def __add__(self,other:URLCompatible)->"Url": # type: ignore
        """
        You can use the + operator to create a new relative url

        Eg
            Url("c:\\something")+"something_else"
        is the same as
            Url("c:\\something\\something_else")
        """
        return Url(other,relativeTo=self) # type: ignore

    def __truediv__(self,other:URLCompatible)->"Url": # type: ignore
        """
        Implement the "/" operator like pathlib.Path has
        """
        return Url(other,relativeTo=self) # type: ignore

    def __ltruediv__(self,other:URLCompatible)->"Url": # type: ignore
        """
        Implement the "/" operator like pathlib.Path has
        """
        return Url(self,relativeTo=other) # type: ignore

Url=URL # same thing


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printHelp=False
    if not args:
        printHelp=True
    else:
        for arg in args:
            if arg.startswith('-'):
                av=[a.strip() for a in arg.split('=',1)]
                if av[0] in ['-h','--help']:
                    printHelp=True
                else:
                    print('ERR: unknown argument "'+av[0]+'"')
            else:
                print('ERR: unknown argument "'+arg+'"')
    if printHelp:
        print('Usage:')
        print('  URL.py [options]')
        print('Options:')
        print('   NONE')
    return 0


if __name__=='__main__':
    #import sys
    #cmdline(sys.argv[1:])
    u=URL(r'file:///c:/folder/')
    u=u.relative('childchild/../../..')
    print(u.fullPath)
    print('url=',u)
    print('filePath=',u.filePath)
