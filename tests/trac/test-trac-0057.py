import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

# Thanks to agrimstrup for this example

import os.path
xsd='''
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified" attributeFormDefault="unqualified" version="8 1.87" targetNamespace="URN:test-trac-0057">  

  <xsd:element name="ObsProject"> 
    <xsd:complexType> 
      <xsd:sequence> 
        <xsd:element name="assignedPriority" type="xsd:int"/>  
        <xsd:element name="timeOfCreation" type="xsd:string"/>  
      </xsd:sequence>  
      <xsd:attribute name="schemaVersion" type="xsd:string" use="required" fixed="8"/>  
      <xsd:attribute name="revision" type="xsd:string" default="1.87"/>  
      <xsd:attribute name="almatype" type="xsd:string" use="required" fixed="APDM::ObsProject"/> 
    </xsd:complexType> 
  </xsd:element>  


</xsd:schema>
'''

#file('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0057 (unittest.TestCase):
    XMLS = '<ns1:ObsProject almatype="APDM::ObsProject" revision="1.74" schemaVersion="8" xmlns:ns1="URN:test-trac-0057"><ns1:timeOfCreation>2009-05-08 21:23:45</ns1:timeOfCreation></ns1:ObsProject>'

    def exec_toxml (self, v):
        return v.toxml()

    def tearDown (self):
        pyxb.RequireValidWhenGenerating(True)
        pyxb.RequireValidWhenParsing(True)

    def testDefault (self):
        self.assertTrue(pyxb._GenerationRequiresValid)
        self.assertTrue(pyxb._ParsingRequiresValid)
        self.assertRaises(pyxb.UnrecognizedContentError, CreateFromDocument, self.XMLS)
        doc = pyxb.utils.domutils.StringToDOM(self.XMLS)
        self.assertRaises(pyxb.UnrecognizedContentError, CreateFromDOM, doc)
        
    def testDisable (self):
        pyxb.RequireValidWhenParsing(False)
        instance = CreateFromDocument(self.XMLS)
        self.assertRaises(pyxb.DOMGenerationError, self.exec_toxml, instance)
        doc = pyxb.utils.domutils.StringToDOM(self.XMLS)
        instance = CreateFromDOM(doc)
        pyxb.RequireValidWhenGenerating(False) 
        xml = instance.toxml(root_only=True)
        self.assertEquals(xml, self.XMLS)

if __name__ == '__main__':
    unittest.main()
