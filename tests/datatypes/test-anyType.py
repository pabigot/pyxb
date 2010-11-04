import unittest
import pyxb.binding.datatypes as xsd

class subAny (xsd.anyType):
    pass

class Test_anyType (unittest.TestCase):
    def testUrType (self):
        self.assertFalse(xsd.anySimpleType._IsUrType())
        self.assertTrue(xsd.anyType._IsUrType())
        self.assertFalse(subAny._IsUrType())

if __name__ == '__main__':
    unittest.main()
