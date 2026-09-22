"""
Unit tests for MimeType objects
"""
import unittest
from paths.mimeType import MimeType,asMimeType


class MimeTypeTests(unittest.TestCase):
    """
    Unit tests for MimeType objects.
    """

    def test_mime_type(self)->None:
        """
        Test that MimeType objects work correctly.
        """
        m:MimeType=asMimeType("text/plain")
        self.assertIsInstance(m,MimeType)
        self.assertEqual(str(m),"text/plain")
        self.assertEqual(m=="text/plain",True)
        self.assertEqual(m=="text/document",False)

    def test_objects_with_mime_type(self)->None:
        """
        Test that objects with a mime or mimeType member work correctly.
        """
        mimeType="application/json"
        obj=type('',(),{'mimeType':mimeType})()
        m:MimeType=asMimeType(obj) # type: ignore
        self.assertIsInstance(m,MimeType)
        self.assertEqual(m=="application/json",True)
        obj=type('',(),{'mime':mimeType})()
        m:MimeType=asMimeType(obj) # type: ignore
        self.assertIsInstance(m,MimeType)
        self.assertEqual(m=="application/json",True)
        obj=type('',(),{'__str__':lambda self: mimeType})() # type: ignore
        m:MimeType=asMimeType(obj) # type: ignore
        self.assertIsInstance(m,MimeType)
        self.assertEqual(m=="application/json",True)

if __name__ == "__main__":
    unittest.main()
