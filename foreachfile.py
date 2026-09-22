"""
A tool that runs a program on every file that matches a given set of criteria

This is very useful for command lines.
"""
import typing
from pathlib import Path
import k_runner
from k_runner import OsRunResult,argvToString
from .search import findFiles,MatchType,osIsCaseSensitive


def forEachFile(
    cmd:typing.Union[str,typing.Iterable[str]],
    files:typing.Union[
        Path,str,
        typing.Iterable[typing.Union[Path,str]]]='.',
    shell:bool=True,
    environment:typing.Union[None,typing.Dict[str,str]]=None,
    )->typing.Generator[OsRunResult,None,None]:
    """
    Run a shell command for each file in a list of files.

    NOTE: To simultaneaously search for files and
    run something on them you can instead try:
        forEachFoundFile()
    """
    if isinstance(files,(str,Path)):
        files=(files,)
    for file in files:
        def fileFix(
            s:typing.Union[str,Path],
            file:typing.Union[str,Path]
            )->str:
            """
            Replace every instance of $FILE, %FILE%, {FILE} ${FILE}
            in the given string
            """
            s=str(s)
            for replacement in ('$FILE','%FILE%','{FILE}','${FILE}'):
                s=s.replace(replacement,str(file))
            return s
        if isinstance(cmd,str):
            newCmd=fileFix(cmd,file)
        else:
            newCmd=[fileFix(c,file) for c in cmd]
        yield k_runner.run(newCmd,shell,env=environment)


def forEachFoundFile(
    cmd:typing.Union[str,typing.Iterable[str]],
    match:typing.Union[None,str,typing.Pattern[str]]=None,
    matchType:MatchType=MatchType.SimpleStringMatch,
    extensions:typing.Union[None,str,typing.Iterable[str]]=None,
    startDirs:typing.Union[
        Path,str,
        typing.Iterable[typing.Union[Path,str]]]='.',
    recursive:bool=True,
    depthFirst:bool=False,
    caseSensitive:bool=osIsCaseSensitive,
    shell:bool=True,
    environment:typing.Union[None,typing.Dict[str,str]]=None,
    )->typing.Generator[OsRunResult,None,None]:
    """
    A tool that runs a program on every file that matches
    a given set of criteria

    This is very useful for command lines.
    """
    for file in findFiles(
        match,matchType,extensions,startDirs,
        recursive,depthFirst,caseSensitive):
        #
        yield from forEachFile(cmd,file,shell,environment)


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    import time
    from stringTools import ANSI_COLORS
    printHelp=False
    match=""
    recursive=False
    matchType=MatchType.GlobMatch
    extensions:typing.List[str]=[]
    caseSensitive:bool=osIsCaseSensitive
    startDirs:typing.List[str]=[]
    environment:typing.Dict[str,str]={}
    depthFirst:bool=False
    shell=True
    cmd:typing.List[str]=[]
    buildingCommand=False
    for arg in args:
        if buildingCommand:
            cmd.append(arg)
        elif arg.startswith('-'):
            kw=arg.split('=',1)
            k=kw[0].lower()
            if k in ('-h','--help'):
                printHelp=True
            elif k.startswith('--ext') and len(kw)>1:
                parts=kw[1].replace(';',',').split(',')
                extensions.extend([s.strip() for s in parts])
            elif k.startswith('--env') and len(kw)>1:
                for s in kw[1].split(','):
                    colonLocation=s.find(':')
                    equalsLocation=s.find('=')
                    if colonLocation<0:
                        if equalsLocation<0:
                            print(f'Invalid environment variable "{s}"')
                        splitLocation=equalsLocation
                    elif equalsLocation<0 or colonLocation>equalsLocation:
                        splitLocation=colonLocation
                    else:
                        splitLocation=equalsLocation
                    environment[s[0:splitLocation].strip()]=\
                        s[splitLocation+1:].strip()
            elif k in ('--case','--casesensitive'):
                if len(kw)>1 and kw[1]:
                    caseSensitive=kw[1][0].lower() in ('y','t','1')
                else:
                    caseSensitive=True
            elif k in ('-r','--r'):
                if len(kw)>1 and kw[1]:
                    recursive=kw[1][0].lower() in ('y','t','1')
                else:
                    recursive=True
            elif k=='--shell':
                if len(kw)>1 and kw[1]:
                    shell=kw[1][0].lower() in ('y','t','1')
                else:
                    shell=True
            elif k in ('--re','--regex'):
                matchType=MatchType.PythonRegexMatch
            elif k in ('--depth','--depthfirst','--deapth','--deapthfirst'):
                if len(kw)>1 and kw[1]:
                    depthFirst=kw[1][0].lower() in ('y','t','1')
                else:
                    depthFirst=True
        else:
            if arg.lower()=='do':
                buildingCommand=True
            else:
                if match:
                    startDirs.append(match)
                match=arg
    if printHelp:
        print("USAGE: foreachfile.py [flags] [in_dir ...] [match] do [cmd $FILE]") # noqa: E501
        print("  where everything after \"do\" is the command to run on each file") # noqa: E501
        print("  each file can be specified with common replacement strategies like:") # noqa: E501
        print(r"    $FILE ${FILE} %FILE%")
        print("FLAGS:")
        print("  -h ................. print this help")
        print("  --help ............. print this help")
        print("  -r[=y/n] ........... recursive")
        print("  --re[gex] .......... match by regex")
        print("  --depth[first][=y/n] ....... perform depth-first search")
        print("  --ext[ension[s]]=e1,e2,e3 .. match by extensions")
        print("  --case[sensitive][=y/n] .... match case sensitivity")
        print("  --shell[=y/n] .............. use command shell")
        print("            (setting to \"no\" can speed thing up slightly)")
        print("  --env[iron[ment]]=[k:v, ...] .. specify shell environment variables") # noqa: E501
        print("            (each k:v can be separated by : or =)")
        print("EXAMPLE:")
        print('  foreachfile --ext=jpg,jpeg "~/my pictures" "" do gimp $FILE')
        return 1
    if not cmd:
        # if there is nothing to do, simply print the found file names
        for f in findFiles(match,matchType,extensions,
            startDirs,recursive,depthFirst,caseSensitive):
            print(f'{ANSI_COLORS.ANSI_CYAN.value}{f.absolute()}{ANSI_COLORS.ANSI_OFF.value}') # pylint: disable=line-too-long # noqa: E501
    else:
        for runResult in forEachFoundFile(cmd,
            match,matchType,extensions,startDirs,recursive,
            depthFirst,caseSensitive,shell,environment):
            print(f'{ANSI_COLORS.ANSI_CYAN.value}{argvToString(cmd)}{ANSI_COLORS.ANSI_OFF.value}') # pylint: disable=line-too-long # noqa: E501
            if not runResult.finished:
                print(f'{ANSI_COLORS.ANSI_DARK_YELLOW.value}WAITING...{ANSI_COLORS.ANSI_OFF.value}') #pylint: disable=line-too-long # noqa: E501
                while not runResult.finished:
                    time.sleep(50)
            if runResult.failed:
                print(f'{ANSI_COLORS.ANSI_DARK_RED.value}{runResult.stdOutErr}{ANSI_COLORS.ANSI_OFF.value}') # pylint: disable=line-too-long # noqa: E501
            else:
                print(runResult.stdOutErr)
    return 0


if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))
