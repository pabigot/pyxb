import pyxb
import unittest
import pyxb.binding.datatypes as xsd

class Test_token (unittest.TestCase):
    def testValid (self):
        valid = [ ('Internal spaces are ok', None),
                  ("with\nnewline", 'with newline'),
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
                xsd.token(f)
                print 'Unexpected success with "%s"' % (f,)
            except Exception, e:
                print 'Caught %s' % (type(e),)
            self.assertRaises(pyxb.BadTypeValueError, xsd.token, f)

if __name__ == '__main__':
    unittest.main()
