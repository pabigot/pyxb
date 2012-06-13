import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.domutils

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:tns="urn:trac-0071" targetNamespace="urn:trac-0071">
  <xs:element name="MetadataDocument" type="tns:MetadataType"/>
  <xs:complexType name="MetadataType">
    <xs:sequence maxOccurs="1" minOccurs="1">
      <xs:element name="template" type="xs:string"/>
      <xs:element name="timespan" maxOccurs="unbounded" minOccurs="0">
        <xs:complexType>
          <xs:sequence>
            <xs:element name="field" maxOccurs="unbounded" minOccurs="0">
              <xs:complexType>
                <xs:sequence>
                  <xs:element name="name" type="xs:string"/>
                  <xs:element name="value" minOccurs="0" maxOccurs="unbounded">
                    <xs:complexType>
                      <xs:simpleContent>
                        <xs:extension base="xs:string">
                          <xs:attribute name="lang" type="xs:language"/>
                          <xs:attribute name="user" type="xs:string"/>
                          <xs:attribute name="timestamp" type="xs:dateTime"/>
                        </xs:extension>
                      </xs:simpleContent>
                    </xs:complexType>
                  </xs:element>
                </xs:sequence>
                <xs:attribute name="track" type="xs:string"/>
              </xs:complexType>
            </xs:element>
          </xs:sequence>
          <xs:attribute name="start" type="xs:string"/>
          <xs:attribute name="end" type="xs:string"/>
        </xs:complexType>
      </xs:element>
    </xs:sequence>
  </xs:complexType>
</xs:schema>
'''

#file('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)
#print code

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0071 (unittest.TestCase):
    def test (self):
        newdoc = MetadataDocument()
        metadatadoc_type = MetadataDocument.typeDefinition()
        timespan_element = metadatadoc_type._ElementMap['timespan'].elementBinding()
        timespan_type = timespan_element.typeDefinition()
        field_element = timespan_type._ElementMap['field'].elementBinding()
        field_type = field_element.typeDefinition()
        value_element = field_type._ElementMap['value'].elementBinding()
        value_type = value_element.typeDefinition()
        newdoc.template = 'anewtemplate'

        field = field_type('title', pyxb.BIND('foo', lang='ENG'), _element=field_element)
        self.assertTrue(isinstance(field.value_, list))
        self.assertEqual(1, len(field.value_))
        self.assertTrue(isinstance(field.value_[0], value_type))
        field.validateBinding()
        self.assertEqual('<field><name>title</name><value lang="ENG">foo</value></field>', field.toxml("utf-8", root_only=True))

        field = field_type(name='title', _element=field_element)
        field.value_.append(pyxb.BIND('foo', lang='ENG'))
        self.assertTrue(isinstance(field.value_, list))
        self.assertEqual(1, len(field.value_))
        self.assertTrue(isinstance(field.value_[0], pyxb.BIND))
        field.validateBinding()
        self.assertTrue(isinstance(field.value_[0], pyxb.BIND))
        self.assertEqual('<field><name>title</name><value lang="ENG">foo</value></field>', field.toxml("utf-8", root_only=True))

        '''

        NOT YET FINISHED

        newdoc.timespan.append(pyxb.BIND( # Single timespan
                pyxb.BIND( # First field instance
                    'title',
                    pyxb.BIND('foo', lang='ENG')
                    ),
                start='-INF', end='+INF'))
        newdoc.validateBinding()
        timespan = newdoc.timespan[0]
        #self.assertTrue(isinstance(timespan, timespan_type))
        print newdoc.toxml("utf-8")
        newdoc.timespan[:] = []
        
        newdoc.timespan.append(pyxb.BIND( # Single timespan
                pyxb.BIND( # First field instance
                    name='title',
                    value=pyxb.BIND('foo', lang='ENG')
                    ),
                start='-INF', end='+INF'))
        newdoc.validateBinding()
        timespan = newdoc.timespan[0]
        #self.assertTrue(isinstance(timespan, timespan_type))
        print newdoc.toxml("utf-8")
        newdoc.timespan[:] = []

        newdoc.timespan.append(pyxb.BIND( # Single timespan
                pyxb.BIND( # First field instance
                    name='title',
                    value_=pyxb.BIND('foo', lang='ENG')
                    ),
                start='-INF', end='+INF'))
        newdoc.validateBinding()
        timespan = newdoc.timespan[0]
        #self.assertTrue(isinstance(timespan, timespan_type))
        print newdoc.toxml("utf-8")
        newdoc.timespan[:] = []

        '''

if __name__ == '__main__':
    unittest.main()
