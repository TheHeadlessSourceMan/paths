#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
Run unit tests

See:
    http://pyunit.sourceforge.net/pyunit.html
"""
import unittest
import os
import paths
from paths import URL, asUrl, MalformedURL


def assertMember(obj,valname,expected):
    """
    Utility to assert that a member is what we expect
    """
    result=getattr(obj,valname)
    if result!=expected:
        raise Exception('%s="%s" NOT "%s"'%(valname,result,expected))


def hr(s):
    """
    Print a horizontal rule
    """
    print('------- %s -------'%s)


__HERE__=os.path.abspath(__file__).rsplit(os.sep,1)[0]+os.sep


class Test(unittest.TestCase): # pylint: disable=no-member
    """
    Run unit test
    """

    def setUp(self):
        """
        Set up the test case
        """

    def tearDown(self):
        """
        Tear down the test case
        """

    def testWebUrl(self):
        """
        Test normal http urls
        """
        path=r"http://www.fooblatz.com/the/path/file.php?name=val"
        hr(path)
        u=URL(path)
        assertMember(u,'protocol','http')
        assertMember(u,'host','www.fooblatz.com')
        assertMember(u,'domain','fooblatz.com')
        assertMember(u,'subdomain','www')
        assertMember(u,'port',None)
        assertMember(u,'path','the/path')
        assertMember(u,'resource','file.php')
        assertMember(u,'fullPath','the/path/file.php')
        assertMember(u,'filePath',None)
        assert len(u)==1
        assert u['name']=='val'
        assert u['semprini'] is None
        u['semprini']=5
        assert u['semprini']=='5'
        del u['name']
        assert u.url==r"http://www.fooblatz.com/the/path/file.php?semprini=5"
        del u['semprini']
        u.subdomain='www1'
        assert u.url==r"http://www1.fooblatz.com/the/path/file.php"
        u.domain='grabbley.nz'
        assert u.url==r"http://www1.grabbley.nz/the/path/file.php"
        u.password='secret'
        assert u.url==r"http://www1.grabbley.nz/the/path/file.php"
        u.username='username'
        assert u.url==\
            r"http://username:secret@www1.grabbley.nz/the/path/file.php"
        u.user='user'
        assert u.url==r"http://user:secret@www1.grabbley.nz/the/path/file.php"
        assert u.username==u.user
        u.password=None
        assert u.url==r"http://user@www1.grabbley.nz/the/path/file.php"
        u.host='www.fooblatz.com'
        assert u.url==r"http://user@www.fooblatz.com/the/path/file.php"
        u.host='fooblatz.com'
        assert u.url==r"http://user@fooblatz.com/the/path/file.php"
        assert u.url==u.name
        print('OK')

    def testIpUrl(self):
        """
        Test urls with ip addresses
        """
        path=r"ftp://ralph:secret@192.168.1.47:400"
        hr(path)
        u=URL(path)
        assertMember(u,'protocol','ftp')
        assertMember(u,'username','ralph')
        assertMember(u,'password','secret')
        assertMember(u,'host','192.168.1.47')
        assertMember(u,'domain','192.168.1.47')
        assertMember(u,'subdomain',None)
        assertMember(u,'port',400)
        assertMember(u,'resource',None)
        assertMember(u,'fullPath',None)
        assertMember(u,'filePath',None)
        assert u['semprini'] is None
        assert u.name==u.url
        print('OK')

    def testFilenameRoundtrip(self):
        """
        Round-trip test of a filename

        test won't work on nonwindows
        """
        path=r'c:/the/path/file.txt'
        hr(path)
        u=URL(path)
        assertMember(u,'url','file:///%s'%path)
        if os.name=='nt':
            # test won't work on nonwindows
            path2=r'c:\the\path\file.txt'
            u2=URL(path2)
            if u!=u2:
                print("ERR ERR ERR:\n%s\n  !=\n%s"%(u.url,u2.url))
                assert False
            assertMember(u2,'url','file:///%s'%path)
            assertMember(u,'filePath',path2)
            assertMember(u2,'filePath',path2)
        else:
            assertMember(u,'filePath',path)
        print('OK')

    def testUrlToFile(self):
        """
        Test conversion of url to filename
        """
        if os.name=='nt':
            # test won't work on nonwindows
            url='file://c:/the/path/file.txt'
            hr(url)
            u=URL(url)
            #TODO: fix this bug!
            #assertMember(u,'dirPath',path.rsplit('\\',1)[0].replace('\\','/'))
            assertMember(u,'host','localhost')
            assertMember(u,'domain','localhost')
            assertMember(u,'subdomain',None)
            assertMember(u,'port',None)
            assertMember(u,'protocol','file')
            assertMember(u,'path','c:/the/path')
            assertMember(u,'resource','file.txt')
            assertMember(u,'fullPath','c:/the/path/file.txt')
            #assertMember(u,'filePath',path)
            u.assign(None,None) # same as u.clear()
            assert u.scheme is None
            assert u.auth is None
            assert u.host is None
            assert u.port is None
            assert u.path is None
            assert len(u.cgi)==0
            assert u.fragment is None
            print('OK')
        else:
            print('WARN: skipping tests for windows files')

    def testUrlToFilePipeChar(self):
        """
        Test conversion of url to file with pipe character
        """
        if os.name=='nt':
            # test won't work on nonwindows
            url='file://c|/the/path/file.txt'
            hr(url)
            u=URL(url)
            #TODO: fix this bug!
            #assertMember(u,'dirPath',path.rsplit('\\',1)[0].replace('\\','/'))
            assertMember(u,'host','localhost')
            assertMember(u,'domain','localhost')
            assertMember(u,'subdomain',None)
            assertMember(u,'port',None)
            assertMember(u,'protocol','file')
            assertMember(u,'path','c:/the/path')
            assertMember(u,'resource','file.txt')
            assertMember(u,'fullPath','c:/the/path/file.txt')
            #assertMember(u,'filePath',path)
            u.assign(None,None) # same as u.clear()
            assert u.scheme is None
            assert u.auth is None
            assert u.host is None
            assert u.port is None
            assert u.path is None
            assert len(u.cgi)==0
            assert u.fragment is None
            print('OK')
        else:
            print('WARN: skipping tests for windows files')

    def testFileToUrl(self):
        """
        Test conversion of a filename to a url
        """
        if os.name=='nt':
            # test won't work on nonwindows
            path=r'c:\the\path\file.txt'
            hr(path)
            u=URL(path)
            #TODO: fix this bug!
            #assertMember(u,'dirPath',path.rsplit('\\',1)[0].replace('\\','/'))
            assertMember(u,'host','localhost')
            assertMember(u,'domain','localhost')
            assertMember(u,'subdomain',None)
            assertMember(u,'port',None)
            assertMember(u,'protocol','file')
            assertMember(u,'path','c:/the/path')
            assertMember(u,'resource','file.txt')
            assertMember(u,'fullPath','c:/the/path/file.txt')
            assertMember(u,'filePath',path)
            u.assign(None,None) # same as u.clear()
            assert u.scheme is None
            assert u.auth is None
            assert u.host is None
            assert u.port is None
            assert u.path is None
            assert len(u.cgi)==0
            assert u.fragment is None
            print('OK')
        else:
            print('WARN: skipping tests for windows files')

    def relativeFileUrl(self):
        """
        Test relative filenames working with urls
        """
        if os.name=='nt':
            # test won't work on nonwindows
            path=r'.\\test.py'
            shouldBe=os.path.curdir.replace(os.sep,'/')
            hr(path)
            u=URL('relativeFileUrl %s'%path)
            assertMember(u,'host',None)
            assertMember(u,'domain',None)
            assertMember(u,'subdomain',None)
            assertMember(u,'port',None)
            assertMember(u,'protocol','file')
            assertMember(u,'path',shouldBe)
            assertMember(u,'resource','test.py')
            assertMember(u,'fullPath',shouldBe+'/test.py')
            assertMember(u,'filePath',os.path.curdir+os.sep+'test.py')
            print('OK')
        else:
            print('WARN: skipping tests for windows files')

    def rootFileUrl(self):
        """
        Test root file path functionality
        """
        if os.name=='nt':
            # test won't work on nonwindows
            path=None
            hr(str(path))
            u=URL(path)
            assertMember(u,'host',None)
            assertMember(u,'domain',None)
            assertMember(u,'subdomain',None)
            assertMember(u,'port',None)
            assertMember(u,'protocol',None)
            assertMember(u,'path',None)
            assertMember(u,'resource',None)
            assertMember(u,'fullPath',None)
            path='.'
            hr(str(path))
            u=URL(path)
            assertMember(u,'host',None)
            assertMember(u,'domain',None)
            assertMember(u,'subdomain',None)
            assertMember(u,'port',None)
            assertMember(u,'protocol',None)
            assertMember(u,'path',None)
            assertMember(u,'resource',None)
            assertMember(u,'fullPath',None)
            print('OK')
        else:
            print('WARN: skipping tests for windows files')

    def windowsDriveUrl(self):
        """
        Test windows drive letter functionality
        """
        if os.name=='nt':
            # test won't work on nonwindows
            path='c:\\'
            hr(str(path))
            u=URL(path)
            assertMember(u,'host',None)
            assertMember(u,'domain',None)
            assertMember(u,'subdomain',None)
            assertMember(u,'port',None)
            assertMember(u,'protocol','file')
            assertMember(u,'path','c:')
            assertMember(u,'resource',None)
            assertMember(u,'fullPath','c:/')
            assertMember(u,'filePath','c:\\')
            print('OK')
        else:
            print('WARN: skipping tests for windows files')

    def compareUrls(self):
        """
        Test comparing of two different urls
        """
        u=asUrl("http://www.zambizi.com/fish/trout.htm")
        u2=u.copy()
        assert u.url==u2.url
        assert u==u2
        u2.subdomain=None
        assert not u.url==u2.url
        assert not u==u2
        assert u.sameDomain(u2)
        u2.host="www.google.com"
        assert not u.url==u2.url
        assert not u==u2
        assert not u.sameDomain(u2)

    def testCommandLine(self):
        """
        Test the command line functionality
        """
        paths.cmdline(['--help'])
        paths.cmdline([])

    def testReadWrite(self):
        """
        test whether file-like access like url.read() and url.write() will work
        """
        relpath=os.sep.join(['test','testdata.txt'])
        hr('testReadWrite %s'%relpath)
        teststring:str='My word is my passport. Verify me.'
        manualTarget=os.path.abspath(relpath)
        try:
            os.remove(manualTarget)
        except Exception:
            pass
        u=asUrl(manualTarget)
        print(u)
        assertMember(u,'filePath',manualTarget)
        u.write(teststring)
        u.flush()
        u=u.copy()
        u.seek(0)
        print('"%s" + "%s" == "%s"'%(u.read(2),u.read(3),teststring[0:5]))
        print('%s%s\n%s'%(u.read(2),u.read(3),teststring[0:5]))
        assert u.read(2)+u.read(3)==teststring[0:5]
        assert u.tell()==5
        u.seek(0) # reset and read all
        assert u.data==teststring
        u.seek(2,0) # relative to start of file
        assert u.tell()==2
        assert u.read(2)==teststring[11:13]
        u.seek(-4,1) # relative to current pos
        assert u.tell()==4
        assert u.read(2)==teststring[7:9]
        u.seek(-3,2) # relative to end of str
        assert u.tell()==len(teststring)-3
        assert u.read(3)==teststring[-3:]

    def testUncPaths(self):
        """
        test whether windows unc paths work

        see:
            https://foswiki.org/Support/Faq72
            https://bytes.com/topic/python/answers/29322-unc-paths-file-object-open
        """
        url=r"file://///myserver/path/somefile.doc"
        unc=r"\\myserver\path\somefile.doc"
        u=URL(url)
        u2=URL(unc)
        assertMember(u,'url',url)
        assertMember(u2,'url',url)
        assertMember(u2,'filePath',unc)
        assertMember(u,'filePath',unc)

    def testRelativePaths(self):
        """
        test relative paths
        """
        base=r"file://topdir/parentdir/childdir/"
        u=URL(base)
        assertMember(u,'fullPath','topdir/parentdir/childdir/')
        u2=u.relative('childchild/')
        assertMember(u2,'fullPath','topdir/parentdir/childdir/childchild/')
        u2=u.relative('./')
        assertMember(u2,'fullPath','topdir/parentdir/childdir/')
        u2=u.relative('.//.') # more complex ways of going nowhere
        assertMember(u2,'fullPath','topdir/parentdir/childdir/')
        u2=u.relative('../')
        assertMember(u2,'fullPath','topdir/parentdir/')
        u2=u.relative('../../')
        assertMember(u2,'fullPath','topdir/')
        # --- make sure we get an exception if we try to navigate past root
        gotException=False
        try:
            u2=u.relative('../../../')
        except MalformedURL:
            gotException=True
        assert not gotException


def testSuite():
    """
    Combine unit tests into an entire suite
    """
    testSuite = unittest.TestSuite() # pylint: disable=no-member
    testSuite.addTest(Test("testUncPaths"))
    testSuite.addTest(Test("testFilenameRoundtrip"))
    testSuite.addTest(Test("relativeFileUrl"))
    testSuite.addTest(Test("testRelativePaths"))
    testSuite.addTest(Test("windowsDriveUrl"))
    testSuite.addTest(Test("compareUrls"))
    testSuite.addTest(Test("testWebUrl"))
    testSuite.addTest(Test("testFileToUrl"))
    testSuite.addTest(Test("testUrlToFile"))
    testSuite.addTest(Test("testUrlToFilePipeChar"))
    testSuite.addTest(Test("testCommandLine"))
    testSuite.addTest(Test("testIpUrl"))
    testSuite.addTest(Test("testReadWrite"))
    return testSuite


def cmdline(args):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    # Run all the test suites in the standard way.
    unittest.main(args) # pylint: disable=no-member


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
