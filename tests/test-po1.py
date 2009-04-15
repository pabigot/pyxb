import PyWXSB.generate
from xml.dom import minidom
from xml.dom import Node

code = PyWXSB.generate.GeneratePython('schemas/po1.xsd')
rv = compile(code, 'test', 'exec')
eval(rv)

from PyWXSB.exceptions_ import *

import unittest

class TestPO1 (unittest.TestCase):
    street_content = '''95 Main St.
Anytown, AS  12345-6789'''
    street_xml = '<street>%s</street>' % (street_content,)
    street_dom = minidom.parseString(street_xml).documentElement

    # Note: name comes before street in the schema.  For now, the
    # order maintenance is wrong.
    address1_xml = '<name>Customer</name><street>95 Main St</street>'
    address2_xml = '<name>Sugar Mama</name><street>24 E. Dearling Ave.</street>'
    #address1_xml = '<street>95 Main St</street><name>Customer</name>'
    #address2_xml = '<street>24 E. Dearling Ave.</street><name>Sugar Mama</name>'

    def testPythonElementSimpleContent (self):
        elt = USAddress_street(self.street_content)
        self.assertEqual(self.street_content, elt.content())
        self.assertEqual(elt.toDOM().toxml(), self.street_xml)

    def testDOMElementSimpleContent (self):
        elt = USAddress_street.CreateFromDOM(self.street_dom)
        self.assertEqual(elt.toDOM().toxml(), self.street_xml)

    def testPythonElementComplexContent_Element (self):
        addr = USAddress(name='Customer', street='95 Main St')
        self.assertEqual('95 Main St', addr.street().content())
        self.assertEqual('<s>%s</s>' % (self.address1_xml,), addr.toDOM(tag='s').toxml())

    def testDOM_CTD_element (self):
        # NB: USAddress is a CTD, not an element.
        xml = '<shipTo>%s</shipTo>' % (self.address1_xml,)
        dom = minidom.parseString(xml)
        addr2 = USAddress.CreateFromDOM(dom.documentElement)
        print addr2
        #self.assertEqual(xml, addr2.toDOM(tag='shipTo').toxml())

    def testPurchaseOrder (self):
        po = purchaseOrder(shipTo=USAddress(name='Customer', street='95 Main St'),
                           billTo=USAddress(name='Sugar Mama', street='24 E. Dearling Ave'),
                           comment='Thanks, dear!')
        #print po.shipTo().toDOM().toxml()
        #print po.toDOM().toxml()

if __name__ == '__main__':
    unittest.main()
    
        
