from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_NCName (unittest.TestCase):
    def testValid (self):
        valid = [ 'schema', '_Underscore', '_With.Dot', 'With-Hyphen' ]
        for f in valid:
            self.assertEqual(f, xsd.NCName(f))
        # NCName descends from token, which has whitespace=collapse
        ws_valid = ['  LeadingSpace', 'TrailingSpace  ']
        for f in ws_valid:
            self.assertEqual(f.strip(), xsd.NCName(f))

    def testInvalid (self):
        invalid = [ '.DotFirst', 'With Spaces', 'With:Colon', 'With?Illegal', '??LeadingIllegal', 'TrailingIllegal??']
        for f in invalid:
            self.assertRaises(BadTypeValueError, xsd.NCName, f)

if __name__ == '__main__':
    unittest.main()
