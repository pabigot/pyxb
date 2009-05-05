import unittest
from pyxb.utils.domutils import *
from xml.dom import minidom
from xml.dom import Node

class TestInScopeNames (unittest.TestCase):
    def show (self, node):
        xmlns_map = GetInScopeNamespaces(node)
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
    </notes>
</book>'''
        book = minidom.parseString(xml).documentElement
        self.assertEqual('book', book.localName)
        SetInScopeNamespaces(book)
        xmlns_map = self.show(book)
        self.assertEqual(2, len(xmlns_map))
        self.assertEqual('urn:loc.gov:books', xmlns_map[None])
        self.assertEqual('urn:ISBN:0-395-36341-6', xmlns_map['isbn'])
        title = book.firstChild.nextSibling
        self.assertEqual('title', title.localName)
        xmlns_map =self.show(title)
        self.assertEqual(2, len(xmlns_map))
        self.assertEqual('urn:loc.gov:books', xmlns_map[None])
        self.assertEqual('urn:ISBN:0-395-36341-6', xmlns_map['isbn'])
        p = title.nextSibling.nextSibling.nextSibling.nextSibling.firstChild.nextSibling.nextSibling.nextSibling
        xmlns_map = self.show(p)
        self.assertEqual('p', p.localName)
        self.assertEqual(2, len(xmlns_map))
        self.assertEqual('http://www.w3.org/1999/xhtml', xmlns_map[None])
        self.assertEqual('urn:ISBN:0-395-36341-6', xmlns_map['isbn'])
        x = title.nextSibling.nextSibling.nextSibling.nextSibling.nextSibling
        xmlns_map = self.show(x)
        self.assertEqual(x.TEXT_NODE, x.nodeType)
        self.assertEqual(2, len(xmlns_map))
        self.assertEqual('urn:loc.gov:books', xmlns_map[None])
        self.assertEqual('urn:ISBN:0-395-36341-6', xmlns_map['isbn'])


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
        SetInScopeNamespaces(Beers)
        xmlns_map = self.show(Beers)
        self.assertEqual(0, len(xmlns_map))
        table = Beers.firstChild.nextSibling.nextSibling.nextSibling
        self.assertEqual('table', table.localName)
        xmlns_map = self.show(table)
        self.assertEqual(1, len(xmlns_map))
        self.assertEqual('http://www.w3.org/1999/xhtml', xmlns_map[None])
        brandName = table.firstChild.nextSibling.nextSibling.nextSibling.firstChild.nextSibling.nextSibling.nextSibling.firstChild
        self.assertEqual('brandName', brandName.localName)
        xmlns_map = self.show(brandName)
        self.assertEqual(0, len(xmlns_map))


if '__main__' == __name__:
    unittest.main()
    
