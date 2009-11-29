import pyxb
import unittest
import pyxb.binding.datatypes as xsd
import datetime

class Test_dateTime (unittest.TestCase):
    
    def verifyTime (self, dt, with_usec=True, with_adj=(0,0), with_tzinfo=True):
        self.assertEqual(2002, dt.year)
        self.assertEqual(10, dt.month)
        self.assertEqual(27, dt.day)
        (hour_adj, minute_adj) = with_adj
        self.assertEqual(12 + hour_adj, dt.hour)
        self.assertEqual(14 + minute_adj, dt.minute)
        self.assertEqual(32, dt.second)
        if with_usec:
            self.assertEqual(123400, dt.microsecond)
        self.assertEqual(with_tzinfo, dt.hasTimeZone())

    def testBad (self):
        self.assertRaises(pyxb.BadTypeValueError, xsd.dateTime, '2002-10-27 12:14:32  ')
        self.assertRaises(pyxb.BadTypeValueError, xsd.dateTime, '2002-10-27 12:14:32.Z')
        self.assertRaises(pyxb.BadTypeValueError, xsd.dateTime, '2002-10-27 12:14:32.123405:00')
        self.assertRaises(pyxb.BadTypeValueError, xsd.dateTime, '2002-10-27 12:14:32.1234+05')
        
    def testFromText (self):
        self.verifyTime(xsd.dateTime('  2002-10-27T12:14:32'), with_usec=False, with_tzinfo=False)
        self.verifyTime(xsd.dateTime('2002-10-27T12:14:32  '), with_usec=False, with_tzinfo=False)
        self.verifyTime(xsd.dateTime('2002-10-27T12:14:32'), with_usec=False, with_tzinfo=False)
        self.verifyTime(xsd.dateTime('2002-10-27T12:14:32.1234'), with_tzinfo=False)
        self.verifyTime(xsd.dateTime('2002-10-27T12:14:32Z'), with_usec=False)
        self.verifyTime(xsd.dateTime('2002-10-27T12:14:32.1234Z'))
        self.verifyTime(xsd.dateTime('2002-10-27T12:14:32.1234+05:00'), with_adj=(-5,0))
        self.verifyTime(xsd.dateTime('2002-10-27T12:14:32.1234Z'))

    def testYear (self):
        # This test can't succeed because Python doesn't support negative years.
        self.assertRaises(pyxb.BadTypeValueError, xsd.dateTime, '-0024-01-01T00:00:00')

    def testXsdLiteral (self):
        dt = xsd.dateTime('2002-10-27T12:14:32Z')
        self.assertEqual('2002-10-27T12:14:32Z', dt.xsdLiteral())
        self.assertTrue(dt.hasTimeZone())
        self.assertEqual('2002-10-27T07:14:32Z', xsd.dateTime('2002-10-27T12:14:32+05:00').xsdLiteral())
        self.assertEqual('2002-10-27T17:14:32Z', xsd.dateTime('2002-10-27T12:14:32-05:00').xsdLiteral())
        self.assertEqual('2002-10-27T17:14:32.1234Z', xsd.dateTime('2002-10-27T12:14:32.123400-05:00').xsdLiteral())
        # No zone info
        dt = xsd.dateTime('2002-10-27T12:14:32')
        self.assertEqual('2002-10-27T12:14:32', dt.xsdLiteral())
        self.assertFalse(dt.hasTimeZone())

    # Manual test to see whether LocalTime works; run this on a
    # machine that uses DST.
    def XtestBogus (self):
        dt = xsd.dateTime.today()
        print dt.xsdLiteral()
        print str(dt)
        print dt.aslocal()
        # NB: duration does not support months in Python version
        delta = xsd.duration('P%dD' % (365 / 2))
        dt = xsd.dateTime(dt + delta)
        print dt.xsdLiteral()
        print str(dt)
        print dt.aslocal()
        

if __name__ == '__main__':
    unittest.main()
