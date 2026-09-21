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

        if you want the freshest possible value, run arpLookup() yourself
        """
        if self._ip is None:
            self.arpLookup()
        return self._ip

    @staticmethod
    def _is_ip_address(value:str)->bool:
        """Return True when the token looks like an IPv4 address."""
        if value is None:
            return False
        parts = value.strip('()[]').split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False

    def arpLookup(self):
        """
        look this up in the arp table to determine an ip address
        """
        from k_runner.osrun import osrun
        fmt=self.formatted('-',True)
        result=osrun('arp -a')
        for raw_line in result.stdout.split('\n'):
            line = raw_line.strip().split()
            if not line:
                continue

            if len(line) >= 2:
                mac_token = line[-1].strip('()[]')
                mac_value = mac_token.replace('-', '').replace(':', '').upper()
                if (
                    self._is_ip_address(line[0])
                    and len(mac_value) == 12
                    and all(ch in '0123456789ABCDEF' for ch in mac_value)
                    and mac_value == self._addr
                ):
                    self._ip = line[0].strip('()[]')
                    return self._ip

            if len(line) >= 3:
                mac_token = line[1].strip('()[]')
                mac_value = mac_token.replace('-', '').replace(':', '').upper()
                if self._is_ip_address(line[0]) and mac_token.lower() == fmt:
                    self._ip = line[0].strip('()[]')
                    return self._ip
                if (
                    len(mac_value) == 12
                    and all(ch in '0123456789ABCDEF' for ch in mac_value)
                    and mac_value == self._addr
                ):
                    if self._is_ip_address(line[0]):
                        self._ip = line[0].strip('()[]')
                        return self._ip
                    if len(line) >= 4 and self._is_ip_address(line[-2].strip('()[]')):
                        self._ip = line[-2].strip('()[]')
                        return self._ip

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
