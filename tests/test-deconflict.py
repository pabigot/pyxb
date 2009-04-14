import PyWXSB.generate
from xml.dom import minidom
from xml.dom import Node

code = PyWXSB.generate.GeneratePython('schemas/test-deconflict.xsd')
rv = compile(code, 'test', 'exec')
eval(rv)

from PyWXSB.exceptions_ import *

import unittest

class TestDeconflict (unittest.TestCase):
    def testAttributes (self):
        self.assertEqual(2, len(CTD_empty._ElementNameMap))
        self.assertEqual(('CreateFromDOM_', False), CTD_empty._ElementNameMap['CreateFromDOM'])
        self.assertEqual(('Factory_', False), CTD_empty._ElementNameMap['Factory'])
        self.assertEqual(2, len(CTD_empty._AttributeNameMap))
        self.assertEqual('toDOM_', CTD_empty._AttributeNameMap['toDOM'])
        self.assertEqual('Factory__', CTD_empty._AttributeNameMap['Factory'])

if __name__ == '__main__':
    unittest.main()
    
