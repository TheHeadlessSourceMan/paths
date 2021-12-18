#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
This represents a url type
"""
from collections import OrderedDict
import typing
import os
import time
import urllib.parse


# --------------------- typing shenanigans
class HasURL(typing.Protocol):
    """
    Duck typing for any object that has a .URL member
    """
    url:typing.Union['URLCompatible',typing.Callable[[],'URLCompatible']]
    #def getUrl(self) -> typing.Union["URL",str]:
    #   ...  # Empty method body (explicit '...')

class DictLike(typing.Protocol):
    """
    Duck typing for a dict-like object
    """
    def keys(self)->str:
        ...
    def __getitem__(self,idx:str)->typing.Any:
        ...

class IsFileWithName(typing.Protocol):
    """
    a file object with a .name member, pointing to an existing filename on the system
    """
    fileno:int
    name:str

URLCompatibleStrict=typing.Union['URL',HasURL,IsFileWithName] # must be certain it is a url, not some other thing
URLCompatible=typing.Union[URLCompatibleStrict,str,bytes,DictLike]
UrlCompatibleStrict=URLCompatibleStrict
UrlCompatible=URLCompatible

def isUrlCompatible(obj:typing.Any,strict=False)->bool:
    if isinstance(obj,(str,bytes)) and not strict:
        return True
    return isinstance(obj,URL) or hasattr(obj,'url') or (hasattr(obj,"fileno") and hasattr(obj,"name"))
isURLCompatible=isUrlCompatible # alias name


# ------------------------- teh code
class MalformedURL(Exception):
    """
    This is thrown when a url is in bad form
    """
    
    def __init__(self,url:str,reason:str):
        Exception(self,'Malformed URL "'+url+'"\n('+reason+')')


def asURL(url:URLCompatible,relativeTo:typing.Optional[URLCompatible]=None)->typing.Union['URL',None]:
    r"""
    Gets the url always as a URL object or None if it is None or "".
    If url is a URL object, WILL NOT create a new one, otherwise, it will.
    If you would rather always have a new URL object, simply create an instance of URL(url)
        (because this supports passing a URL object as the initialization)

    Raises MalformedURL exception if it doesn't work.

    See also:
        https://www.ietf.org/rfc/rfc3986.html

    TODO:
        what about re, for instance ^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?
        or something from https://regexpattern.com/

    :param url: Can be:
        * another URL object
        * a properly-formatted URL string
        * any object with a (Url,url, or URL) data member
            or (filename,path) like it is referring to a file
            or even (href,src,location,rel) like in html-ish objects
        * a file object with a .name member
        * a system path+file where the path exists
    :type url: URLCompatible
    :param relativeTo: the url parameter is relative to this. eg asUrl('about.htm','http://fooblatz.com') gives "http://fooblatz.com/about.htm"
        if relativeTo is a simple string ending in ":" it suffices as a default protocol eg asURL('bob@mailbox.com','mailto:')
        if NONE, relativeTo is treated as "file://[current directory]" eg asUrl("readme.txt") gives "file://./readme.txt"
    :type relativeTo: str, optional
    :return: A URL object of url
    :rtype: URL
    """
    if url is None:
        return None
    if isinstance(url,URL):
        return url
    return URL(url)
asUrl=asURL # alias name


class URL:
    r"""
    Any URL of the form:
        <protocol>://<user>:<password>@<host>:<port>/<path...>/<resource>[?<option=value>&<option=value...>]
        
    All members of this object are properly decoded automatically.

    This includes local file paths, which are interpereted as file:// urls
        see: https://en.wikipedia.org/wiki/File_URI_scheme
        * does handle Windows paths (c:\dir\file)
        * does handle Windows UNC paths (\\machine\dir\file)
        * does handle technically malformed paths (file://filename should actually be file:///filename)

    This is directly compatible with urllib3 and backwards-compatible to urllib.

    You can do things like:
        u=Url('http://www.mysite.com/path/search?q=something&page=1')
        u['page']=2
        print(u)
        # prints "http://www.mysite.com/path/search?q=something&page=2"
        u['q']='this&that'
        print(u)
        # prints "http://www.mysite.com/path/search?q=this%26that&page=2"
        u=Url('http://www.mysite.com/path/search?q=this%26that&page=2')
        print(u['q'])
        # prints "this&that" (meaning the url encode/decode is fully automatic!)
        u2=u.relative('/images/1.jpg')
        print(u2)
        # prints "http://www.mysite.com/path/images/1.jpg"
        
    NOTE: specifying password in the url is generally considered bad form

    NOTE: has EXPERIMENTAL file-like object access

    TODO: IPv6 hosts
    """

    URL_LIKE_MEMBERS=['url','URL','Url','filename','path','href','src','location','rel'] # object members that could likely contain a url. order is important
    
    def __init__(self,url:URLCompatible=None,relativeTo:typing.Optional[URLCompatible]=None):
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
        :param relativeTo: the url parameter is relative to this. eg asUrl('about.htm','http://fooblatz.com') gives "http://fooblatz.com/about.htm"
            if relativeTo is a simple string ending in ":" it suffices as a default protocol eg asURL('bob@mailbox.com','mailto:')
            if NONE, relativeTo is treated as "file://[current directory]" eg asUrl("readme.txt") gives "file://./readme.txt"
        :type relativeTo: str, optional
        """
        self.URL_GETTER=None
        self.scheme:typing.Optional[str]=None
        self.username:typing.Optional[str]=None
        self.password:typing.Optional[str]=None
        self.domain:typing.Optional[str]=None
        self.subdomain:typing.Optional[str]=None
        self.port:typing.Optional[int]=None
        self._path:typing.Optional[str]=None
        self.cgi:typing.Dict[str,typing.Any]=OrderedDict()
        self.fragment:typing.Optional[str]=None
        self.isUNC:bool=False
        self.cache:bool=True
        self.persist:bool=True
        self.filesUrlPreferLocal:bool=True # given file://foo/bar assume foo is local as opposed to a host named foo  - basically False is more standards-compliant, but True is more used in practice
        self._data:typing.Optional[bytearray]=None
        self._idx:int=0
        if url is not None:
            self.assign(url,relativeTo)

    @property
    def parent(self):
        """
        parent directory
        """
        return self.relative('..')

    @property
    def root(self):
        """
        domain root directory
        """
        return self.relative('/')

    @property
    def dirPath(self):
        """
        directory location path

        eg http://x.com/foo/bar/baz.htm
            dirpath=/foo/bar

        or in other words
            dirpath+'/'+filename is usually self.path
        """
        ret=None
        if self.path is not None:
            if self.path.endswith('/'):
                ret=self.path[0:-1]
            else:
                p=self.path.split('/')
                if len(p)>1:
                    ret='/'.join(p[0:-1])
                else:
                    ret=[0]
        return ret
        
    @property
    def filename(self)->typing.Optional[str]:
        """
        get the filename portion of the url, for example
            http://x.com/foo/bar/baz.htm
            filename=baz.htm

        alias for self.resource
        """
        return self.resource
    @filename.setter
    def filename(self,filename:typing.Optional[str]):
        self.resource=filename

    def clear(self):
        """
        clean out existing data
        """
        self.scheme=None
        self.auth=None
        self.host=None
        self.port=None
        self.path=None
        self.isUNC=False
        self.cgi=OrderedDict()
        self.fragment=None

    def copy(self):
        """
        create an identical copy
        """
        return Url(self)

    def __len__(self):
        """
        access like a dict
        """
        return len(self.cgi)

    def __iter__(self):
        """
        access like a dict
        """
        return self.cgi.items().__iter__()

    def __setitem__(self,k,v):
        """
        access like a dict
        """
        self.cgi[k]=str(v)

    def __delitem__(self,k):
        """
        access like a dict
        """
        del self.cgi[k]

    def __getitem__(self,k):
        """
        access like a dict
        """
        return self.cgi.get(k)

    def items(self):
        """
        access like a dict
        """
        return self.cgi.items()

    def keys(self):
        """
        access like a dict
        """
        return self.cgi.keys()

    def values(self):
        """
        access like a dict
        """
        return self.cgi.values()

    def get(self,key,default=None):
        """
        access like a dict
        """
        return self.cgi.get(key,default)

    @property
    def query(self):
        """
        the query as a string

        NOTE: the self.cgi[x] dict is safer, easier, and simpler
        """
        if not self.cgi:
            return None
        return urllib.parse.urlencode(self.cgi)
    @query.setter
    def query(self,query):
        self.cgi={}
        if query is not None:
            query=urllib.parse.parse_qs(query,keep_blank_values=True)
            for k,vv in query.items():
                self.cgi[k]=vv[-1]

    @property
    def auth(self):
        """
        full authentication section of the url

        NOTE: it may be easier for you to set username and password individually
        """
        if self.username is None:
            return None
        if self.password is None:
            return self.username
        return '%s:%s'%(self.username,self.password)
    @auth.setter
    def auth(self,auth):
        if auth is None or not auth:
            self.username=None
            self.password=None
        else:
            auth=auth.split(':',1)
            self.username=auth[0]
            if len(auth)>1:
                self.password=auth[1]
            else:
                self.password=None

    def isLocalhost(self):
        """
        returns whether the host is referring to ourselves

        NOTE: presently only supports "localhost", "127.0.0.1", or "::1"
            may someday be expanded to do a lookup to match against other ip's
            but for now keeping it simple
        """
        return self.host in (None,'','localhost','127.0.0.1','::1')

    @property
    def filePath(self):
        """
        for file:// urls, convert back into a native filesystem path
        (only works for host=localhost)

        (Other url schemes will return None!)
        """
        if self.scheme!='file' or not (self.isUNC or self.isLocalhost()):
            return None
        path=self.url
        path=path.split('://')[-1].split('?',1)[0]
        if os.sep!='/':
            path=path.replace('/',os.sep)
            # assuming windows, root doesn't start with /
            while path and path[0]==os.sep:
                path=path[1:]
        if self.isUNC:
            path='\\\\'+path
        return path
    @filePath.setter
    def filePath(self,filepath):
        self.assign(filepath)

    @property
    def protocol(self):
        """
        alias for self.scheme
        """
        return self.scheme
    @protocol.setter
    def protocol(self,protocol):
        self.scheme=protocol

    @property
    def path(self):
        """
        the path portion of the url
        """
        return self._path
    @path.setter
    def path(self,path):
        """
        fix a path by removing .. and . entries
            example
                /x//./y/..
            returns
                /x
        """
        if path is None or not path:
            self._path=None
            return
        ret=[]
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
                if len(ret)==2 and not ret[0] and (not ret[1] or ret[1].endswith(':')):
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

    def __eq__(self,url:URLCompatible)->bool: # type: ignore
        """
        compare this url with another
        """
        urlObj=asURL(url)
        if urlObj is None:
            return False
        return (self.protocol==urlObj.protocol and
            self.username==urlObj.username and
            self.password==urlObj.password and
            self.host==urlObj.host and
            self.port==urlObj.port and
            self.path==urlObj.path and
            self.resource==urlObj.resource and
            self.cgi==urlObj.cgi)

    def __repr__(self)->str:
        """
        string representation of the url
        """
        return self.url

    def domainMatches(self,other:UrlCompatible)->bool:
        """
        alias for sameDomain()
        """
        return self.sameDomain(other)
    def sameDomain(self,other:UrlCompatible):
        """
        returns true if the given urls are of the same domain
            (disregarding the domain prefix)
        """
        otherUrl=asURL(other)
        if otherUrl is None:
            return False
        if self.domain is None:
            return self.domain==otherUrl.domain
        if otherUrl.domain is None:
            return False
        return self.domain.lower()==otherUrl.domain.lower()

    def location(self):
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

    def unRelativeUrl(self,url:URLCompatible)->typing.Optional['URL']:
        """
        alias of getRelativeUrl
        """
        return self.getRelativeUrl(url)
    def getRelativeUrl(self,url:typing.Optional[URLCompatible])->typing.Optional['URL']:
        """
        Turns a relative url (eg href="/about") to its full form.

        If it is already a full url, that's okay too.  It will simply return it.
        """
        if url is None:
            return None
        if not isinstance(url,str):
            # assume it is fully qualified, whatever it is
            return asURL(url)
        urlStr=str(url)
        currentLocation=self.location()
        if currentLocation=='':
            return asURL(urlStr)
        while currentLocation[-1]=='/':
            currentLocation=currentLocation[0:-1]
        protoPos=urlStr.find('://')
        if (protoPos>0 and protoPos<6):# or getDomain(currentLocation)==getDomain(urlStr):
            return asURL(urlStr)
        currentParts=currentLocation.split('/')
        lastEmpty=False
        for step in urlStr.split('/'):
            if step in ('','.'):
                lastEmpty=True
                pass
            elif step=='..':
                lastEmpty=False
                # check if we are navigating past root
                # or if windows file, we are trying to navigate past c:/
                if len(currentParts)<5:
                    if len(currentParts)<4 or currentParts[3].endswith(':'):
                        raise MalformedURL(urlStr,'Attempt to navigate past root in "%s"'%currentLocation)
                # go up a level
                currentParts.pop()
            else:
                lastEmpty=False
                currentParts.append(step)
        if lastEmpty: # special case where we end in a /
            currentParts.append('')
        urlStr='/'.join(currentParts)
        return asURL(urlStr)
    def relative(self,subPath):
        """
        Get a url relative to this url

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

        NOTE: if subPath is a full url (eg 'http://whatever') then there is no resolving
        """
        return self.getRelativeUrl(subPath)
        if subPath is None:
            ret=self
        elif not isinstance(subPath,str) or subPath.find('://')>=0:
            ret=Url(subPath)
        else:
            ret=Url(self)
            ret.path='%s/%s'%(self.path.rsplit('/',1)[0],subPath)
        return ret

    def watch(self,notifyFn=None,pollInterval:float=1):
        """
        If there is a notifyFn, will run forever (meant to be run threaded)
        
        If not, will return when the data has changed.
        """
        d=self._data
        while True:
            time.sleep(pollInterval)
            self.read()
            if self.data!=d:
                if notifyFn is None:
                    return
                else:
                    notifyFn(self)
        
    @property
    def url(self)->str:
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
        if self.path is not None:
            if self.host is not None:
                ret.append('/')
            allowColons=self.protocol=='file'
            px=[]
            for p in self.path.split('/'):
                if allowColons:
                    # special case: when there's a colon in the first path segment, such as windows files
                    px.append(urllib.parse.quote(p).replace('%3A',':'))
                else:
                    px.append(urllib.parse.quote(p))
            ret.append('/'.join(px))
        if self.path is not None or self.host is not None:
            ret.append('/')
        if self.resource is not None:
            ret.append(urllib.parse.quote(self.resource))
        if self.cgi:
            rr:typing.List[str]=[]
            for k,v in self.cgi.items():
                if k is None or not k:
                    continue
                kv=[urllib.parse.quote(k)]
                if v is not None:
                    kv.append(urllib.parse.quote(str(v)))
                rr.append('='.join(kv))
            if rr:
                ret.append('?')
                ret.append('&'.join(rr))
        return ''.join(ret)
    @url.setter
    def url(self,url):
        self.assign(url)
        
    @property
    def name(self)->str:
        """
        same as the url itself

        used for compatibility where objects with names are expected
        """
        return self.url
    @name.setter
    def name(self,name:str):
        self.url=name
        
    @property
    def data(self):
        """
        the remote data
        (will be read on demand)
        """
        if self._data is None:
            self._readFile()
        return self._data
    @data.setter
    def data(self,data):
        self.write(data)
        
    def write(self,data:typing.Union[str,bytes])->None:
        """
        file-like object write method
        """
        self._dirty=True
        if isinstance(data,str):
            data=data.encode('utf-8')
        if self._data is None:
            self._data=bytearray(data)
        else:
            self._data.extend(data)
        
    def close(self):
        """
        file-like object close method
        """
        self.flush()
        self._data=None
        self._idx=0
        
    def flush(self):
        """
        file-like object flush method
        """
        if self._dirty and self._data is not None:
            self._writeFile()
        self._dirty=False
        
    def read(self,bytes:typing.Optional[int]=None)->str:
        """
        file-like object read method
        """
        if bytes is None:
            ret=self.data[self._idx:len(self.data)]
            self._idx=len(self.data)
        else:
            ret=self.data[self._idx:min(self._idx+bytes,len(self.data))]
            self._idx+=len(ret)
        return ret.decode('utf-8')

    def _readFile(self)->None:
        """
        Physically go and read the file right now
        """
        # TODO: use EzFs instead if installed
        if self.protocol=='file':
            f=open(self.filePath,'rb')
            self._data=bytearray(f.read())
            f.close()
        else:
            # TODO: read typical things python can read, such as http and ftp
            raise NotImplementedError()

    def _writeFile(self)->None:
        """
        Physically go and write the file right now
        """
        # TODO: use EzFs instead if installed
        if self.protocol=='file':
            f=open(self.filePath,'wb')
            if self._data is not None:
                f.write(bytes(self._data))
            f.close()
        else:
            # TODO: read typical things python can read, such as http and ftp
            raise NotImplementedError()

    def seek(self,idx:int,fromWhere:int=0):
        """
        file-like object seek method
        """
        if fromWhere==0: # means your reference point is the beginning of the file
            self._idx=idx
        elif fromWhere==1: # means your reference point is the current file position
            self._idx+=idx
        elif fromWhere==2: # means your reference point is the end of the file
            self._idx=len(self.data)-idx
        
    def tell(self)->int:
        return self._idx

    @property
    def fullPath(self)->typing.Optional[str]:
        """
        path, including the resource
        """
        if self.path is None:
            if self.resource is None:
                return None
            return self.resource
        if self.resource is None:
            return self.path
        return self.path+'/'+self.resource
    @fullPath.setter
    def fullPath(self,fullPath:typing.Optional[str]):
        if fullPath is None or not fullPath:
            self.path=None
            self.resource=None
            return
        pr=fullPath.rsplit('/',1)
        self.resource=pr[-1]
        if len(pr)>1:
            self.path=pr[0]
        else:
            self.path=None
        if fullPath.find('//')>1:
            raise Exception()

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
        if self.domain is None:
            return None
        if self.subdomain is not None:
            return '%s.%s'%(self.subdomain,self.domain)
        return self.domain
    @host.setter
    def host(self,host:typing.Optional[str]):
        if host is None:
            self.domain=None
            self.subdomain=None
        else:
            ss=host.split('.')
            if len(ss)==4 and ss[-1].isdigit():
                # looks like ip address to me
                self.domain=host
                self.subdomain=None
            elif len(ss)>2:
                # split off subdomain like www.fooblatz.com into www and fooblatz.com
                self.subdomain='.'.join(ss[0:len(ss)-2])
                self.domain='.'.join(ss[-2:])
            else:
                # this has no subdomain
                self.domain=host
                self.subdomain=None
    
    def _getUrlString(self,url:UrlCompatible)->typing.Union[str,"URL"]:
        """
        get the best(tm) possible url string from an object

        throws MalformedUrlException if it can't get anything reasonable.

        NOTE: the
        """
        if url is None:
            return None
        if isinstance(url,URL):
            return url
        if not isinstance(url,(str,bytes)):
            # check its members for something url-like
            foundSomething=False
            for memberName in self.URL_LIKE_MEMBERS:
                if hasattr(url,memberName):
                    foundSomething=True
                    url=getattr(url,memberName)
                    if callable(url):
                        url=url()
                    if isinstance(url,URL):
                        # in case the member was a URL obj
                        return url
                    break
            if (not foundSomething) and hasattr(url,'read') and hasattr(url,'name'):
                # for file-like objects "name" can be considered a filename
                foundSomething=True
                url=getattr(url,'name')
            if (not foundSomething) and hasattr(url,'keys'):
                # it's a dict-like, so we can check that too
                keys=url.keys() # type: ignore
                for memberName in self.URL_LIKE_MEMBERS:
                    if memberName in keys:
                        foundSomething=True
                        url=url[memberName] # type: ignore
                        if callable(url):
                            url=url()
                        if isinstance(url,URL):
                            # in case the member was a URL obj
                            return url
                        break
            if not isinstance(url,str):
                # couldn't figure out how that object translates into a URL
                raise MalformedURL(str(url),'incompatible type %s for assigning'%url.__class__.__name__)
        if isinstance(url,bytes):
            url=url.decode('utf-8')
        return url

    def _getCleverURL(self,url:str)->typing.Optional["URL"]:
        """
        This is a hook used to get cleverly get things as urls,
        for instance 
        "sam@abc.com"->"mailto:sam@abc.com"
        "(800)555-1234"->"tel:+18005551234"
        """
        # TODO: this is an interesting concept, but needs
        # 1) to be more extensible
        # 2) called only after proper urls get their chance
        # 3) need some mechanism for getting these from an object
        return None

    def setUrl(self,url:URLCompatible,assume='http'):
        """
        same as assign()
        """
    def assign(self,url:typing.Optional[URLCompatible],relativeTo:typing.Optional[URLCompatible],_useRelTo=True)->None:
        """
        Assign this url to something

        Raises MalformedURL exception if it doesn't work.

        NOTE: unlike many things like asURL(), relativeTo has no default =None (which will assume file://[current directory]).
            This is because in most cases you probably want to be relative to the current location eg
                myUrl.assign(url,myUrl)
            Removing the default was intended to force the caller to be specific in their intent.

        :param url: Can be:
            * another URL object
            * a properly-formatted URL string
            * any object with a (Url,url, or URL) data member
                or (filename,path) like it is referring to a file
                or even (href,src,location,rel) like in html-ish objects
            * a file object with a .name member
            * a system path+file where the path exists
        :type url: URLCompatible
        :param relativeTo: the url parameter is relative to this. eg asUrl('about.htm','http://fooblatz.com') gives "http://fooblatz.com/about.htm"
            if relativeTo is a simple string ending in ":" it suffices as a default protocol eg asURL('bob@mailbox.com','mailto:')
            if NONE, relativeTo is treated as "file:///[current directory]" eg asUrl("readme.txt") gives "file:///./readme.txt"
        :type relativeTo: URLCompatible
        """
        self.clear()
        if url is None:
            return
        url=self._getUrlString(url)
        if isinstance(url,URL):
            self.scheme=url.scheme
            self.username=url.username
            self.password=url.password
            self.host=url.host
            self.port=url.port
            self.path=url.path
            self.isUNC=url.isUNC
            self.resource=url.resource
            self.cgi=url.cgi
            return
        # by now url is ALWAYS a simple url string
        url2:typing.Union[None,"URL"]=self._getCleverURL(url)
        if url2 is not None:
            self.assign(url2,None)
            return
        # check for possibly malformed file://
        #    technically file://foo/bar means foo=host, though most people assume foo is directory
        #    the "correct" way of foo as a directory is file:///foo/bar
        #    this section attemts to guess what they really meant and correct as necessary
        #    the algorithm used to determine to treat foo is a local file:
        #        * if self.filesUrlPreferLocal is True
        #        * if there is no more to the path assume they meant file://file not file://host
        #        * if first dir ends with a :, assume they meant file://c: not host named c
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
            # the format is different than url, so it makes more sense to do this manually
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
            # the format is different than url, so it makes more sense to do this manually
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
            relativeTo='file:///./' # no real need as c:\ is an absolute path
            url='/'+url.replace('\\','/')
        elif os.sep!='/':
            url=url.replace(os.sep,'/')
        # url is always using '/' as the separator from here on out
        # make sure relativeTo is ready for use
        if _useRelTo:
            if relativeTo is None:
                relativeTo='file:///./'
            rTo=URL()
            rTo.assign(relativeTo,None,False)
            if rTo is None:
                raise MalformedURL(str(relativeTo),"Unable to parse url for relativeTo")
            else:
                relativeTo=rTo
        # let the standard parser have a go at it
        parsed=urllib.parse.urlparse(url)
        ret=URL()
        ret.scheme=parsed.scheme
        ret.username=parsed.username
        ret.password=parsed.password
        ret.host=parsed.hostname
        if ret.host is None or ret.host=='':
            ret.host='localhost'
        ret.port=parsed.port
        path=parsed.path
        if isWindowsAbsolutePath:
            # TODO: I believe they also sometimes used to use '|' instead of ':'. Should we support this?
            path.replace('%3A',':',1) # url decode where they encoded the ':'
            ret.scheme='file'
        if path.startswith('/'):
            path=path[1:]
        ret.fullPath=path
        ret.cgi={}
        if parsed.query is not None:
            cgi=parsed.query.split('&')
            for c in cgi:
                item=[urllib.parse.unquote(v) for v in c.split('=',1)]
                if len(item)<2:
                    ret.cgi[item[0]]=None
                else:
                    ret.cgi[item[0]]=item[1]
        if ret.protocol is None and _useRelTo:
            r2=relativeTo.getRelativeUrl(ret) # type: ignore
            if r2 is None:
                MalformedURL(url,'relative url broke')
            else:
                ret=r2
        if ret.host is None and ret.protocol!='file':
            MalformedURL(url,'missing host')
        if self.protocol!='file' and self.path is not None:
            # remove any leading / from path
            if path.startswith('/'):
                path=path[1:]
        self.assign(ret,None)


Url=URL # same thing

        
def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printhelp=False
    if not args:
        printhelp=True
    else:
        for arg in args:
            if arg.startswith('-'):
                av=[a.strip() for a in arg.split('=',1)]
                if av[0] in ['-h','--help']:
                    printhelp=True
                else:
                    print('ERR: unknown argument "'+av[0]+'"')
            else:
                print('ERR: unknown argument "'+arg+'"')
    if printhelp:
        print('Usage:')
        print('  URL.py [options]')
        print('Options:')
        print('   NONE')
    return 0


if __name__=='__main__':
    import sys
    #cmdline(sys.argv[1:])
    u=URL(r'file:///c:/folder/')
    u=u.relative('childchild/../../..')
    print(u.fullPath)
    print('url=',u)
    print('filePath=',u.filePath)
