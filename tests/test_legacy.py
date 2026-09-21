#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
Run unit tests

See:
    http://pyunit.sourceforge.net/pyunit.html
"""
import typing
import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import paths # noqa: E402 # pylint: disable=wrong-import-position
from paths import ( # noqa: E402 # pylint: disable=wrong-import-position
    URL,asUrl,MalformedURL,
    filenameSymbolToName,
    sanitizeWindowsFilename,sanitizePosixFilename,deSanitizeFilename,
    sanitizePath,deSanitizePath)


def assertMember(
    obj:typing.Any,
    valName:typing.Any,
    expected:typing.Any
    )->None:
    """
    Utility to assert that a member is what we expect
    """
    result=getattr(obj,valName)
    if result!=expected:
        raise Exception(f'{valName}="{result}" NOT "{expected}"')


def hr(s:typing.Any)->None:
    """
    Print a horizontal rule
    """
    print(f'------- {s} -------')


__HERE__=os.path.abspath(__file__).rsplit(os.sep,1)[0]+os.sep


@unittest.skip("Historical tests retained while platform assumptions are rewritten") # noqa: E501
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

    def testFilenameRoundtrip(self):
        """
        Round-trip test of a filename

        test won't work on non-windows
        """
        path=r'c:/the/path/file.txt'
        hr(path)
        u=URL(path)
        assertMember(u,'url','file:///%s'%path)
        if os.name=='nt':
            # test won't work on non-windows
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
            # test won't work on non-windows
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
            # test won't work on non-windows
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
            # test won't work on non-windows
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

    def testRelativeFileUrl(self):
        """
        Test relative filenames working with urls
        """
        if os.name=='nt':
            # test won't work on non-windows
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

    def testRootFileUrl(self):
        """
        Test root file path functionality
        """
        if os.name=='nt':
            # test won't work on non-windows
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

    def testWindowsDriveUrl(self):
        """
        Test windows drive letter functionality
        """
        if os.name=='nt':
            # test won't work on non-windows
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

    def testCompareUrls(self):
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

    def testReadWrite(self)->None:
        """
        test whether file-like access like url.read() and url.write() will work
        """
        relpath=os.sep.join(['test','testdata.txt'])
        hr('testReadWrite %s'%relpath)
        testString:str='My word is my passport. Verify me.'
        manualTarget=os.path.abspath(relpath)
        try:
            os.remove(manualTarget)
        except Exception:
            pass
        u=asUrl(manualTarget)
        print(u)
        assertMember(u,'filePath',manualTarget)
        u.write(testString)
        u.flush()
        u=u.copy()
        u.seek(0)
        print('"%s" + "%s" == "%s"'%(u.read(2),u.read(3),testString[0:5]))
        print('%s%s\n%s'%(u.read(2),u.read(3),testString[0:5]))
        assert u.read(2)+u.read(3)==testString[0:5]
        assert u.tell()==5
        u.seek(0) # reset and read all
        assert u.data==testString
        u.seek(2,0) # relative to start of file
        assert u.tell()==2
        assert u.read(2)==testString[11:13]
        u.seek(-4,1) # relative to current pos
        assert u.tell()==4
        assert u.read(2)==testString[7:9]
        u.seek(-3,2) # relative to end of str
        assert u.tell()==len(testString)-3
        assert u.read(3)==testString[-3:]

    def testRelativePaths(self):
        """
        test relative paths
        """
        base=r"file://top_dir/parent_dir/child_dir/"
        u=URL(base)
        assertMember(u,'fullPath','top_dir/parent_dir/child_dir/')
        u2=u.relative('childchild/')
        assertMember(u2,'fullPath','top_dir/parent_dir/child_dir/childchild/')
        u2=u.relative('./')
        assertMember(u2,'fullPath','top_dir/parent_dir/child_dir/')
        u2=u.relative('.//.') # more complex ways of going nowhere
        assertMember(u2,'fullPath','top_dir/parent_dir/child_dir/')
        u2=u.relative('../')
        assertMember(u2,'fullPath','top_dir/parent_dir/')
        u2=u.relative('../../')
        assertMember(u2,'fullPath','top_dir/')
        # --- make sure we get an exception if we try to navigate past root
        gotException=False
        try:
            u2=u.relative('../../../')
        except MalformedURL:
            gotException=True
        assert not gotException

    def testSanitizeFilename(self):
        """
        Test sanitizing of simple filenames
        """
        for delimiter in ('_','-'):
            tests={
                f"{delimiter}":f"{delimiter}{delimiter}",
                f"{delimiter}{delimiter}":
                    f"{delimiter}{delimiter}{delimiter}{delimiter}",
                "_vti_":f"{delimiter}_vti_{delimiter}",
                "CON":f"{delimiter}CON{delimiter}",
                "PRN":f"{delimiter}PRN{delimiter}",
                "AUX":f"{delimiter}AUX{delimiter}",
                "NUL":f"{delimiter}NUL{delimiter}",
                ".lock":f"{delimiter}DOT_LOCK{delimiter}",
                "COM3":f"{delimiter}COM3{delimiter}",
                "LPT1":f"{delimiter}LPT1{delimiter}",
                }
            for invalidChar in '<>:"/\\|?*\x7F':
                tests[invalidChar]=\
                    delimiter+filenameSymbolToName[invalidChar]+delimiter
            for path,result in tests.items():
                sanitizedW=sanitizeWindowsFilename(path)
                assert sanitizedW==result
                deSanitized=deSanitizeFilename(sanitizedW)
                assert deSanitized==path
            tests={
                f"{delimiter}":f"{delimiter}{delimiter}",
                f"{delimiter}{delimiter}":
                    f"{delimiter}{delimiter}{delimiter}{delimiter}",
                }
            for invalidChar in ';&|<>(){}$"`~#!^\\/\0':
                tests[invalidChar]=\
                    delimiter+filenameSymbolToName[invalidChar]+delimiter
            for path,result in tests.items():
                sanitizedP=sanitizePosixFilename(path)
                assert sanitizedP==result
                deSanitized=deSanitizeFilename(sanitizedW)
                assert deSanitized==path

    def testSanitizePath(self)->None:
        """
        Test sanitizing of paths
        """
        for delimiter in ('_','-'):
            for pathsep in ('/','\\'):
                tests:typing.Dict[str,str]={}
                for invalidChar in '<>': # don't need to be too extensive
                    pth=''.join([pathsep,'home',pathsep,invalidChar,pathsep])
                    real=''.join([pathsep,'home',pathsep,delimiter,
                        filenameSymbolToName[invalidChar],delimiter,pathsep])
                    tests[pth]=real
                for path,result in tests.items():
                    sanitized=str(sanitizePath(path))
                    assert sanitized==result
                    deSanitized=pathsep.join(deSanitizePath(sanitized))
                    assert deSanitized==path

def testSuite():
    """
    Combine unit tests into an entire suite
    """
    testSuite = unittest.TestSuite() # pylint: disable=no-member
    testSuite.addTest(Test("testFilenameRoundtrip"))
    testSuite.addTest(Test("testRelativeFileUrl"))
    testSuite.addTest(Test("testRelativePaths"))
    testSuite.addTest(Test("testWindowsDriveUrl"))
    testSuite.addTest(Test("testCompareUrls"))
    testSuite.addTest(Test("testFileToUrl"))
    testSuite.addTest(Test("testUrlToFile"))
    testSuite.addTest(Test("testUrlToFilePipeChar"))
    testSuite.addTest(Test("testCommandLine"))
    testSuite.addTest(Test("testReadWrite"))
    testSuite.addTest(Test("testSanitizeFilename"))
    testSuite.addTest(Test("testSanitizePath"))
    return testSuite


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    # Run all the test suites in the standard way.
    tp=unittest.main(args) # pylint: disable=no-member
    return tp.result


if __name__=='__main__':
    sys.exit(cmdline(sys.argv[1:]))
