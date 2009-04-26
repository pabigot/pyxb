from pyxb.exceptions_ import *
import unittest
import pyxb.binding.datatypes as xsd

class Test_normalizedString (unittest.TestCase):
    def testInvalid (self):
        invalid = [ "with\nnewline", "with\rreturn", "with\ttab",
                    "\n\nleading newline",
                    "trailing newline\n\n" ]
        for f in invalid:
            try:
                xsd.normalizedString(f)
                #print "\nUnexpected success with %s\n\n" % (f.replace("\n", "<nl>").replace("\r", "<cr>").replace("\t", "<tab>"),)
            except:
                pass
            self.assertRaises(BadTypeValueError, xsd.normalizedString, f)

if __name__ == '__main__':
    unittest.main()
