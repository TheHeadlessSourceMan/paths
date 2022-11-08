"""
Decipher software version numbers so they can be compared.

NOTE: handles:
    versions - "1.0"
    indefinite sub-versions - "1.0.3.7.21.8"
    alpha/beta/etc releases - "1.0a", "1.0 beta 3"
    release candidates - "1.0 rc 3"
    underscored formats - "Version_1_0"
    formats starting with "v"/"ver"/"version" - "Version_1_0" "v1.0"
    Mooshed-together text parts "1.0rc3"
"""
from itertools import zip_longest
import typing
import re


VersionCompatible=typing.Union[str,float,"Version"]
_VersionSegmentRe=re.compile(r"""\d+|([a-z]+(_[a-z]+)*)""",re.IGNORECASE)
class Version:
    """
    Decipher software version numbers so they can be compared.

    Note that:
        Version("1.0")==Version("1.0.5")
    but
        Version("1.0.0")!=Version("1.0.5")
    This design was chosen so you can determine if a version is in the 1.0 branch.

    NOTE: handles:
        versions - "1.0"
        indefinite sub-versions - "1.0.3.7.21.8"
        alpha/beta/etc releases - "1.0a", "1.0 beta 3"
        release candidates - "1.0 rc 3"
        underscored formats - "Version_1_0"
        formats starting with "v"/"ver"/"version" - "Version_1_0" "v1.0"
        Mooshed-together text parts "1.0rc3"
    """

    def __init__(self,
        value:typing.Optional[VersionCompatible],
        experimental:typing.Optional[bool]=None):
        """ """
        self._segments:typing.List[typing.Union[str,int]]=[]
        self.experimental=False
        if value is not None:
            self.assign(value,experimental)

    def assign(self,
        value:VersionCompatible,
        experimental:typing.Optional[bool]=None):
        """ """
        if isinstance(value,Version):
            self._segments=value._segments
            self.experimental=value.experimental
        else:
            self._segments=[]
            self.experimental=False
            for m in _VersionSegmentRe.finditer(str(value)):
                segment=str(m.group(0)).lower()
                if not self._segments and segment[0]=='v':
                    # chop off strings starting with "Version", "ver", "v"
                    continue
                try:
                    iseg=int(segment)
                    self._segments.append(iseg)
                except ValueError:
                    self.experimental=True
                    self._segments.append(segment)
        if experimental is not None:
            self.experimental=experimental

    @property
    def release(self)->bool:
        return not self.experimental
    @property
    def preRelease(self)->bool:
        return self.experimental
    @property
    def releaseCandidate(self)->bool:
        for seg in self._segments:
            if seg=='rc':
                return True
        return False
    @property
    def alpha(self)->bool:
        for seg in self._segments:
            if seg in ('a','alpha'):
                return True
        return False
    @property
    def beta(self)->bool:
        for seg in self._segments:
            if seg in ('b','beta'):
                return True
        return False

    def __seg_score__(self,seg:typing.Union[int,str])->float:
        """
        scores an int segment as its value, pro-rates a text value as a partial float
        """
        if isinstance(seg,int):
            return seg
        if seg[0]=='r': # release candidate
            return -0.1
        elif seg[0]=='b': # beta release
            return -0.5
        elif seg[0]=='a': # alpha release
            return -0.75
        return -0.9 # unknown

    def __seg_cmp__(self,seg1:typing.Union[int,str],seg2:typing.Union[int,str])->float:
        """
        scores two aligned version segments against eachother

        can be negative if seg1<seg2
        can be decimal for text segments
        """
        if seg1==seg2:
            ret=0.0
        else:
            ret=self.__seg_score__(seg1)-self.__seg_score__(seg2)
        #print(f'segcmp {seg1}<->{seg2} = {ret}')
        return ret

    def __add__(self,other:VersionCompatible)->"Version":
        """
        This is usuful for indexing to the next version number
        Eg:
            Version("1.2.36.0")+"0.0.1.0"
        """
        other=asVersion(other)
        ret=Version(None)
        for us,them in zip(self._segments,other._segments):
            if isinstance(us,str) or isinstance(them,str):
                ret._segments.append(them)
            else:
                ret._segments.append(us+them)
        return ret

    def __eq__(self,other:typing.Any)->bool:
        """
        Notice that "7.2.1"=="7.2" is True
            but "7.2.1"<="7.2" is False
        """
        if not isinstance(other,(str,Version,float)):
            return False
        other=asVersion(other)
        for us,them in zip(self._segments,other._segments):
            if us!=them:
                return False
        return True

    def __lt__(self,other:typing.Any)->bool:
        if not isinstance(other,(str,Version,float)):
            return False
        other=asVersion(other)
        #print("lt",self._segments,other._segments)
        for us,them in zip_longest(self._segments,other._segments,fillvalue=0):
            if us==them:
                continue
            if self.__seg_cmp__(us,them)<0:
                return True
            break
        return False

    def __gt_redundant_function__(self,other:typing.Any)->bool:
        if not isinstance(other,(str,Version,float)):
            return False
        other=asVersion(other)
        for us,them in zip_longest(self._segments,other._segments,fillvalue=0):
            if us==them:
                continue
            if self.__seg_cmp__(us,them)>0:
                return True
        return False

    def __le__(self,other:typing.Any)->bool:
        if not isinstance(other,(str,Version,float)):
            return False
        other=asVersion(other)
        for us,them in zip_longest(self._segments,other._segments,fillvalue=0):
            if self.__seg_cmp__(us,them)<=0:
                return True
        return False

    def __repr__(self):
        """
        Joins int segments with '.' and int-text or text-text segmens with ' '
        """
        ret=[]
        lastWasInt=True
        for seg in self._segments:
            if isinstance(seg,int):
                if ret:
                    if lastWasInt:
                        ret.append('.')
                    else:
                        ret.append(' ')
                ret.append(str(seg))
                lastWasInt=True
            else:
                if ret:
                    ret.append(' ')
                ret.append(seg)
                lastWasInt=False
        return ''.join(ret)

def asVersion(ver:VersionCompatible)->Version:
    """
    Always return ver as a version.

    If it is already one, simply return.
    Otherwise, convert it.
    """
    if isinstance(ver,Version):
        return ver
    return Version(ver)



class VersioningScheme:
    r"""
    The rules used for creating/interpreting version numbers.

    It is based on like your time formatting pattern or whatever.
        %R - release version
        %P - pre-release version
        %E - even denotes release version
        %O - odd denotes release version
        %a - one-letter alpha/beta
        %A - fully spelled out 'alpha'/'beta'
        %r - 'rc' number
    Example:
        "%R.%R.%R pre%P"

    TODO: not yet implemented!
    """
    def __init__(self):
        self.pattern='R.R.R.P'