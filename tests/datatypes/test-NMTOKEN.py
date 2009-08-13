from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_NMTOKEN (unittest.TestCase):
    def testValid (self):
        valid = [ 'schema', '_Underscore', '_With.Dot', 'With-Hyphen',
                  'With:Colon', '.DotFirst' ]
        for f in valid:
            self.assertEqual(f, xsd.NMTOKEN(f))
        self.assertEqual('LeadingSpace', xsd.NMTOKEN('  LeadingSpace'))
        self.assertEqual('TrailingSpace', xsd.NMTOKEN('TrailingSpace  '))

    def testInvalid (self):
        invalid = [ 'With Spaces', 
                    'With?Illegal', '??LeadingIllegal', 'TrailingIllegal??']
        for f in invalid:
            try:
                xsd.NMTOKEN(f)
                print 'Unexpected success with %s' % (f,)
            except:
                pass
            self.assertRaises(BadTypeValueError, xsd.NMTOKEN, f)

if __name__ == '__main__':
    unittest.main()
