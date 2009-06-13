from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_boolean (unittest.TestCase):
    def testTrue (self):
        self.assertTrue(xsd.boolean(True))
        self.assertTrue(xsd.boolean("true"))
        self.assertTrue(xsd.boolean(1))
        self.assertTrue(xsd.boolean("1"))

    def testFalse (self):
        self.assertFalse(xsd.boolean(False))
        self.assertFalse(xsd.boolean("false"))
        self.assertFalse(xsd.boolean(0))
        self.assertFalse(xsd.boolean("0"))
        self.assertFalse(xsd.boolean())
        
    def testInvalid (self):
        self.assertRaises(BadTypeValueError, xsd.boolean, "True")
        self.assertRaises(BadTypeValueError, xsd.boolean, "FALSE")

if __name__ == '__main__':
    unittest.main()
