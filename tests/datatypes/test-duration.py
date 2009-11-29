import pyxb
import unittest
import pyxb.binding.datatypes as xsd

class Test_duration (unittest.TestCase):
    def testBasic (self):
        v = xsd.duration('P1347Y')
        self.assertEqual(0, v.days)
        self.assertEqual(0, v.seconds)
        self.assertEqual(0, v.microseconds)
        self.assertEqual(1347, v.durationData()['years'])
        self.assertEqual('P1347Y', v.xsdLiteral())

        v = xsd.duration('P1347M')
        self.assertEqual(0, v.days)
        self.assertEqual(0, v.seconds)
        self.assertEqual(0, v.microseconds)
        self.assertEqual(1347, v.durationData()['months'])
        self.assertEqual('P1347M', v.xsdLiteral())

        v = xsd.duration('P1Y2MT2H')
        self.assertEqual(0, v.days)
        self.assertEqual(2 * 60 * 60, v.seconds)
        self.assertEqual(0, v.microseconds)
        self.assertEqual(1, v.durationData()['years'])
        self.assertEqual(2, v.durationData()['months'])
        self.assertEqual('P1Y2MT2H', v.xsdLiteral())

        v = xsd.duration('P0Y1347M')
        self.assertEqual(0, v.days)
        self.assertEqual(0, v.seconds)
        self.assertEqual(0, v.microseconds)
        self.assertEqual(1347, v.durationData()['months'])
        self.assertEqual('P1347M', v.xsdLiteral())

        v = xsd.duration('P0Y1347M0D')
        self.assertEqual(0, v.days)
        self.assertEqual(0, v.seconds)
        self.assertEqual(0, v.microseconds)
        self.assertEqual(1347, v.durationData()['months'])
        self.assertFalse(v.negativeDuration())
        self.assertEqual('P1347M', v.xsdLiteral())

        self.assertRaises(pyxb.BadTypeValueError, xsd.duration, 'P-1347M')
        v = xsd.duration('-P1347M')
        self.assertEqual(0, v.days)
        self.assertEqual(0, v.seconds)
        self.assertEqual(0, v.microseconds)
        self.assertEqual(1347, v.durationData()['months'])
        self.assertTrue(v.negativeDuration())
        self.assertEqual('-P1347M', v.xsdLiteral())

        self.assertRaises(pyxb.BadTypeValueError, xsd.duration, 'P1Y2MT')

        v = xsd.duration('P3DT4H7M')

    def testNegative (self):
        v = xsd.duration('-P3DT4H7M23.5S')
        # Time is 19H52M36.5S into day -4
        base_date = xsd.dateTime('2000-01-10T00:00:00')
        delta_date = xsd.dateTime(base_date + v)
        self.assertEqual(-4, v.days)
        self.assertEqual(36 + 60 * (52 + 60 * 19), v.seconds)
        self.assertEqual(500000, v.microseconds)
        self.assertEqual('2000-01-06T19:52:36.5', delta_date.xsdLiteral())

    def testAddition (self):
        date = xsd.dateTime(2002, 10, 27, 12, 14, 32)
        duration = xsd.duration('P3DT5H3M')
        self.assertEqual('2002-10-30T17:17:32', xsd.dateTime(date + duration).xsdLiteral())
        self.assertEqual('2002-10-24T07:11:32', xsd.dateTime(date - duration).xsdLiteral())
        
    def testCreation (self):
        base_date = xsd.dateTime('2000-01-10T00:00:00')
        delta_date = xsd.dateTime('2000-01-06T19:52:37.5')
        v = xsd.duration(base_date - delta_date)
        self.assertEqual(3, v.days)
        self.assertEqual(14842, v.seconds)
        self.assertEqual('P3DT4H7M22.5S', v.xsdLiteral())
        


if __name__ == '__main__':
    unittest.main()
