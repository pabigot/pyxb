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
        self.assertEqual(2, len(CTD_empty._ElementMap))
        ef = CTD_empty._ElementMap['CreateFromDOM']
        self.assertEqual('CreateFromDOM_', ef.pythonTag())
        self.assertFalse(ef.isPlural())
        self.assertTrue(ef.defaultValue() is None)
        ef = CTD_empty._ElementMap['Factory']
        self.assertEqual('Factory_', ef.pythonTag())
        self.assertFalse(ef.isPlural())
        self.assertTrue(ef.defaultValue() is None)
        self.assertEqual(2, len(CTD_empty._AttributeMap))
        self.assertEqual('toDOM_', CTD_empty._AttributeMap['toDOM'].pythonTag())
        self.assertEqual('Factory__', CTD_empty._AttributeMap['Factory'].pythonTag())

if __name__ == '__main__':
    unittest.main()
    
