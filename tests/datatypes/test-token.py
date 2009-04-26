from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_token (unittest.TestCase):
    def testValid (self):
        valid = [ 'Internal spaces are ok' ]
        for f in valid:
            self.assertEqual(f, xsd.token(f))

    def testInvalid (self):
        invalid = [ "with\nnewline", "with\rreturn", "with\ttab",
                    "\n\nleading newline",
                    "trailin newline\n\n",
                    ' LeadingSpace', 'TrailingSpace ',
                    'Internal  Multiple Spaces' ]
        for f in invalid:
            try:
                xsd.token(f)
                print 'Unexpected success with %s' % (f,)
            except:
                pass
            self.assertRaises(BadTypeValueError, xsd.token, f)

if __name__ == '__main__':
    unittest.main()
