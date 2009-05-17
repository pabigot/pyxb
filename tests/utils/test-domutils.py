import unittest
from pyxb.utils.domutils import *
from xml.dom import minidom
from xml.dom import Node
import xml.dom
import pyxb.Namespace

class TestInScopeNames (unittest.TestCase):
    def show (self, node):
        xmlns_map = pyxb.Namespace.NamespaceContext.GetNodeContext(node).inScopeNamespaces()
        #print '%s xmlns map %s' % (node.nodeName, GetInScopeNamespaces(node))
        return xmlns_map

    def test_6_2_2 (self):
        xml = '''<?xml version="1.0"?>
<!-- initially, the default namespace is "books" -->
<book xmlns='urn:loc.gov:books'
      xmlns:isbn='urn:ISBN:0-395-36341-6'>
    <title>Cheaper by the Dozen</title>
    <isbn:number>1568491379</isbn:number>
    <notes>
      <!-- make HTML the default namespace for some commentary -->
      <p xmlns='http://www.w3.org/1999/xhtml'>
          This is a <i>funny</i> book!
      </p>
      <p>another graf without namespace change</p>
    </notes>
</book>'''
        book = minidom.parseString(xml).documentElement
        self.assertEqual('book', book.localName)
        ns_ctx = pyxb.Namespace.NamespaceContext(book)
        xmlns_map = self.show(book)
        self.assertEqual(4, len(xmlns_map))
        self.assertEqual('http://www.w3.org/2001/XMLSchema-instance', xmlns_map['xsi'].uri())
        self.assertEqual('http://www.w3.org/XML/1998/namespace', xmlns_map['xml'].uri())
        self.assertEqual('urn:loc.gov:books', xmlns_map[None].uri())
        self.assertEqual('urn:ISBN:0-395-36341-6', xmlns_map['isbn'].uri())
        title = book.firstChild.nextSibling
        self.assertEqual('title', title.localName)
        xmlns_map =self.show(title)
        self.assertEqual(4, len(xmlns_map))
        self.assertEqual('http://www.w3.org/2001/XMLSchema-instance', xmlns_map['xsi'].uri())
        self.assertEqual('http://www.w3.org/XML/1998/namespace', xmlns_map['xml'].uri())
        self.assertEqual('urn:loc.gov:books', xmlns_map[None].uri())
        self.assertEqual('urn:ISBN:0-395-36341-6', xmlns_map['isbn'].uri())
        p = title.nextSibling.nextSibling.nextSibling.nextSibling.firstChild.nextSibling.nextSibling.nextSibling
        xmlns_map = self.show(p)
        self.assertEqual('p', p.localName)
        self.assertEqual(4, len(xmlns_map))
        self.assertEqual('http://www.w3.org/2001/XMLSchema-instance', xmlns_map['xsi'].uri())
        self.assertEqual('http://www.w3.org/XML/1998/namespace', xmlns_map['xml'].uri())
        self.assertEqual('http://www.w3.org/1999/xhtml', xmlns_map[None].uri())
        self.assertEqual('urn:ISBN:0-395-36341-6', xmlns_map['isbn'].uri())
        x = p.nextSibling.nextSibling
        xmlns_map = self.show(x)
        self.assertEqual('p', x.localName)
        self.assertEqual(4, len(xmlns_map))
        self.assertEqual('http://www.w3.org/2001/XMLSchema-instance', xmlns_map['xsi'].uri())
        self.assertEqual('http://www.w3.org/XML/1998/namespace', xmlns_map['xml'].uri())
        self.assertEqual('urn:loc.gov:books', xmlns_map[None].uri())
        self.assertEqual('urn:ISBN:0-395-36341-6', xmlns_map['isbn'].uri())


    def test_6_2_3 (self):
        xml = '''<?xml version='1.0'?>
<Beers>
  <!-- the default namespace inside tables is that of HTML -->
  <table xmlns='http://www.w3.org/1999/xhtml'>
   <th><td>Name</td><td>Origin</td><td>Description</td></th>
   <tr> 
     <!-- no default namespace inside table cells -->
     <td><brandName xmlns="">Huntsman</brandName></td>
     <td><origin xmlns="">Bath, UK</origin></td>
     <td>
       <details xmlns=""><class>Bitter</class><hop>Fuggles</hop>
         <pro>Wonderful hop, light alcohol, good summer beer</pro>
         <con>Fragile; excessive variance pub to pub</con>
         </details>
        </td>
      </tr>
    </table>
  </Beers>'''
        Beers = minidom.parseString(xml).documentElement
        ns_ctx = pyxb.Namespace.NamespaceContext(Beers)
        xmlns_map = self.show(Beers)
        self.assertEqual(2, len(xmlns_map))
        self.assertEqual('http://www.w3.org/2001/XMLSchema-instance', xmlns_map['xsi'].uri())
        self.assertEqual('http://www.w3.org/XML/1998/namespace', xmlns_map['xml'].uri())
        table = Beers.firstChild.nextSibling.nextSibling.nextSibling
        self.assertEqual('table', table.localName)
        xmlns_map = self.show(table)
        self.assertEqual(3, len(xmlns_map))
        self.assertEqual('http://www.w3.org/2001/XMLSchema-instance', xmlns_map['xsi'].uri())
        self.assertEqual('http://www.w3.org/XML/1998/namespace', xmlns_map['xml'].uri())
        self.assertEqual('http://www.w3.org/1999/xhtml', xmlns_map[None].uri())
        brandName = table.firstChild.nextSibling.nextSibling.nextSibling.firstChild.nextSibling.nextSibling.nextSibling.firstChild
        self.assertEqual('brandName', brandName.localName)
        xmlns_map = self.show(brandName)
        self.assertEqual(2, len(xmlns_map))
        self.assertEqual('http://www.w3.org/2001/XMLSchema-instance', xmlns_map['xsi'].uri())
        self.assertEqual('http://www.w3.org/XML/1998/namespace', xmlns_map['xml'].uri())


class TestNamespaceURIs (unittest.TestCase):
    # Make sure we agree with xml.dom on what the core namespace URIs are
    def testURI (self):
        self.assertEqual(xml.dom.XML_NAMESPACE, pyxb.Namespace.XML.uri())
        self.assertEqual(xml.dom.XMLNS_NAMESPACE, pyxb.Namespace.XMLNamespaces.uri())
        self.assertEqual(xml.dom.XHTML_NAMESPACE, pyxb.Namespace.XHTML.uri())

if '__main__' == __name__:
    unittest.main()
    
