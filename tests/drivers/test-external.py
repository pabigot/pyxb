import pyxb.binding.generate
from xml.dom import minidom
from xml.dom import Node
import pyxb.Namespace
import sys
import imp

import os.path
schema_path = '%s/../schemas' % (os.path.dirname(__file__),)

# Create a module into which we'll stick the shared types bindings.
# Put it into the sys modules so the import directive in subsequent
# code is resolved.
st = imp.new_module('st')
sys.modules['st'] = st

# Now get the code for the shared types bindings, and evaluate it
# within the new module.
code = pyxb.binding.generate.GeneratePython(schema_file=schema_path + '/shared-types.xsd')
rv = compile(code, 'shared-types', 'exec')
exec code in st.__dict__

# Set the path by which we expect to reference the module
stns = pyxb.Namespace.NamespaceForURI('URN:shared-types')
stns.setModulePath('st')

# Now get and build a module that refers to that module.
code = pyxb.binding.generate.GeneratePython(schema_file=schema_path + '/test-external.xsd')
rv = compile(code, 'test-external', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestExternal (unittest.TestCase):

    def testSharedTypes (self):
        self.assertEqual(word_from._TypeDefinition, st.english)
        self.assertEqual(word_to._TypeDefinition, st.welsh)
        one = st.english('one')
        self.assertRaises(BadTypeValueError, st.english, 'five')
        # Element constructor without content is error
        self.assertRaises(BadTypeValueError, english)
        self.assertEqual('one', english('one').content())
        # Element constructor with out-of-range content is error
        self.assertRaises(BadTypeValueError, english, 'five')

        xml = '<english>one</english>'
        dom = minidom.parseString(xml)
        instance = english.CreateFromDOM(dom.documentElement)
        self.assertEqual('one', instance.content())
        self.assertEqual(xml, instance.toDOM().toxml())
        

    def testWords (self):
        xml = '<word><from>one</from><to>un</to></word>'
        dom = minidom.parseString(xml)
        instance = word.CreateFromDOM(dom.documentElement)
        self.assertEquals('one', instance.from_().content())
        self.assertEquals('un', instance.to().content())
        self.assertEqual(xml, instance.toDOM().toxml())
        
    def testBadWords (self):
        xml = '<word><from>five</from><to>pump</to></word>'
        dom = minidom.parseString(xml)
        self.assertRaises(BadTypeValueError, word.CreateFromDOM, dom.documentElement)

    def testComplexShared (self):
        xml = '<lwords language="english" newlanguage="welsh">un</lwords>'
        dom = minidom.parseString(xml)
        instance = lwords.CreateFromDOM(dom.documentElement)
        self.assertTrue(isinstance(instance, lwords))
        self.assertTrue(isinstance(instance.content(), st.welsh))
        self.assertEquals('english', instance.language())
        self.assertEquals('welsh', instance.newlanguage())

if __name__ == '__main__':
    unittest.main()
    
        
