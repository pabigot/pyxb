# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../schemas/test-namespace-uu.xsd'))
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestNamespaceUU (unittest.TestCase):
    def testBad (self):
        # Default namespace improperly gives namespace to local element
        xml = '<globalStruct xmlns="urn:namespaceTest"><local>local</local><globalElt>global</globalElt></globalStruct>'
        self.assertRaises(pyxb.UnrecognizedContentError, CreateFromDocument, xml)
        # Did not add namespace to internal global element
        xml = '<ns1:globalStruct xmlns:ns1="urn:namespaceTest"><local>local</local><globalElt>global</globalElt></ns1:globalStruct>'
        self.assertRaises(pyxb.UnrecognizedContentError, CreateFromDocument, xml)
        # Improperly added namespace to internal local element
        xml = '<ns1:globalStruct xmlns:ns1="urn:namespaceTest"><ns1:local>local</ns1:local><ns1:globalElt>global</ns1:globalElt></ns1:globalStruct>'
        self.assertRaises(pyxb.UnrecognizedContentError, CreateFromDocument, xml)

    def testGood (self):
        xml = '<ns1:globalStruct xmlns:ns1="urn:namespaceTest"><local>local</local><ns1:globalElt>global</ns1:globalElt></ns1:globalStruct>'
        instance = CreateFromDocument(xml)
        self.assertEqual(instance.local, 'local')
        self.assertEqual(instance.globalElt, 'global')

if __name__ == '__main__':
    unittest.main()
    
        
