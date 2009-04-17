import pywxsb.binding.generate
from xml.dom import minidom
from xml.dom import Node

import os.path
schema_path = '%s/../schemas/test-wildcard.xsd' % (os.path.dirname(__file__),)
code = pywxsb.binding.generate.GeneratePython(schema_file=schema_path)

rv = compile(code, 'test', 'exec')
eval(rv)

from pywxsb.exceptions_ import *

import unittest


def nc_not (ns_or_absent):
    return ( pywxsb.xmlschema.structures.Wildcard.NC_not, ns_or_absent )

class TestIntensionalSet (unittest.TestCase):

    def testTest (self):
        ns = 'URN:namespace'
        not_nc = nc_not(ns)
        self.assert_(isinstance(not_nc, tuple))
        self.assertEqual(2, len(not_nc))
        self.assertEqual(pywxsb.xmlschema.structures.Wildcard.NC_not, not_nc[0])
        self.assertEqual(ns, not_nc[1])

    def testUnion_1 (self):
        UNION = pywxsb.xmlschema.structures.Wildcard.IntensionalUnion
        nc_any = pywxsb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(nc_any, UNION([ nc_any, nc_any ]))
        self.assertEqual(nc_not(ns1), UNION([ nc_not(ns1), nc_not(ns1) ]))
        self.assertEqual(set([ns1]), UNION([ set([ns1]), set([ns1]) ]))

    def testUnion_2 (self):
        UNION = pywxsb.xmlschema.structures.Wildcard.IntensionalUnion
        nc_any = pywxsb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(nc_any, UNION([ nc_any, set([ns1]) ]))
        self.assertEqual(nc_any, UNION([ nc_any, nc_not(ns1) ]))
        self.assertEqual(nc_any, UNION([ nc_any, nc_not(None) ]))

    def testUnion_3 (self):
        UNION = pywxsb.xmlschema.structures.Wildcard.IntensionalUnion
        nc_any = pywxsb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(set([ns1, ns2]), UNION([set([ns1]), set([ns2])]))
        self.assertEqual(set([None, ns1]), UNION([set([None]), set([ns1])]))
        self.assertEqual(set([None]), UNION([set([None]), set([None])]))

    def testUnion_4 (self):
        UNION = pywxsb.xmlschema.structures.Wildcard.IntensionalUnion
        nc_any = pywxsb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(nc_not(None), UNION([nc_not(ns1), nc_not(ns2)]))
        self.assertEqual(nc_not(None), UNION([nc_not(ns1), nc_not(None)]))

    def testUnion_5 (self):
        UNION = pywxsb.xmlschema.structures.Wildcard.IntensionalUnion
        nc_any = pywxsb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(nc_any, UNION([nc_not(ns1), set([ns1, None])])) # 5.1
        self.assertEqual(nc_not(None), UNION([nc_not(ns1), set([ns1, ns2])])) # 5.2
        self.assertRaises(SchemaValidationError, UNION, [nc_not(ns1), set([None, ns2])]) # 5.3
        self.assertEqual(nc_not(ns1), UNION([nc_not(ns1), set([ns2])])) # 5.4

    def testUnion_6 (self):
        UNION = pywxsb.xmlschema.structures.Wildcard.IntensionalUnion
        nc_any = pywxsb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(nc_any, UNION([nc_not(None), set([ns1, ns2, None])])) # 6.1
        self.assertEqual(nc_not(None), UNION([nc_not(None), set([ns1, ns2])])) # 6.2

    def testIntersection_1 (self):
        ISECT = pywxsb.xmlschema.structures.Wildcard.IntensionalIntersection
        nc_any = pywxsb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(nc_any, ISECT([ nc_any, nc_any ]))
        self.assertEqual(nc_not(ns1), ISECT([ nc_not(ns1), nc_not(ns1) ]))
        self.assertEqual(set([ns1]), ISECT([ set([ns1]), set([ns1]) ]))

    def testIntersection_2 (self):
        ISECT = pywxsb.xmlschema.structures.Wildcard.IntensionalIntersection
        nc_any = pywxsb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(set([ns1]), ISECT([ nc_any, set([ns1]) ]))
        self.assertEqual(nc_not(ns1), ISECT([ nc_any, nc_not(ns1) ]))
        self.assertEqual(nc_not(None), ISECT([ nc_any, nc_not(None) ]))

    def testIntersection_3 (self):
        ISECT = pywxsb.xmlschema.structures.Wildcard.IntensionalIntersection
        nc_any = pywxsb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(set([ns2]), ISECT([nc_not(ns1), set([ns1, ns2, None])]))
        self.assertEqual(set([ns2]), ISECT([nc_not(ns1), set([ns1, ns2])]))
        self.assertEqual(set([ns2]), ISECT([nc_not(ns1), set([ns2])]))

    def testIntersection_4 (self):
        ISECT = pywxsb.xmlschema.structures.Wildcard.IntensionalIntersection
        nc_any = pywxsb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(set([ns2]), ISECT([set([ns1, ns2]), set([ns2, None])]))
        self.assertEqual(set([ns2, None]), ISECT([set([None, ns1, ns2]), set([ns2, None])]))
        self.assertEqual(set([]), ISECT([set([ns1]), set([ns2, None])]))
        self.assertEqual(set([]), ISECT([set([ns1]), set([ns2, ns1]), set([ns2, None])]))
        self.assertEqual(set([ns1]), ISECT([set([ns1, None]), set([None, ns2, ns1]), set([ns1, ns2])]))

    def testIntersection_5 (self):
        ISECT = pywxsb.xmlschema.structures.Wildcard.IntensionalIntersection
        nc_any = pywxsb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertRaises(SchemaValidationError, ISECT, [nc_not(ns1), nc_not(ns2)])

    def testIntersection_6 (self):
        ISECT = pywxsb.xmlschema.structures.Wildcard.IntensionalIntersection
        nc_any = pywxsb.xmlschema.structures.Wildcard.NC_any
        ns1 = 'URN:first'
        ns2 = 'URN:second'
        self.assertEqual(nc_not(ns1), ISECT([nc_not(ns1), nc_not(None)]))



class TestWildcard (unittest.TestCase):
    def testElement (self):
        xml = '<wrapper><first/><second/><third/></wrapper>'
        doc = minidom.parseString(xml)
        instance = wrapper.CreateFromDOM(doc.documentElement)

    def testAttribute (self):
        xml = '<wrapper myattr="true" auxattr="somevalue"/>'
        doc = minidom.parseString(xml)
        instance = wrapper.CreateFromDOM(doc.documentElement)

if __name__ == '__main__':
    unittest.main()
    
        
