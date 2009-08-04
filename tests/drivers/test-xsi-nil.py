import pyxb
import pyxb.binding.generate
import pyxb.utils.domutils
import pyxb.binding.saxer
import StringIO

from xml.dom import Node

import os.path
schema_path = '%s/../schemas/xsi-nil.xsd' % (os.path.dirname(__file__),)
code = pyxb.binding.generate.GeneratePython(schema_location=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestXSIType (unittest.TestCase):

    def testFull (self):
        xml = '<full xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">content</full>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(instance, 'content')
        self.assertFalse(instance._isNil())
        self.assertRaises(pyxb.NoNillableSupportError, instance._setIsNil)

        xml = '<full xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="false">content</full>'
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(instance, 'content')
        self.assertFalse(instance._isNil())

        xml = '<full xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true">content</full>'
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(instance, 'content')
        self.assertFalse(instance._isNil())


    def testXFull (self):
        xml = '<xfull xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">content</xfull>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(instance, 'content')
        self.assertFalse(instance._isNil())
        self.assertRaises(pyxb.NoNillableSupportError, instance._setIsNil)

    def testOptional (self):
        xml = '<optional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">content</optional>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(instance, 'content')
        self.assertFalse(instance._isNil())
        instance._setIsNil()
        self.assertTrue(instance._isNil())

        saxer = pyxb.binding.saxer.make_parser(fallback_namespace=Namespace)
        handler = saxer.getContentHandler()
        saxer.parse(StringIO.StringIO(xml))
        instance = handler.rootObject()
        self.assertEqual(instance, 'content')
        self.assertFalse(instance._isNil())


    def testOptionalNilFalse (self):
        xml = '<optional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="false">content</optional>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(instance, 'content')
        self.assertFalse(instance._isNil())
        instance._setIsNil()
        self.assertTrue(instance._isNil())

    def testOptionalNilEETag (self):
        xml = '<optional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(instance, '')
        self.assertTrue(instance._isNil())

        saxer = pyxb.binding.saxer.make_parser(fallback_namespace=Namespace)
        handler = saxer.getContentHandler()
        saxer.parse(StringIO.StringIO(xml))
        instance = handler.rootObject()
        self.assertEqual(instance, '')
        self.assertTrue(instance._isNil())

    def testOptionalNilSETag (self):
        xml = '<optional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"></optional>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(instance, '')
        self.assertTrue(instance._isNil())

        saxer = pyxb.binding.saxer.make_parser(fallback_namespace=Namespace)
        handler = saxer.getContentHandler()
        saxer.parse(StringIO.StringIO(xml))
        instance = handler.rootObject()
        self.assertEqual(instance, '')
        self.assertTrue(instance._isNil())

    def testOptionalNilSCETag (self):
        xml = '<optional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"><!-- comment --></optional>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(instance, '')
        self.assertTrue(instance._isNil())

        saxer = pyxb.binding.saxer.make_parser(fallback_namespace=Namespace)
        handler = saxer.getContentHandler()
        saxer.parse(StringIO.StringIO(xml))
        instance = handler.rootObject()
        self.assertEqual(instance, '')
        self.assertTrue(instance._isNil())

    def testNilOptionalSpaceContent (self):
        xml = '<optional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"> </optional>'
        self.assertRaises(pyxb.ExtraContentError, CreateFromDocument, xml)

    def testNilComplexSpaceContent (self):
        xml = '<complex xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"> </complex>'
        self.assertRaises(pyxb.ExtraContentError, CreateFromDocument, xml)

    def testComplexInternal (self):
        xml = '<complex><full>full content</full><optional>optional content</optional></complex>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(instance.full, 'full content')
        self.assertEqual(instance.optional, 'optional content')
        self.assertFalse(instance.optional._isNil())
        self.assertEqual(instance.toDOM().documentElement.toxml(), xml)
        instance.validateBinding()

        saxer = pyxb.binding.saxer.make_parser(fallback_namespace=Namespace)
        handler = saxer.getContentHandler()
        saxer.parse(StringIO.StringIO(xml))
        instance = handler.rootObject()
        self.assertEqual(instance.full, 'full content')
        self.assertEqual(instance.optional, 'optional content')
        self.assertFalse(instance.optional._isNil())

        xml = '<complex xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><full>full content</full><optional xsi:nil="true"></optional></complex>'
        doc = pyxb.utils.domutils.StringToDOM(xml)
        instance = CreateFromDOM(doc.documentElement)
        self.assertEqual(instance.full, 'full content')
        self.assertEqual(instance.optional, '')
        self.assertTrue(instance.optional._isNil())
        self.assertEqual(instance.toDOM().documentElement.toxml(), xml)
        instance.validateBinding()

        saxer = pyxb.binding.saxer.make_parser(fallback_namespace=Namespace)
        handler = saxer.getContentHandler()
        saxer.parse(StringIO.StringIO(xml))
        instance = handler.rootObject()
        self.assertEqual(instance.full, 'full content')
        self.assertEqual(instance.optional, '')
        self.assertTrue(instance.optional._isNil())

        xml = '<complex xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>'
        instance._setIsNil()
        self.assertEqual(instance.toDOM().documentElement.toxml(), xml)
        instance.validateBinding()

    def testComplex (self):
        canonical = '<complex xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"/>'
        for xml in ( canonical,
                     '<complex xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"></complex>',
                     '<complex xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:nil="true"><!-- comment --></complex>') :
            doc = pyxb.utils.domutils.StringToDOM(xml)
            instance = CreateFromDOM(doc.documentElement)
            self.assertTrue(instance._isNil())
            self.assertEqual(instance.toDOM().documentElement.toxml(), canonical)
            instance.validateBinding()

if __name__ == '__main__':
    unittest.main()
    
        
