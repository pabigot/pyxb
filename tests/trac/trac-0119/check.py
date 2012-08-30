# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import unittest

import base
import absent

import pyxb.utils.domutils
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(base.Namespace, 'base')

class TestTrac0119 (unittest.TestCase):

    def testRoundTrip (self):
        c = absent.doit('hi')
        m = base.Message(c)
        xmls = m.toxml("utf-8")
        # Cannot resolve absent namespace in base module
        self.assertRaises(pyxb.SchemaValidationError, base.CreateFromDocument, xmls)
        # Can resolve it in absent module
        instance = absent.CreateFromDocument(xmls)
        self.assertEquals(xmls, instance.toxml("utf-8"))

    def testNoDefault (self):
        xmls='''<?xml version="1.0"?>
<base:Message xmlns:base="urn:trac0119" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <command xsi:type="doit">
    <payload>hi</payload>
  </command>
</base:Message>
'''
        # Cannot resolve absent namespace in base module
        self.assertRaises(pyxb.SchemaValidationError, base.CreateFromDocument, xmls)
        # Can resolve it in absent module
        instance = absent.CreateFromDocument(xmls)
        self.assertEquals('hi', instance.command.payload)
        # Can resolve in base module if fallback namespace overridden
        instance = base.CreateFromDocument(xmls, default_namespace=absent.Namespace)
        self.assertEquals('hi', instance.command.payload)
        
    def testDefault (self):
        xmls='''<?xml version="1.0"?>
<Message xmlns="urn:trac0119" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <command xmlns="" xsi:type="doit"> <!-- undefine the default namespace -->
    <payload>hi</payload>
  </command>
</Message>
'''
        # Cannot resolve absent namespace in base module
        self.assertRaises(pyxb.SchemaValidationError, base.CreateFromDocument, xmls)
        # Can resolve it in absent module
        instance = absent.CreateFromDocument(xmls)
        self.assertEquals('hi', instance.command.payload)
        # Can resolve in base module if fallback namespace overridden
        instance = base.CreateFromDocument(xmls, default_namespace=absent.Namespace)
        self.assertEquals('hi', instance.command.payload)
        
    def testUndefineNondefault (self):
        xmls='''<?xml version="1.0"?>
<base:Message xmlns:base="urn:trac0119" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <command xsi:type="doit" xmlns:base=""> <!-- undefine the base namespace -->
    <payload>hi</payload>
  </command>
</base:Message>
'''
        # Cannot undefine a prefix in SAX.
        import xml.sax
        self.assertRaises(xml.sax.SAXParseException, base.CreateFromDocument, xmls)
        self.assertRaises(xml.sax.SAXParseException, absent.CreateFromDocument, xmls)
        self.assertRaises(xml.sax.SAXParseException, base.CreateFromDocument, xmls, default_namespace=absent.Namespace)

if __name__ == '__main__':
    unittest.main()
