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
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="HOST">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="ID" type="xs:integer"/>
        <xs:element name="TEMPLATE" type="xs:anyType"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)

rv = compile(code, 'test', 'exec')
eval(rv)

import unittest

class TestIssue0092 (unittest.TestCase):
    def testCreateEmptyTemplate (self):
        xmlt = '<HOST><ID>1</ID><TEMPLATE/></HOST>';
        xmld = xmlt.encode('utf-8');
        doc = CreateFromDocument(xmld);
        self.assertEqual(doc.ID,1)

    def testCreateToDom (self):
        xmlt = '<HOST><ID>1</ID><TEMPLATE><NODE>1</NODE></TEMPLATE></HOST>';
        xmld = xmlt.encode('utf-8');
        doc = CreateFromDocument(xmld);
        templateFragment=doc.TEMPLATE.toDOM()
        self.assertEqual(templateFragment.toxml(), '''<?xml version="1.0" ?><TEMPLATE><NODE>1</NODE></TEMPLATE>''')

    def testCreateWithCDATAToDom (self):
        xmlt = '<HOST><ID>1</ID><TEMPLATE><NODE><![CDATA[text]]></NODE></TEMPLATE></HOST>';
        xmld = xmlt.encode('utf-8');
        doc = CreateFromDocument(xmld);
        templateFragment=doc.TEMPLATE.toDOM()
        self.assertEqual(templateFragment.toxml(), '''<?xml version="1.0" ?><TEMPLATE><NODE>text</NODE></TEMPLATE>''')

    def testCreateFromDOMWithCDATAToDom (self):
        xmlt = '<HOST><ID>1</ID><TEMPLATE><NODE><![CDATA[text]]></NODE></TEMPLATE></HOST>';
        xmld = xmlt.encode('utf-8');
        domDoc=dom.parseString(xmld);
        doc = CreateFromDOM(domDoc);
        templateFragment=doc.TEMPLATE.toDOM()
        self.assertEqual(templateFragment.toxml(), '''<?xml version="1.0" ?><TEMPLATE><NODE>text</NODE></TEMPLATE>''')


if __name__ == '__main__':
    unittest.main()
