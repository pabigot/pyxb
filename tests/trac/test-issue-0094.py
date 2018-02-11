# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
import pyxb.binding.generate
import pyxb.utils.domutils
import xml.dom.minidom as dom

if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)

xsd = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified"
  targetNamespace="urn:test-issue-0094"
  xmlns:tns="urn:test-issue-0094">
  <xs:element name="MARKETPLACE">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="NAME" type="xs:string"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
  <xs:element name="MARKETPLACE_POOL">
    <xs:complexType>
        <xs:sequence maxOccurs="1" minOccurs="1">
            <xs:element ref="tns:MARKETPLACE" maxOccurs="unbounded" minOccurs="0"/>
        </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
'''

# Fully qualified XML
fqXmlSample = '''<?xml version="1.0" encoding="UTF-8"?>
<ns:MARKETPLACE_POOL xmlns:ns="urn:test-issue-0094">
  <ns:MARKETPLACE>
    <ns:NAME>OpenNebula Public</ns:NAME>
  </ns:MARKETPLACE>
</ns:MARKETPLACE_POOL>
'''

# Default-qualified XML
dqXmlSample = '''<?xml version="1.0" encoding="UTF-8"?>
<MARKETPLACE_POOL xmlns="urn:test-issue-0094">
  <MARKETPLACE>
    <NAME>OpenNebula Public</NAME>
  </MARKETPLACE>
</MARKETPLACE_POOL>
'''

# XML that lacks any namespace association
nqXmlSample = '''<?xml version="1.0" encoding="UTF-8"?>
<MARKETPLACE_POOL>
  <MARKETPLACE>
    <NAME>OpenNebula Public</NAME>
  </MARKETPLACE>
</MARKETPLACE_POOL>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#open('code.py', 'w').write(code)
rv = compile(code, 'test', 'exec')
eval(rv)

import unittest

class TestIssue0094 (unittest.TestCase):
    def testFullyQualified (self):
        doc = CreateFromDocument(fqXmlSample);
        self.assertEqual(doc.MARKETPLACE[0].NAME, "OpenNebula Public")

    def testDefaultQualified (self):
        doc = CreateFromDocument(dqXmlSample);
        self.assertEqual(doc.MARKETPLACE[0].NAME, "OpenNebula Public")

    def testNoQualifier (self):
        with self.assertRaises(pyxb.UnrecognizedDOMRootNodeError) as cm:
            doc = CreateFromDocument(nqXmlSample)

    def testNoQualifierDefaulted (self):
        with self.assertRaises(pyxb.UnrecognizedDOMRootNodeError) as cm:
            doc = CreateFromDocument(nqXmlSample, default_namespace=Namespace)

if __name__ == '__main__':
    unittest.main()
