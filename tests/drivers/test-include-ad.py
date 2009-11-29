import pyxb.binding.generate
import pyxb.utils.domutils

import os.path

from pyxb.exceptions_ import *

import unittest

class TestIncludeDD (unittest.TestCase):
    def testDefault (self):
        schema_path = '%s/../schemas/test-include-ad.xsd' % (os.path.dirname(__file__),)
        self.assertRaises(pyxb.SchemaValidationError, pyxb.binding.generate.GeneratePython, schema_location=schema_path)

if __name__ == '__main__':
    unittest.main()
    
