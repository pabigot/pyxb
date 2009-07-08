import pyxb
import unittest
import pyxb.binding.datatypes as xsd

class Test_gYear (unittest.TestCase):
    def testBasic (self):
        v = xsd.gYear('1234')
        self.assertEqual(v.year, 1234)
        v = xsd.gYear(1234)
        self.assertEqual(v.year, 1234)

    def testXSDLiteral (self):
        v = xsd.gYear(1234)
        self.assertEqual('1234', v.xsdLiteral())

    def testAccessor (self):
        v = xsd.gYear(1234)
        #self.assertRaises((AttributeError, TypeError), getattr, v, 'year')
        self.assertRaises((AttributeError, TypeError), getattr, v, 'month')
        self.assertRaises((AttributeError, TypeError), getattr, v, 'day')
        self.assertRaises((AttributeError, TypeError), setattr, v, 'year', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'month', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'day', 5)

        
if __name__ == '__main__':
    unittest.main()
