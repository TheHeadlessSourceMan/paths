"""
Universal Resource Identifier

Generally speaking, this is a base class for either a URL or URN
"""

class URI:
    """
    Universal Resource Identifier

    Generally speaking, this is a base class for either a URL or URN
    """

    def exists(self)->bool:
        """
        Return True if the resource exists, False otherwise
        """
        raise NotImplementedError()

uri=URI
