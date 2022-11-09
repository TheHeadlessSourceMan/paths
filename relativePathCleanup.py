"""
A fairly simple way of cleaning up relative paths
"""
import os
import re

# You should use this like path=PathCleanupRe.sub('/',path+'/')
PathCleanupRe=re.compile(r"""((?<!:)//+)|(/[.]/)|(/[^/]+/[.][.]/)""")

def cleanup(path:str,relativeTo:str)->str:
    """
    A fairly simple way of cleaning up relative paths

    Basically just appends path to relativeTo and then
    skips over:
        //
        /./
        /anything/../

    Accepts urls, windows, and unc filenames.

    Always converts \ to /

    NOTE: if using filesystem paths, you may want to use:
        cleanupOsPath() instead
    """
    path=path.replace('\\','/').strip()
    if path[0]!='/' and path.find(':')!=path.find('/')-1:
        # if it's not root then add relativeTo
        relativeTo=relativeTo.replace('\\','/').strip()
        path=f'{relativeTo}/{path}/'
    path=PathCleanupRe.sub('/',path)
    while path[-1]=='/':
        path=path[0:-1]
    return path

def cleanupOsPath(path:str,relativeTo:str='')->str:
    """
    improves upon cleanup() by:
    1) always returns path with native os separators
    2) expanding environment variables in the path
    3) if relativeTo is not specified, uses current working directory
    """
    if not relativeTo:
        relativeTo=os.path.abspath('.')
    path=cleanup(os.path.expandvars(path),relativeTo)
    if os.sep!='/':
        path=path.replace('/',os.sep)
    return path

if __name__=='__main__':
    import sys
    if len(sys.argv)<2:
        print("Useage: relativePathCleanup path [relativeTo]")
    else:
        relativeTo=''
        path=sys.argv[1]
        if len(sys.argv)>2:
            relativeTo=sys.argv[2]
        result=cleanupOsPath(path,relativeTo)
        print(result)