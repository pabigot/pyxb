import pyxb.binding.generate
import pyxb.binding.datatypes as xsd
import pyxb.utils.domutils
import pyxb.binding.basis
from xml.dom import Node
import new

import os.path
schema_path = '%s/../schemas/components.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)
rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestStyle (unittest.TestCase):
    
    def setUp (self):
        self.__inBindingStyle = pyxb.binding.basis.CURRENT_BINDING_STYLE
        self.__simpleInstance = CreateFromDocument('<simple>simple</simple>')
        self.__complexInstance = CreateFromDocument('<complex><simple>sub_simple></simple><complex/></complex>')
        self.__complexSimpleInstance = CreateFromDocument('<complexSimple attr="value">simple content</complexSimple>')

    def tearDown (self):
        pyxb.binding.basis.ConfigureBindingStyle(self.__inBindingStyle)

    def testAccessor (self):
        pyxb.binding.basis.ConfigureBindingStyle(pyxb.binding.basis.BINDING_STYLE_ACCESSOR)
        self.assertTrue(isinstance(pyxb.binding.basis.complexTypeDefinition.value, new.instancemethod))
        self.assertEqual('simple content', self.__complexSimpleInstance.value())
        self.assertTrue(isinstance(pyxb.binding.basis.complexTypeDefinition.content, new.instancemethod))
        cv = self.__complexInstance.content()
        self.assertTrue(isinstance(cv, list))

    def testProperty (self):
        pyxb.binding.basis.ConfigureBindingStyle(pyxb.binding.basis.BINDING_STYLE_PROPERTY)
        self.assertTrue(isinstance(pyxb.binding.basis.complexTypeDefinition.value, new.instancemethod))
        self.assertEqual('simple content', self.__complexSimpleInstance.value())
        self.assertTrue(isinstance(pyxb.binding.basis.complexTypeDefinition.content, new.instancemethod))
        cv = self.__complexInstance.content()
        self.assertTrue(isinstance(cv, list))

if __name__ == '__main__':
    unittest.main()
    
        
