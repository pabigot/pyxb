from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_QName (unittest.TestCase):
    def testValid (self):
        valid = [ 'schema', 'xs:something', 'with.dots' ]
        for f in valid:
            self.assertEqual(f, xsd.QName(f))
        self.assertEqual('whitespace', xsd.QName(' whitespace '))

    def testInvalid (self):
        invalid = [ '-NonName', '-also:-not', 'and:-not', 'too:many:colons' ]
        for f in invalid:
            try:
                xsd.QName(f)
                print 'Unexpected pass with %s' % (f,)
            except:
                pass
            self.assertRaises(BadTypeValueError, xsd.QName, f)

if __name__ == '__main__':
    unittest.main()
