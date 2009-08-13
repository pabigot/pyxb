from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_NCName (unittest.TestCase):
    def testValid (self):
        valid = [ 'schema', '_Underscore', '_With.Dot', 'With-Hyphen' ]
        for f in valid:
            self.assertEqual(f, xsd.NCName(f))
        self.assertEqual('LeadingSpace', xsd.NCName('  LeadingSpace'))
        self.assertEqual('TrailingSpace', xsd.NCName('TrailingSpace  '))

    def testInvalid (self):
        invalid = [ '.DotFirst', 'With Spaces', 'With:Colon', 
                    'With?Illegal', '??LeadingIllegal', 'TrailingIllegal??']
        for f in invalid:
            self.assertRaises(BadTypeValueError, xsd.NCName, f)

if __name__ == '__main__':
    unittest.main()
