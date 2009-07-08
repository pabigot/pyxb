import pyxb
import unittest
import pyxb.binding.datatypes as xsd

class Test_gMonth (unittest.TestCase):

    def testBasic (self):
        self.assertRaises(pyxb.BadTypeValueError, xsd.gMonth, 0)
        self.assertRaises(pyxb.BadTypeValueError, xsd.gMonth, 13)
        v = xsd.gMonth('10')
        self.assertEqual(v.month, 10)
        v = xsd.gMonth(10)
        self.assertEqual(v.month, 10)

    def testXSDLiteral (self):
        v = xsd.gMonth(10)
        self.assertEqual('10', v.xsdLiteral())

    def testAccessor (self):
        v = xsd.gMonth(10)
        self.assertRaises((AttributeError, TypeError), getattr, v, 'year')
        #self.assertRaises((AttributeError, TypeError), getattr, v, 'month')
        self.assertRaises((AttributeError, TypeError), getattr, v, 'day')
        self.assertRaises((AttributeError, TypeError), setattr, v, 'year', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'month', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'day', 5)


if __name__ == '__main__':
    unittest.main()
