import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils

from xml.dom import Node

import os.path
schema_path = '%s/../schemas/xsi-type.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

originalOneFloor = oneFloor
def oneFloorCtor (*args, **kw):
    return restaurant(*args, **kw)
originalOneFloor._SetAlternativeConstructor(oneFloorCtor)

from pyxb.exceptions_ import *

import unittest

class TestXSIType (unittest.TestCase):
    def testFailsNoType (self):
        xml = '<elt/>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        self.assertRaises(pyxb.AbstractInstantiationError, CreateFromDOM, doc.documentElement)

    def testDirect (self):
        xml = '<notAlt attrOne="low"><first>content</first></notAlt>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual('content', instance.first)
        self.assertEqual('low', instance.attrOne)

    def testSubstitutions (self):
        xml = '<elt attrOne="low" xsi:type="alt1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><first>content</first></elt>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual('content', instance.first)
        self.assertEqual('low', instance.attrOne)
        xml = '<elt attrTwo="hi" xsi:type="alt2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><second/></elt>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertTrue(instance.second is not None)
        self.assertEqual('hi', instance.attrTwo)

    def testMultilevel (self):
        xml = '<concreteBase><basement>dirt floor</basement></concreteBase>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual('dirt floor', instance.basement)
        xml = '<oneFloor xsi:type="restaurant" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><basement>concrete</basement><lobby>tiled</lobby><room>eats</room></oneFloor>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(concreteBase_.basement, instance.__class__.basement)
        self.assertEqual(oneFloor_.lobby, instance.__class__.lobby)
        self.assertEqual(restaurant_.room, instance.__class__.room)
        self.assertEqual('tiled', instance.lobby)
        self.assertEqual('eats', instance.room)

    def testConstructor (self):
        kw = { 'basement' : 'concrete',
               'lobby' : 'tiled',
               'room' : 'eats' }
        ctd = restaurant_(**kw)
        dom = ctd.toDOM().documentElement
        xml = '<restaurant><basement>concrete</basement><lobby>tiled</lobby><room>eats</room></restaurant>'
        self.assertEqual(xml, dom.toxml())

        rest = restaurant(**kw)
        dom = rest.toDOM().documentElement
        self.assertEqual(xml, dom.toxml())

        self.assertRaises(pyxb.AbstractInstantiationError, originalOneFloor, **kw)

    def testNesting (self):
        instance = block(oneFloor=[ restaurant(basement="dirt", lobby="tile", room="messy"),
                                    restaurant(basement="concrete", lobby="carpet", room="tidy")])
        self.assertEqual('dirt', instance.oneFloor[0].basement)
        self.assertEqual('messy', instance.oneFloor[0].room)
        self.assertEqual('concrete', instance.oneFloor[1].basement)
        self.assertEqual('tidy', instance.oneFloor[1].room)
        xml = instance.toxml()
        dom = pyxb.utils.domutils.StringToDOM(xml)
        instance2 = CreateFromDOM(dom.documentElement)
        r2 = instance2.toxml()
        r3 = instance2.toxml()
        self.assertEqual(r2, r3)
        self.assertEqual(xml, r2)

if __name__ == '__main__':
    unittest.main()
