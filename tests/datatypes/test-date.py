import pyxb
import unittest
import pyxb.binding.datatypes as xsd
import datetime

class Test_date (unittest.TestCase):
    
    def verifyTime (self, dt, with_usec=True, with_adj=(0,0), with_tzinfo=True):
        self.assertEqual(2002, dt.year)
        self.assertEqual(10, dt.month)
        self.assertEqual(27, dt.day)

    def testBad (self):
        self.assertRaises(pyxb.BadTypeValueError, xsd.date, '  2002-10-27')
        self.assertRaises(pyxb.BadTypeValueError, xsd.date, '2002-10-27  ')
        self.assertRaises(pyxb.BadTypeValueError, xsd.date, '2002-10-27T')
        
    def testFromText (self):
        self.verifyTime(xsd.date('2002-10-27'), with_usec=False, with_tzinfo=False)

    def testYear (self):
        # This test can't succeed because Python doesn't support negative years.
        self.assertRaises(pyxb.BadTypeValueError, xsd.date, '-0024-01-01')

    def testXsdLiteral (self):
        dt = xsd.date('2002-10-27')
        self.assertEqual('2002-10-27', dt.xsdLiteral())


if __name__ == '__main__':
    unittest.main()
