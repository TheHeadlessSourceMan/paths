"""
Tools to search paths
"""
import typing
from pathlib import Path


def findFilenamesOfType(
    extensions:typing.Union[None,str,typing.Iterable[str]]=None,
    startDirs:typing.Union[
        Path,str,
        typing.Iterable[typing.Union[Path,str]]]='.',
    recursive:bool=True
    )->typing.Generator[Path,None,None]:
    """
    Depth-first file search.

    Yields only files, never directories.

    :startDirs: one or more directories to start searching at
        if not specified, use working directory
    :extensions: limit results to one or more extensions
        (extensions must include the dot, for instance [".c",".cpp"])
    :recursive: default=true
    """
    tape:typing.List[Path]
    if isinstance(startDirs,Path):
        tape=[startDirs]
    elif isinstance(startDirs,str):
        tape=[Path(startDirs)]
    else:
        tape=[Path(startDir) for startDir in startDirs]
    if not startDirs.is_dir():
        return
    if isinstance(extensions,str):
        extensions=(extensions,)
    for currentDir in tape:
        for filename in currentDir.iterdir():
            if filename.is_dir():
                if recursive:
                    tape.append(filename) # noqa: E501 # pylint: disable=modified-iterating-list
            elif extensions is None or filename.suffix in extensions:
                yield filename
