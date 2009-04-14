import PyWXSB.generate
from xml.dom import minidom
from xml.dom import Node

code = PyWXSB.generate.GeneratePython('schemas/po1.xsd')
rv = compile(code, 'test', 'exec')
eval(rv)

from PyWXSB.exceptions_ import *

import unittest

class TestPO1 (unittest.TestCase):
    def testUSAddress (self):
        #str = USAddress_street('1595 fernwood')
        #print str
        addr = USAddress(street='1595 fernwood', name='St. Paul')
        print addr.toDOM('address').toxml()
        self.assertEqual('1595 fernwood', addr.street().content())

    def testPurchaseOrder (self):
        po = purchaseOrder(shipTo=USAddress(name='Customer', street='95 Main St'),
                           billTo=USAddress(name='Sugar Mama', street='24 E. Dearling Ave'),
                           comment='Thanks, dear!')
        print po.shipTo().toDOM().toxml()
        print po.toDOM().toxml()

if __name__ == '__main__':
    unittest.main()
    
        
