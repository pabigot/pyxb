import unittest
import pyxb.binding.datatypes as xsd

class Test_gMonthDay (unittest.TestCase):
    def testBasic (self):
        v = xsd.gMonthDay('10-27')
        #self.assertEqual(v.year, 2002)
        self.assertEqual(v.month, 10)
        self.assertEqual(v.day, 27)
        v = xsd.gMonthDay(10, 27)
        #self.assertEqual(v.year, 2002)
        self.assertEqual(v.month, 10)
        self.assertEqual(v.day, 27)
        self.assertRaises(TypeError, xsd.gMonthDay, 2002)

    def testXSDLiteral (self):
        v = xsd.gMonthDay(10, 27)
        self.assertEqual('10-27', v.xsdLiteral())

    def testAccessor (self):
        v = xsd.gMonthDay(10, 27)
        self.assertRaises((AttributeError, TypeError), getattr, v, 'year')
        #self.assertRaises((AttributeError, TypeError), getattr, v, 'month')
        #self.assertRaises((AttributeError, TypeError), getattr, v, 'day')
        self.assertRaises((AttributeError, TypeError), setattr, v, 'year', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'month', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'day', 5)

if __name__ == '__main__':
    unittest.main()
