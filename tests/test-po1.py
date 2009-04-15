import PyWXSB.generate
from xml.dom import minidom
from xml.dom import Node

code = PyWXSB.generate.GeneratePython('schemas/po1.xsd')
rv = compile(code, 'test', 'exec')
eval(rv)

from PyWXSB.exceptions_ import *

import unittest

class TestPO1 (unittest.TestCase):
    street_xml = '''<street>95 Main St.
Anytown, AS  12345-6789</street>'''
    street_dom = minidom.parseString(street_xml).documentElement

    def testElementSimpleContent (self):
        elt = USAddress_street.CreateFromDOM(self.street_dom)
        self.assertEqual(elt.toDOM().toxml(), self.street_xml)

    def testUSAddress (self):
        #str = USAddress_street('1595 fernwood')
        #print str
        xml = '<shipTo><street>95 Main St</street><name>Customer</name></shipTo>'
        addr = USAddress(name='Customer', street='95 Main St')
        #print addr.toDOM(tag='shipTo').toxml()
        #self.assertEqual('95 Main St', addr.street().content())
        #self.assertEqual(xml, addr.toDOM(tag='shipTo').toxml())
        dom = minidom.parseString(xml)
        #addr2 = USAddress.CreateFromDOM(dom)
        #self.assertEqual(xml, addr2.toDOM(tag='shipTo').toxml())

    def testPurchaseOrder (self):
        po = purchaseOrder(shipTo=USAddress(name='Customer', street='95 Main St'),
                           billTo=USAddress(name='Sugar Mama', street='24 E. Dearling Ave'),
                           comment='Thanks, dear!')
        #print po.shipTo().toDOM().toxml()
        #print po.toDOM().toxml()

if __name__ == '__main__':
    unittest.main()
    
        
