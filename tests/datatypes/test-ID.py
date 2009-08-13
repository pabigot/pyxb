from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_ID (unittest.TestCase):
    def testValid (self):
        valid = [ 'schema', '_Underscore', '_With.Dot', 'With-Hyphen' ]
        for f in valid:
            self.assertEqual(f, xsd.ID(f))
        self.assertEqual('LeadingSpace', xsd.ID('  LeadingSpace'))
        self.assertEqual('TrailingSpace', xsd.ID('TrailingSpace  '))

    def testInvalid (self):
        invalid = [ '.DotFirst', 'With Spaces', 'With:Colon', 
                    'With?Illegal', '??LeadingIllegal', 'TrailingIllegal??']
        for f in invalid:
            self.assertRaises(BadTypeValueError, xsd.ID, f)

if __name__ == '__main__':
    unittest.main()
