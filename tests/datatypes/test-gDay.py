import pyxb
import unittest
import pyxb.binding.datatypes as xsd

class Test_gDay (unittest.TestCase):
    def testBasic (self):
        self.assertRaises(pyxb.BadTypeValueError, xsd.gDay, 0)
        self.assertRaises(pyxb.BadTypeValueError, xsd.gDay, 42)
        v = xsd.gDay('27')
        self.assertEqual(v.day, 27)
        v = xsd.gDay(27)
        self.assertEqual(v.day, 27)

    def testXSDLiteral (self):
        v = xsd.gDay(27)
        self.assertEqual('27', v.xsdLiteral())

    def testAccessor (self):
        v = xsd.gDay(27)
        self.assertRaises((AttributeError, TypeError), getattr, v, 'year')
        self.assertRaises((AttributeError, TypeError), getattr, v, 'month')
        #self.assertRaises((AttributeError, TypeError), getattr, v, 'day')
        self.assertRaises((AttributeError, TypeError), setattr, v, 'year', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'month', 5)
        self.assertRaises((AttributeError, TypeError), setattr, v, 'day', 5)


if __name__ == '__main__':
    unittest.main()
