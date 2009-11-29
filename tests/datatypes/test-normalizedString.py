from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_normalizedString (unittest.TestCase):
    def testValid (self):
        valid = [ ("with\nnewline", 'with newline'),
                  ("with\rreturn", 'with return'),
                  ("with\ttab", 'with tab'),
                  ("\n\nleading newline", 'leading newline'),
                  ("trailing newline\n\n", 'trailing newline'),
                  (' LeadingSpace', 'LeadingSpace'),
                  ('TrailingSpace ', 'TrailingSpace'),
                  ('Internal  Multiple Spaces', 'Internal Multiple Spaces'),
                  ]
        for (before, expected) in valid:
            if expected is None:
                expected = before
            try:
                self.assertEqual(expected, xsd.token(before))
            except pyxb.PyXBException, e:
                print 'Unexpected failure on "%s": %s' % (before, e)

    def testInvalid (self):
        invalid = [  ]
        for f in invalid:
            try:
                xsd.normalizedString(f)
                #print "\nUnexpected success with %s\n\n" % (f.replace("\n", "<nl>").replace("\r", "<cr>").replace("\t", "<tab>"),)
            except:
                pass
            self.assertRaises(BadTypeValueError, xsd.normalizedString, f)

if __name__ == '__main__':
    unittest.main()
