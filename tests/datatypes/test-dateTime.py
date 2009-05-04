import unittest
import pyxb.binding.datatypes as xsd

class Test_dateTime (unittest.TestCase):
    
    def testBasics (self):
        dt = xsd.dateTime('2002-10-10T12:00:00')
        dt = xsd.dateTime('2002-10-10T12:00:00.1234')
        print '%s %s' % (dt, dt.xsdLiteral())
        dt = xsd.dateTime('2002-10-10T12:00:00.1234+05:00')
        print '%s %s' % (dt, dt.xsdLiteral())
        dt = xsd.dateTime('2002-10-10T00:00:00.1234+05:00')
        print '%s %s' % (dt, dt.xsdLiteral())
        dt = xsd.dateTime('2002-10-10T12:00:00.1234Z')
        print '%s %s' % (dt, dt.xsdLiteral())
        print xsd.dateTime().xsdLiteral()

if __name__ == '__main__':
    unittest.main()
