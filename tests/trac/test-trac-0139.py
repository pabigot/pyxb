# -*- coding: iso-2022-jp -*-
#

import sys
import pyxb.binding.generate
import pyxb.binding.datatypes as xs
import pyxb.binding.basis
import pyxb.utils.saxutils
import tempfile
import xml.sax

import os.path
xsd=u'''<?xml version="1.0" encoding="utf-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
        <xs:element name="text" type="xs:string"/>
</xs:schema>
'''

#file('schema.xsd', 'w').write(xsd)
code = pyxb.binding.generate.GeneratePython(schema_text=xsd)
file('code.py', 'w').write(code)
#print code

rv = compile(code.encode('utf-8'), 'test', 'exec')
eval(rv)

from pyxb.exceptions_ import *

import unittest

class TestTrac_0139 (unittest.TestCase):
    ascii_enc = sys.getdefaultencoding()
    ascii = u'something'
    nihongo_enc = 'iso-2022-jp'
    nihongo = u'基盤地図情報ダウンロードデータ（GML版）'
    
    @classmethod
    def buildDocument (cls, text, encoding):
        map = { 'text' : text }
        if encoding is None:
            map['encoding'] = ''
        else:
            map['encoding'] = ' encoding="%s"' % (encoding,)
        return u'<?xml version="1.0"%(encoding)s?><text>%(text)s</text>' % map

    @classmethod
    def setUpClass (cls):
        cls.nihongo_xml = cls.buildDocument(cls.nihongo, cls.nihongo_enc)
        (fd, cls.path_nihongo) = tempfile.mkstemp()
        bytes = cls.nihongo_xml
        if cls.nihongo_enc is not None:
            bytes = bytes.encode(cls.nihongo_enc)
        os.fdopen(fd, 'w').write(bytes)
        cls.ascii_xml = cls.buildDocument(cls.ascii, cls.ascii_enc)
        (fd, cls.path_ascii) = tempfile.mkstemp()
        bytes = cls.ascii_xml
        if cls.ascii_enc is not None:
            bytes = bytes.encode(cls.ascii_enc)
        os.fdopen(fd, 'w').write(bytes)

        # Ensure test failures are not due to absence of libxml2,
        # which PyXB can't control.
        cls.have_libxml2 = True
        try:
            import drv_libxml2
        except ImportError:
            cls.have_libxml2 = False
            print 'WARNING: libxml2 not present, test is not valid'

    @classmethod
    def tearDownClass (cls):
        pyxb.utils.saxutils.SetCreateParserModules(None)
        os.remove(cls.path_ascii)
        os.remove(cls.path_nihongo)

    def useLibXML2Parser (self):
        pyxb.utils.saxutils.SetCreateParserModules(['drv_libxml2'])

    # Make sure create parser modules is reset after each test
    def tearDown (self):
        pyxb.utils.saxutils.SetCreateParserModules(None)

    def testParserTypes (self):
        self.assertEqual('ascii', sys.getdefaultencoding())
        parser = pyxb.utils.saxutils.make_parser()
        self.assertTrue(isinstance(parser, xml.sax.expatreader.ExpatParser))
        if self.have_libxml2:
            import drv_libxml2
            self.useLibXML2Parser();
            parser = pyxb.utils.saxutils.make_parser()
            self.assertTrue(isinstance(parser, drv_libxml2.LibXml2Reader))

    def testASCII_expat_str (self):
        xmls = self.ascii_xml
        instance = CreateFromDocument(xmls)
        self.assertEqual(self.ascii, instance)

    def testASCII_libxml2_str (self):
        self.useLibXML2Parser();
        xmls = self.ascii_xml
        # ERROR: This should be fine, see trac/147
        #instance = CreateFromDocument(xmls)
        #self.assertEqual(self.ascii, instance)
        self.assertRaises(xml.sax.SAXParseException, CreateFromDocument, xmls)

    def testASCII_expat_file (self):
        xmls = file(self.path_ascii).read()
        instance = CreateFromDocument(xmls)
        self.assertEqual(self.ascii, instance)

    def testASCII_libxml2_file (self):
        self.useLibXML2Parser();
        xmls = file(self.path_ascii).read()
        instance = CreateFromDocument(xmls)
        self.assertEqual(self.ascii, instance)

    def testNihongo_expat_str (self):
        xmls = self.nihongo_xml
        self.assertRaises(UnicodeEncodeError, CreateFromDocument, xmls)

    def testNihongo_expat_file (self):
        xmls = file(self.path_nihongo).read()
        self.assertRaises(xml.sax.SAXParseException, CreateFromDocument, xmls)

    def testNihongo_libxml2_str (self):
        xmls = self.nihongo_xml
        # ERROR: This should be fine, see trac/147
        #instance = CreateFromDocument(xmls)
        #self.assertEqual(self.nihongo, instance)
        self.assertRaises(UnicodeEncodeError, CreateFromDocument, xmls)

    def testNihongo_libxml2_file (self):
        self.useLibXML2Parser();
        xmls = file(self.path_nihongo).read()
        instance = CreateFromDocument(xmls)
        self.assertEqual(self.nihongo, instance)

    def testASCII_stringio (self):
        f = file(self.path_ascii).read();
        sio = StringIO.StringIO(self.ascii_xml).read()
        self.assertEqual(f, sio)

if __name__ == '__main__':
    unittest.main()
