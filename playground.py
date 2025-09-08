"""
Experimental features I am playing around with
"""
from cProfile import run
from timeit import timeit
import os
import typing
import re

_URL_REGEXES:typing.Optional[typing.List[typing.Pattern]]=None

class UrlNew:
    """
    New-style url
    """

    def __init__(self,s:str):
        self.assign(s)

    @property
    def _uncRegex(self):
        """
        Create a regular expression for parsing unc paths
        """
        regex=r"""(?P<uncPath>\\{2}.*)"""
        return re.compile(regex)
    def _assignUncPath(self,uncPath):
        pass

    @property
    def _urlRegex(self):
        """
        Create a regular expression for parsing urls
        """
        proto=r"""((?P<proto>[a-z]+):(//){1})"""
        host=r"""(?P<host>[0-9a-z]+[.][0-9a-z.]+)"""
        port=r"""(:(?P<port>[0-9]+))"""
        location=r"""("""+host+port+r"""?)"""
        login=r"""((?P<username>[-a-z0-9_.]*)?(:(?P<password>[-a-z0-9_]*))?@)"""
        resource=r"""(/((?P<path>[-a-z0-9_./]*?)(?P<resource>/[-a-z0-9_.])?)(\#(?P<part>.*))?(\?(?P<cgi>.*)))""" # pylint: disable:line-too-long
        regex=r"""(?P<url>"""+proto+login+r"""?"""+location+resource+r"""?)"""
        return re.compile(regex,re.IGNORECASE)
    def _assignUrl(self,
        url:str,
        proto:str,
        host:str,
        port:typing.Optional[str]=None,
        username:typing.Optional[str]=None,
        password:typing.Optional[str]=None,
        path:str='',
        resource:str='',
        part:typing.Optional[str]=None,
        cgi:typing.Dict[str,str]={}
        )->None:
        """
        specific assignment
        """
        self.filePath=None
        self.url=url
        self.proto=proto
        self.host=host
        self.port=port
        self.part=part
        self.cgi.clear()
        self.cgi.update(cgi)
        self.username=username
        self.password=password
        self.path=path
        self.resource=resource
        self.relative=False

    @property
    def _dosFilePathRegex(self):
        """
        Create a regular expression for parsing urls
        """
        regex=r"""(?P<dosFilePath>(([a-z]:)|[\\.])(.*))"""
        return re.compile(regex)
    def _assignDosFilePath(self,dosFilePath):
        self.filePath=dosFilePath
        fixedPath=dosFilePath.replace('\\','/')
        self.url='file://'+fixedPath
        self.proto='file'
        self.host='localhost'
        self.port=None
        self.part=None
        self.cgi=None
        self.username=None
        self.password=None
        f=fixedPath.rsplit('/',1)
        self.path=f[0]
        self.resource=''
        if len(f)>0:
            self.resource=f[1]
        self.relative=False

    @property
    def _uncUrlRegex(self):
        """
        Create a regular expression for parsing urls
        """
        regex=r"""(?P<uncUrl>(?P<proto>file):/{4}(?P<host>[^/]+)(/(?P<path>.*))?)"""
        return re.compile(regex)
    def _assignUncUrl(self,uncUrl,proto,host,path=''):
        self.filePath=uncUrl[7:].replace('/','\\')
        self.url=uncUrl
        self.proto=proto
        self.username=None
        self.password=None
        f=path.rsplit('\\',1)
        self.path=f[0]
        self.resource=''
        if len(f)>1:
            self.resource=f[-1]
        self.host=host
        self.port=None
        self.part=None
        self.cgi=None
        self.relative=False

    @property
    def _fileUrlRegex(self):
        """
        Create a regular expression for parsing file:// urls
        """
        proto=r"""((?P<proto>file)://)"""
        login=r"""((?P<username>[-a-z0-9_.]*)?(:(?P<password>[-a-z0-9_]*))?@)"""
        resource=r"""(?P<fullPath>((?P<path>[-a-z0-9_./\\]*?)(?P<resource>[/\\][-a-z0-9_.])?))"""
        regex=r"""(?P<fileUrl>"""+proto+login+r"""?"""+resource+r"""?)"""
        return re.compile(regex,re.IGNORECASE)
    def _assignFileUrl(self,fileUrl,fullPath,proto='file',username=None,password=None,path='',resource=''):
        if os.sep!='/':
            fullPath=fullPath.replace('/',os.sep)
        self.filePath=fullPath
        self.url=fileUrl
        self.proto=proto
        self.username=username
        self.password=password
        self.path=path
        self.resource=resource
        self.host='localhost'
        self.port=None
        self.part=None
        self.cgi.clear()
        self.relative=False

    def _assignOther(self,other):
        self.host=None
        self.port=None
        self.part=None
        self.cgi.clear()
        filePath=other
        standardPath=other
        if os.sep!='/':
            filePath=filePath.replace('/',os.sep)
            standardPath=filePath.replace(os.sep,'/')
        self.filePath=filePath
        self.url=None
        self.proto=None
        self.username=None
        self.password=None
        f=standardPath.rsplit('/',1)
        self.path=f[0]
        self.resource=''
        if len(f)>1:
            self.resource=f[-1]
        self.relative=True

    @property
    def _regexes(self):
        global _URL_REGEXES
        if _URL_REGEXES is None:
            q=(
                self._uncRegex,
                self._dosFilePathRegex,
                self._uncUrlRegex,
                self._fileUrlRegex,
                self._urlRegex,
                )
            #master_regex=re.compile('|'.join([qq.pattern for qq in q]),re.IGNORECASE)
            _URL_REGEXES=q#list([master_regex])
        return _URL_REGEXES

    def assign(self,s:str)->None:
        """
        Assign the value of this object
        """
        kinds:typing.List[typing.Tuple[str,typing.Callable]]=[ # (kindName, typeAssign())
            ('dosFilePath',self._assignDosFilePath),
            ('uncPath',self._assignUncPath),
            ('uncUrl',self._assignUncUrl),
            ('fileUrl',self._assignFileUrl),
            ('url',self._assignUrl)]
        vals={'other':s}
        assign:typing.Callable=self._assignOther
        for regex in self._regexes:
            m=regex.match(s)
            if m is None:
                continue
            gd=m.groupdict()
            for kind,assigner in kinds:
                if kind in gd:
                    vals={}
                    for k,v in gd.items():
                        if v is not None:
                            vals[k]=v
                    assign=assigner
                    break
        assign(**vals)

    def printMembers(self,indent='\t'):
        """
        print values of the individual members to stdout
        """
        for k,v in self.__dict__.items():
            print(f'{indent}{k} = {v}')

# -----

def validate():
    """
    Test validation on a known series
    of valid urls/filenames
    """
    tests=[
        r"c:\windows\thing",
        r"c:/windows/thing",
        r"\\shareddrive\thing",
        r"file://c:\windows\thing",
        r"file://c|\windows\thing",
        r"file:///c:\windows\thing",
        r"file:////shareddrive/thing",
        r"/usr/bin/something",
        r"http://fooblatz.com",
        r"http://sub.domain.0.fooblatz.com",
        r"http://www.fooblatz.com",
        r"http://www.fooblatz.com/path/to/resource",
        r"http://www.fooblatz.com/path/to/",
        r"http://www.fooblatz.com/webabb?q=semprini",
        r"http://www.fooblatz.com/bigthing#4000",
        r"mailto:bob@fooblatz.com",
        r"ftp://kenny:1234@www.fooblatz.com",
        r"ftp://kenny:1234@www.fooblatz.com:22",
        r"autoexec.bat",
        ]
    for t in tests:
        print(t)
        u=UrlNew(t)
        u.printMembers()

def speedcompare():
    """
    test to compare the speeds of runUnitTestsOn()
    """
    from paths import Url
    class S:
        """ test class """
        def __init__(self,s:str):
            self.s=''
            self.assign(s)
        def assign(self,s:str):
            """ value assignement """
            self.s=s
    tests=[
        r"c:\windows\thing",
        r"c:/windows/thing",
        #r"\\shareddrive\thing",
        r"file://c:\windows\thing",
        r"file://c|\windows\thing",
        r"file:///c:\windows\thing",
        r"file:////shareddrive/thing",
        r"/usr/bin/something",
        r"http://fooblatz.com",
        r"http://sub.domain.0.fooblatz.com",
        r"http://www.fooblatz.com",
        r"http://www.fooblatz.com/path/to/resource",
        r"http://www.fooblatz.com/path/to/",
        r"http://www.fooblatz.com/webabb?q=semprini",
        r"http://www.fooblatz.com/bigthing#4000",
        r"mailto:bob@fooblatz.com",
        r"ftp://kenny:1234@www.fooblatz.com",
        r"ftp://kenny:1234@www.fooblatz.com:22",
        #r"autoexec.bat",
        ]
    def runTestsOn(cls):
        for _ in range(1000):
            for u in tests:
                _=cls(u)

        print('DONE')
    _=UrlNew('')
    _=Url('http://www.fooblatz.com')
    def rt1():
        runTestsOn(Url)
    def rt2():
        runTestsOn(UrlNew)
    def rt3():
        runTestsOn(S)
    t1=timeit(rt1,number=1)
    t2=timeit(rt2,number=1)
    t3=timeit(rt3,number=1)
    print(t1,t2,t3)


if __name__=='__main__':
    # speedcompare()
    validate()
