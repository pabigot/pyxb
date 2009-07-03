import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils

from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-typeinf.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

import unittest

class TestTypeInference (unittest.TestCase):
    def testBasic (self):
        e = holder(4) # should be int
        print e.toxml()
        #self.assertEqual(e.int(), 4)
        #self.assertTrue(e.float() is None)
        #self.assertTrue(e.str() is None)
        e = holder(4.4)
        print e.toxml()
        #self.assertTrue(e.int() is None)
        #self.assertEqual(e.float(), 4.4)
        #self.assertTrue(e.str() is None)
        e = holder("3")
        print e.toxml()
        self.assertRaises(pyxb.UnrecognizedContentError, holder, {})

if __name__ == '__main__':
    unittest.main()
    
        
