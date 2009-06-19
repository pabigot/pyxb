import unittest
import pyxb.binding.datatypes as xsd

class Test_gYearMonth (unittest.TestCase):
    def testBasic (self):
        v = xsd.gYearMonth('2002-10')
        self.assertEqual(v.year, 2002)
        self.assertEqual(v.month, 10)
        v = xsd.gYearMonth(2002, 10)
        self.assertEqual(v.year, 2002)
        self.assertEqual(v.month, 10)
        self.assertRaises(TypeError, xsd.gYearMonth, 2002)

    def testXSDLiteral (self):
        v = xsd.gYearMonth(2002, 10)
        self.assertEqual('2002-10', v.xsdLiteral())

    def testAccessor (self):
        v = xsd.gYearMonth(2002, 10)
        #self.assertRaises(AttributeError, getattr, v, 'year')
        #self.assertRaises(AttributeError, getattr, v, 'month')
        self.assertRaises(AttributeError, getattr, v, 'day')
        self.assertRaises(AttributeError, setattr, v, 'year', 5)
        self.assertRaises(AttributeError, setattr, v, 'month', 5)
        self.assertRaises(AttributeError, setattr, v, 'day', 5)

if __name__ == '__main__':
    unittest.main()
