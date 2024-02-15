"""
Wrapper around a MAC address string that allows you to do useful
things like formatting, etc.

TODO: move into networkTools
"""
import typing


class MacAddress:
    """
    Wrapper around a MAC address string that allows you to do useful
    things like formatting, etc.
    """

    def __init__(self,addr:str):
        self._addr=addr
        self.assign(addr)
        self._ip=None

    @property
    def ip(self):
        """
        the ip address associated with this mac address

        will run arpLookup() the first time to determine this

        if you want the freshest possible value, run arpLookup() youself
        """
        if self._ip is None:
            self.arpLookup()
        return self._ip

    def arpLookup(self):
        """
        look this up in the arp table to determine an ip address
        """
        from k_runner import osrun
        fmt=self.formatted('-',True)
        result=osrun.osrun('arp -a')
        for line in result.stdout.split('\n'):
            line=line.strip().split()
            if len(line)==3 and line[1]==fmt:
                self._ip=line[0]
                break
        return self._ip

    def assign(self,addr:str)->None:
        """
        Assign the value of this mac address
        """
        self._addr=addr.replace(' ','').replace(':','').replace('-','').upper()

    def __eq__(self,other:typing.Any)->bool:
        if not isinstance(other,MacAddress):
            other=MacAddress(str(other))
        return other._addr==self._addr

    def formatted(self,separator:str=':',lowercase:bool=False)->str:
        """
        :lowercase: whether hex digits are 0-9A-F or 0-9a-f
        """
        a=[self._addr[i:i+2] for i in range(0,len(self._addr),2)]
        ret=separator.join(a)
        if lowercase:
            return ret.lower()
        return ret

    def __repr__(self):
        return self.formatted()
MACAddress=MacAddress
