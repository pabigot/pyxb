import pyxb.binding.generate
import pyxb.utils.domutils

import os.path
schema_path = '%s/../schemas/test-include-ddu.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
file('code.py', 'w').write(code)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestIncludeDD (unittest.TestCase):
    def testDefault (self):
        xmls = '<entry xmlns="URN:declared"><from>one</from><to>single</to></entry>'
        # Default namespace applies to from which should be in no namespace
        self.assertRaises(pyxb.UnrecognizedElementError, CreateFromDocument, xmls)

    def testExplicit (self):
        xmls = '<ns:entry xmlns:ns="URN:declared"><from>one</from><ns:to>single</ns:to></ns:entry>'
        instance = CreateFromDocument(xmls)
        self.assertEqual(english.one, instance.from_)

if __name__ == '__main__':
    unittest.main()
    
