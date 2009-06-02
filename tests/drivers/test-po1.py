import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/po1.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_file=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

from pyxb.utils import domutils
def ToDOM (instance, tag=None):
    dom_support = domutils.BindingDOMSupport()
    parent = None
    if tag is not None:
        parent = dom_support.document().appendChild(dom_support.document().createElement(tag))
    dom_support = instance.toDOM(dom_support, parent)
    return dom_support.finalize().documentElement

import unittest

class TestPO1 (unittest.TestCase):
    street_content = '''95 Main St.
Anytown, AS  12345-6789'''
    street_xml = '<street>%s</street>' % (street_content,)
    street_dom = pyxb.utils.domutils.StringToDOM(street_xml).documentElement

    address1_xml = '<name>Customer</name><street>95 Main St</street>'
    address2_xml = '<name>Sugar Mama</name><street>24 E. Dearling Ave.</street>'

    def testPythonElementSimpleContent (self):
        elt = USAddress_street(self.street_content)
        self.assertEqual(self.street_content, elt.content())
        self.assertEqual(ToDOM(elt).toxml(), self.street_xml)

    def testDOMElementSimpleContent (self):
        elt = USAddress_street.CreateFromDOM(self.street_dom)
        self.assertEqual(ToDOM(elt).toxml(), self.street_xml)

    def testPythonElementComplexContent_Element (self):
        addr = USAddress(name='Customer', street='95 Main St')
        self.assertEqual('95 Main St', addr.street().content())
        self.assertEqual('<s>%s</s>' % (self.address1_xml,), ToDOM(addr, tag='s').toxml())

    def testDOM_CTD_element (self):
        # NB: USAddress is a CTD, not an element.
        xml = '<shipTo>%s</shipTo>' % (self.address1_xml,)
        dom = pyxb.utils.domutils.StringToDOM(xml)
        addr2 = USAddress.CreateFromDOM(dom.documentElement)
        self.assertEqual(xml, ToDOM(addr2, tag='shipTo').toxml())

    def testPurchaseOrder (self):
        po = purchaseOrder(shipTo=USAddress(name='Customer', street='95 Main St'),
                           billTo=USAddress(name='Sugar Mama', street='24 E. Dearling Ave'),
                           comment='Thanks!')
        xml = ToDOM(po).toxml()
        dom = pyxb.utils.domutils.StringToDOM(xml)
        po2 = purchaseOrder.CreateFromDOM(dom.documentElement)
        self.assertEqual(xml, ToDOM(po2).toxml())

if __name__ == '__main__':
    unittest.main()
    
        
