import pyxb.binding.generate
import pyxb.utils.domutils
from xml.dom import Node

import pyxb.binding.basis

import os.path
schema_path = '%s/../schemas/alt-po1.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path, binding_style=pyxb.binding.basis.BINDING_STYLE_PROPERTY)
#file('code.py', 'w').write(code)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

from pyxb.utils import domutils

def ToDOM (instance, tag=None, dom_support=None):
    return instance.toDOM(dom_support).documentElement

import unittest

class TestProperties (unittest.TestCase):

    def setUp (self):
        pyxb.binding.basis.ConfigureBindingStyle(pyxb.binding.basis.BINDING_STYLE_PROPERTY)

    def tearDown (self):
        pyxb.binding.basis.ConfigureBindingStyle(pyxb.binding.basis.DEFAULT_BINDING_STYLE)

    street_content = '''95 Main St.
Anytown, AS  12345-6789'''
    street_xml = '<street>%s</street>' % (street_content,)
    street_dom = pyxb.utils.domutils.StringToDOM(street_xml).documentElement

    address1_xml = '<name>Customer</name><street>95 Main St</street>'
    address2_xml = '<name>Sugar Mama</name><street>24 E. Dearling Ave.</street>'

    def testPythonElementSimpleContent (self):
        elt = USAddress._ElementMap['street'].elementBinding()(self.street_content)
        self.assertEqual(self.street_content, elt)
        self.assertEqual(ToDOM(elt).toxml(), self.street_xml)

    def testDOMElementSimpleContent (self):
        elt = USAddress._ElementMap['street'].elementBinding().createFromDOM(self.street_dom)
        self.assertEqual(ToDOM(elt).toxml(), self.street_xml)

    def testPythonElementComplexContent_Element (self):
        addr = USAddress(name='Customer', street='95 Main St')
        self.assertEqual('95 Main St', addr.street)
        addr = USAddress('Customer', '95 Main St')
        self.assertEqual('95 Main St', addr.street)
        addr.street = '43 West Oak'
        self.assertEqual('43 West Oak', addr.street)
        #self.assertEqual('<s>%s</s>' % (self.address1_xml,), ToDOM(addr, tag='s').toxml())

    def testDOM_CTD_element (self):
        # NB: USAddress is a CTD, not an element.
        xml = '<shipTo>%s</shipTo>' % (self.address1_xml,)
        dom = pyxb.utils.domutils.StringToDOM(xml)
        addr2 = USAddress.Factory(dom_node=dom.documentElement)
        #self.assertEqual(xml, ToDOM(addr2, tag='shipTo').toxml())

    def testPurchaseOrder (self):
        po = purchaseOrder(shipTo=USAddress(name='Customer', street='95 Main St'),
                           billTo=USAddress(name='Sugar Mama', street='24 E. Dearling Ave'),
                           comment='Thanks!')
        xml = ToDOM(po).toxml()
        xml1 = '<ns1:purchaseOrder xmlns:ns1="http://www.example.com/altPO1"><shipTo><name>Customer</name><street>95 Main St</street></shipTo><billTo><name>Sugar Mama</name><street>24 E. Dearling Ave</street></billTo><ns1:comment>Thanks!</ns1:comment></ns1:purchaseOrder>'
        self.assertEqual(xml, xml1)

        dom = pyxb.utils.domutils.StringToDOM(xml)
        po2 = purchaseOrder.createFromDOM(dom.documentElement)
        self.assertEqual(xml1, ToDOM(po2).toxml())

        xml2 = '<purchaseOrder xmlns="http://www.example.com/altPO1"><shipTo><name>Customer</name><street>95 Main St</street></shipTo><billTo><name>Sugar Mama</name><street>24 E. Dearling Ave</street></billTo><comment>Thanks!</comment></purchaseOrder>'
        bds = pyxb.utils.domutils.BindingDOMSupport()
        bds.setDefaultNamespace(Namespace)
        self.assertEqual(xml2, ToDOM(po2, dom_support=bds).toxml())

if __name__ == '__main__':
    unittest.main()
    
        
