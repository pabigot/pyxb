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
    
    def buildDocument (self, text, encoding):
        map = { 'text' : text }
        if encoding is None:
            map['encoding'] = ''
        else:
            map['encoding'] = ' encoding="%s"' % (encoding,)
        return u'<?xml version="1.0"%(encoding)s?><text>%(text)s</text>' % map

    # NOTE: Init-lower version does not exist before Python 2.7, so
    # make this non-standard and invoke it in init
    def SetUpClass (self):
        self.nihongo_xml = self.buildDocument(self.nihongo, self.nihongo_enc)
        (fd, self.path_nihongo) = tempfile.mkstemp()
        bytes = self.nihongo_xml
        if self.nihongo_enc is not None:
            bytes = bytes.encode(self.nihongo_enc)
        os.fdopen(fd, 'w').write(bytes)
        self.ascii_xml = self.buildDocument(self.ascii, self.ascii_enc)
        (fd, self.path_ascii) = tempfile.mkstemp()
        bytes = self.ascii_xml
        if self.ascii_enc is not None:
            bytes = bytes.encode(self.ascii_enc)
        os.fdopen(fd, 'w').write(bytes)

        # Ensure test failures are not due to absence of libxml2,
        # which PyXB can't control.
        self.have_libxml2 = True
        try:
            import drv_libxml2
        except ImportError:
            self.have_libxml2 = False
            print 'WARNING: libxml2 not present, test is not valid'

    # NOTE: Init-lower version does not exist before Python 2.7, so
    # make this non-standard and invoke it in del
    def TearDownClass (self):
        os.remove(self.path_ascii)
        os.remove(self.path_nihongo)

    def useLibXML2Parser (self):
        pyxb.utils.saxutils.SetCreateParserModules(['drv_libxml2'])

    def tearDown (self):
        pyxb.utils.saxutils.SetCreateParserModules(None)

    def __init__ (self, *args, **kw):
        self.SetUpClass()
        super(TestTrac_0139, self).__init__(*args, **kw)

    def __del__ (self, *args, **kw):
        self.TearDownClass()
        try:
            super(TestTrac_0139, self).__del__(*args, **kw)
        except AttributeError:
            pass

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
        if sys.version_info[:2] == (2, 7):
            self.assertRaises(xml.sax.SAXParseException, CreateFromDocument, xmls)
        else:
            instance = CreateFromDocument(xmls)
            self.assertEqual(self.ascii, instance)

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
        if self.have_libxml2:
            # ERROR: This should be fine, see trac/147
            #instance = CreateFromDocument(xmls)
            #self.assertEqual(self.nihongo, instance)
            self.assertRaises(UnicodeEncodeError, CreateFromDocument, xmls)

    def testNihongo_libxml2_file (self):
        self.useLibXML2Parser();
        if self.have_libxml2:
            xmls = file(self.path_nihongo).read()
            instance = CreateFromDocument(xmls)
            self.assertEqual(self.nihongo, instance)

    def testASCII_stringio (self):
        f = file(self.path_ascii).read();
        sio = StringIO.StringIO(self.ascii_xml).read()
        self.assertEqual(f, sio)

if __name__ == '__main__':
    unittest.main()
