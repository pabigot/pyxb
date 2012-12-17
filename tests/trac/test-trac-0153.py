# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
xsd='''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:group name="gText">
    <xs:choice>
      <xs:element ref="text"/>
      <xs:element ref="bold"/>
      <xs:element ref="ital"/>
    </xs:choice>
  </xs:group>
  <xs:complexType name="tText" mixed="true">
    <xs:group ref="gText" minOccurs="0" maxOccurs="unbounded"/>
  </xs:complexType>
  <xs:complexType name="tBold" mixed="true">
    <xs:group ref="gText" minOccurs="0" maxOccurs="unbounded"/>
  </xs:complexType>
  <xs:complexType name="tItal" mixed="true">
    <xs:group ref="gText" minOccurs="0" maxOccurs="unbounded"/>
  </xs:complexType>
  <xs:element name="text" type="tText"/>
  <xs:element name="bold" type="tBold"/>
  <xs:element name="ital" type="tItal"/>
  <xs:complexType name="tOrdered">
    <xs:sequence>
      <xs:element ref="bold" minOccurs="0" maxOccurs="unbounded"/>
      <xs:element ref="ital" minOccurs="0" maxOccurs="unbounded"/>
      <xs:element ref="text" minOccurs="0" maxOccurs="unbounded"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="ordered" type="tOrdered"/>
</xs:schema>'''

code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
#file('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

# Assign a shared validation configuration to these types
gvc = pyxb.GlobalValidationConfig
vc = gvc.copy()
for cls in [ tText, tBold, tItal, tOrdered ]:
    cls._SetValidationConfig(vc)

from pyxb.exceptions_ import *

import unittest
import sys

class TestTrac0153 (unittest.TestCase):
    def tearDown (self):
        vc._setContentInfluencesGeneration(gvc.contentInfluencesGeneration)
        vc._setOrphanElementInContent(gvc.orphanElementInContent)
        vc._setInvalidElementInContent(gvc.invalidElementInContent)

    ExpectedText = '''<text>Intro with <bold>bold text</bold> and <ital>italicized text with <bold>bold</bold> inside</ital> ending with a little <bold>more bold</bold> text.</text>'''

    def makeText (self):
        return text('Intro with ',
                    bold('bold text'),
                    ' and ',
                    ital('italicized text with ', bold('bold'), ' inside'),
                    ' ending with a little ',
                    bold('more bold'),
                    ' text.')

    ExpectedMulti = '''<text>t1<bold>b2</bold>t3<bold>b4</bold><ital>i5</ital><bold>b6</bold></text>'''
    def makeMulti (self):
        return text('t1', bold('b2'), 't3', bold('b4'), ital('i5'), bold('b6'))

    def testDefaults (self):
        self.assertEqual(vc.contentInfluencesGeneration, vc.MIXED_ONLY)
        self.assertEqual(vc.orphanElementInContent, vc.IGNORE_ONCE)
        self.assertEqual(vc.invalidElementInContent, vc.IGNORE_ONCE)

    def testMakeText (self):
        i = self.makeText()
        self.assertEqual(2, len(i.bold))
        self.assertEqual(1, len(i.ital))
        self.assertEqual(1, len(i.ital[0].bold))
        self.assertEqual(self.ExpectedText, i.toxml('utf-8', root_only=True))
        i2 = CreateFromDocument(self.ExpectedText)
        self.assertEqual(self.ExpectedText, i2.toxml('utf-8', root_only=True))

    def testNeverCIT (self):
        i = self.makeText()
        vc._setContentInfluencesGeneration(vc.NEVER)
        # All non-element content is lost, and element content is
        # emitted in declaration order.
        self.assertEqual('<text><bold/><bold/><ital><bold/></ital></text>', i.toxml('utf-8', root_only=True))

    def testOrphan (self):
        i = self.makeText()
        # Drop the second bold
        dropped = i.bold.pop()
        xmls = i.toxml('utf-8', root_only=True)
        self.assertEqual(vc.orphanElementInContent, vc.IGNORE_ONCE)
        self.assertEqual('''<text>Intro with <bold>bold text</bold> and <ital>italicized text with <bold>bold</bold> inside</ital> ending with a little  text.</text>''',
                         xmls)
        vc._setOrphanElementInContent(vc.GIVE_UP)
        self.assertEqual(vc.orphanElementInContent, vc.GIVE_UP)
        self.assertEqual(gvc.orphanElementInContent, gvc.IGNORE_ONCE)
        xmls = i.toxml('utf-8', root_only=True)
        self.assertEqual('''<text>Intro with <bold>bold text</bold> and <ital>italicized text with <bold>bold</bold> inside</ital> ending with a little  text.</text>''',
                         xmls)
        vc._setOrphanElementInContent(vc.RAISE_EXCEPTION)
        self.assertEqual(vc.orphanElementInContent, vc.RAISE_EXCEPTION)
        self.assertEqual(gvc.orphanElementInContent, gvc.IGNORE_ONCE)
        if sys.version_info[:2] < (2, 7):
            self.assertRaises(pyxb.OrphanElementContentError, i.toxml, 'utf-8', root_only=True)
            return
        with self.assertRaises(pyxb.OrphanElementContentError) as cm:
            xmls = i.toxml('utf-8', root_only=True)
        e = cm.exception
        self.assertEqual(e.instance, i)
        self.assertEqual(e.preferred.value, dropped)

    def testOrphan2 (self):
        i = self.makeMulti()
        xmls = i.toxml('utf-8', root_only=True) 
        self.assertEqual(self.ExpectedMulti, xmls)
        self.assertEqual(3, len(i.bold))
        dropped = i.bold.pop(0)
        xmls = i.toxml('utf-8', root_only=True) 
        self.assertEqual(vc.orphanElementInContent, vc.IGNORE_ONCE)
        self.assertEqual('<text>t1t3<bold>b4</bold><ital>i5</ital><bold>b6</bold></text>', xmls)
        vc._setOrphanElementInContent(vc.GIVE_UP)
        xmls = i.toxml('utf-8', root_only=True) 
        # Elements in declaration order, non-element content at end
        self.assertEqual('<text><bold>b4</bold><bold>b6</bold><ital>i5</ital>t1t3</text>', xmls)

    ExpectedOrdered = '''<ordered><bold>b1</bold><bold>b2</bold><ital>i1</ital><text>t1</text></ordered>'''
    def makeOrdered (self):
        return ordered(bold('b1'), bold('b2'), ital('i1'), text('t1'))

    def testOrdered (self):
        i = self.makeOrdered()
        xmls = i.toxml('utf-8', root_only=True)
        self.assertEqual(self.ExpectedOrdered, xmls)

if __name__ == '__main__':
    unittest.main()
    
