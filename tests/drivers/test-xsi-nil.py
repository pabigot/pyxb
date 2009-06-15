import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils

from xml.dom import Node

import os.path
schema_path = '%s/../schemas/xsi-nil.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_file=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestXSIType (unittest.TestCase):
    def testFull (self):
        xml = '<full xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">content</full>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(instance, 'content')

    def testXFull (self):
        xml = '<xfull xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">content</xfull>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(instance, 'content')

    def testOptional (self):
        xml = '<optional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">content</optional>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(instance, 'content')



if __name__ == '__main__':
    unittest.main()
    
        
