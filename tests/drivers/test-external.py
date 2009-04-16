import pywxsb.binding.generate
from xml.dom import minidom
from xml.dom import Node
import pywxsb.Namespace
import sys
import imp

import os.path
schema_path = '%s/../schemas' % (os.path.dirname(__file__),)

# First, get and build a module that has the shared types in it.
code = pywxsb.binding.generate.GeneratePython(schema_file=schema_path + '/shared-types.xsd')
rv = compile(code, 'shared-types', 'exec')

st = imp.new_module('st')
exec code in st.__dict__
sys.modules['st'] = st

stns = pywxsb.Namespace.NamespaceForURI('URN:shared-types')
stns.setModulePath('st')

# Now get and build a module that refers to that module.  (Comment out
# the import for the shared one; it's already present.)
code = pywxsb.binding.generate.GeneratePython(schema_file=schema_path + '/test-external.xsd')
code.replace('import st', '#import st')
#print code
rv = compile(code, 'test-external', 'exec')
eval(rv)

from pywxsb.exceptions_ import *

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

if __name__ == '__main__':
    unittest.main()
    
        
