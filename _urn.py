"""
Universal Resource Name
"""
import paths


class URN(paths.URI):
    """
    Universal Resource Name

    Simple wrapper to distinguish a URN name from a regular old string
    """
    def __init__(self,urn:str):
        self._urn=urn
    def __repr__(self):
        return self._urn

urn=URN