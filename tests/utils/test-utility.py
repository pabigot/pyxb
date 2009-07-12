import unittest
from pyxb.utils.utility import *
from pyxb.utils.utility import _DeconflictSymbols_mixin

class DST_base (_DeconflictSymbols_mixin):
    _ReservedSymbols = set([ 'one', 'two' ])

class DST_sub (DST_base):
    _ReservedSymbols = DST_base._ReservedSymbols.union(set([ 'three' ]))

class DeconfictSymbolsTtest (unittest.TestCase):
    def testDeconflict (self):
        self.assertEquals(2, len(DST_base._ReservedSymbols))
        self.assertEquals(3, len(DST_sub._ReservedSymbols))

class BasicTest (unittest.TestCase):
    
    cases = ( ( r'"1\x042"', "1\0042" ) # expanded octal
            , ( r'"1\x042"', '1\0042' ) # expanded octal (single quotes do not affect escaping)
            , ( "r'1\\0042'", r'1\0042' ) # preserve unexpanded octal
            , ( r'"1\x222&3"', '1"2&3' )  # escape double quotes
            , ( '"one\'two"', "one'two" ) # preserve single quote
            , ( r'"1\n2"', "1\n2" )       # expanded newline to escape sequence
            , ( "r'1\\n2'", r'1\n2' )     # raw backslash preserved
            , ( "\"1'\\n'2\"", "1'\n'2" ) # expanded newline to escape sequence
            , ( "\"1'\\n'2\"", '1\'\n\'2' ) # expanded newline to escape sequence (single quotes)
            , ( "\"1\\x22\\n\\x222\"", '1"\n"2' ) # escape double quotes around expanded newline
            , ( "r'1\\'\\n\\'2'", r'1\'\n\'2' )   # preserve escaped quote and newline
            , ( r'u"1\u00042"', u"1\0042" )       # unicode expanded octal
            , ( r'u"1\u00222&3"', u'1"2&3' )      # unicode escape double quotes
            , ( r'u"one' + "'" + r'two"', u"one'two" ) # unicode embedded single quote
            , ( "r'\\i\\c*'", r'\i\c*' )               # backslashes as in patterns
            , ( u'u"0"', u'\u0030' )                   # expanded unicode works
            , ( u'u"\\u0022"', u'"' )      # unicode double quotes are escaped
            , ( u'u"\\u0022"', u'\u0022' ) # single quotes don't change that expanded unicode works
            , ( u'u"\\u0022"', ur'\u0022' ) # raw has no effect on unicode escapes
            , ( u"u\"'\"", u"'" )           # unicode single quote works
            , ( u"u\"\\u00220\\u0022\"", u'"\u0030"' ) # unicode with double quotes works
            )
            

    def testPrepareIdentifier (self):
        in_use = set()
        self.assertEquals('id', PrepareIdentifier('id', in_use))
        self.assertEquals('id_', PrepareIdentifier('id', in_use))
        self.assertEquals('id_2', PrepareIdentifier('id_', in_use))
        self.assertEquals('id_3', PrepareIdentifier('id____', in_use))
        self.assertEquals('_id', PrepareIdentifier('id', in_use, protected=True))
        self.assertEquals('_id_', PrepareIdentifier('id', in_use, protected=True))
        self.assertEquals('__id', PrepareIdentifier('id', in_use, private=True))
        self.assertEquals('__id_', PrepareIdentifier('id', in_use, private=True))

        reserved = frozenset([ 'Factory' ])
        in_use = set()
        self.assertEquals('Factory_', PrepareIdentifier('Factory', in_use, reserved))
        self.assertEquals('Factory_2', PrepareIdentifier('Factory', in_use, reserved))
        self.assertEquals('Factory_3', PrepareIdentifier('Factory', in_use, reserved))

        in_use = set()
        self.assertEquals('global_', PrepareIdentifier('global', in_use))
        self.assertEquals('global_2', PrepareIdentifier('global', in_use))
        self.assertEquals('global_3', PrepareIdentifier('global', in_use))

        in_use = set()
        self.assertEquals('n24_hours', PrepareIdentifier('24 hours', in_use))

    def testQuotedEscape (self):
        for ( expected, input ) in self.cases:
            result = QuotedEscaped(input)
            # Given "expected" value may not be correct.  Don't care as
            # long as the evalution produces the input.
            #self.assertEquals(expected, result)
            self.assertEquals(input, eval(result))

    def testMakeIdentifier (self):
        self.assertEquals('id', MakeIdentifier('id'))
        self.assertEquals('id', MakeIdentifier(u'id'))
        self.assertEquals('id_sep', MakeIdentifier(u'id_sep'))
        self.assertEquals('id_sep', MakeIdentifier(u'id sep'))
        self.assertEquals('id_sep_too', MakeIdentifier(u'id-sep too'))
        self.assertEquals('idid', MakeIdentifier(u'id&id'))
        self.assertEquals('id', MakeIdentifier('_id'))
        self.assertEquals('id_', MakeIdentifier('_id_'))
        self.assertEquals('emptyString', MakeIdentifier(''))
        self.assertEquals('emptyString', MakeIdentifier('_'))

    def testDeconflictKeyword (self):
        self.assertEquals('id', DeconflictKeyword('id'))
        self.assertEquals('for_', DeconflictKeyword('for'))

    def testMakeUnique (self):
        in_use = set()
        self.assertEquals('id', MakeUnique('id', in_use))
        self.assertEquals(1, len(in_use))
        self.assertEquals('id_', MakeUnique('id', in_use))
        self.assertEquals(2, len(in_use))
        self.assertEquals('id_2', MakeUnique('id', in_use))
        self.assertEquals(3, len(in_use))
        self.assertEquals(set(( 'id', 'id_', 'id_2' )), in_use)

class TestGraph (unittest.TestCase):

    _Edges = [
        (1, 2),
        (2, 3),
        (2, 4),
        (4, 8),
        (5, 6),
        (5, 7),
        (6, 10),
        (7, 8),
        (8, 5),
        (8, 9),
        (9, 10),
        (10, 0)
        ]

    def testRoot (self):
        graph = Graph()
        [ graph.addEdge(*_e) for _e in self._Edges ]
        roots = graph.roots().copy()
        self.assertEquals(1, len(roots))
        self.assertEquals(1, roots.pop())

    def testTarjan (self):
        graph = Graph()
        [ graph.addEdge(*_e) for _e in self._Edges ]
        scc = graph.scc()
        self.assertEquals(1, len(scc))
        self.assertEquals(set([5, 7, 8]), set(scc[0]))

    def testDFSOrder1 (self):
        graph = Graph()
        [ graph.addEdge(*_e) for _e in self._Edges ]
        order = graph.dfsOrder()
        self.assertTrue(isinstance(order, list))
        self.assertEqual(len(graph.nodes()), len(order))
        walked = set()
        for source in order:
            for target in graph.edgeMap().get(source, []):
                self.assertTrue((target in walked) or (graph.sccForNode(source) == graph.sccForNode(target)), '%s -> %s not satisfied, seen' % (source, target))
            walked.add(source)
        order = graph.sccOrder()
        self.assertEqual(len(graph.nodes()), len(order) + 2)
        walked = set()
        for source in order:
            if isinstance(source, list):
                walked.update(source)
                continue
            for target in graph.edgeMap().get(source, []):
                self.assertTrue((target in walked) or (graph.sccForNode(source) == graph.sccForNode(target)), '%s -> %s not satisfied, seen' % (source, target))
            walked.add(source)

    def testDFSOrder2 (self):
        graph = Graph()
        graph.addEdge(2, 2)
        graph.addEdge(2, 1)
        graph.addNode(3)
        order = graph.dfsOrder()
        self.assertTrue(isinstance(order, list))
        self.assertEqual(len(graph.nodes()), len(order))
        walked = set()
        for source in order:
            for target in graph.edgeMap().get(source, []):
                self.assertTrue((target in walked) or (graph.sccForNode(source) == graph.sccForNode(target)), '%s -> %s not satisfied, seen' % (source, target))
            walked.add(source)

    def testDFSOrder_Loop (self):
        graph = Graph()
        graph.addEdge(1, 2)
        graph.addEdge(2, 3)
        graph.addEdge(3, 1)
        self.assertEqual(0, len(graph.roots()))
        self.assertRaises(Exception, graph.dfsOrder)
        graph.addRoot(1)
        self.assertEqual(1, len(graph.roots()))
        scc = graph.scc()
        self.assertEqual(1, len(scc))
        self.assertEqual(set([1, 2, 3]), set(scc[0]))

    def testDFSOrder4 (self):
        graph = Graph()
        graph.addEdge('gmd.applicationSchema', 'gco.basicTypes')
        graph.addEdge('gmd.applicationSchema', 'gmd.applicationSchema')
        graph.addEdge('gmd.applicationSchema', 'xlink.xlinks')
        graph.addEdge('gmd.applicationSchema', 'gco.gcoBase')
        graph.addEdge('gmd.applicationSchema', 'gmd.citation')
        graph.addEdge('gmd.applicationSchema', 'gml.basicTypes')
        graph.addEdge('gmd.portrayalCatalogue', 'gco.gcoBase')
        graph.addEdge('gmd.portrayalCatalogue', 'gmd.portrayalCatalogue')
        graph.addEdge('gmd.portrayalCatalogue', 'gmd.citation')
        graph.addEdge('gmd.portrayalCatalogue', 'xlink.xlinks')
        graph.addEdge('gmd.portrayalCatalogue', 'gml.basicTypes')
        graph.addEdge('gmd.freeText', 'gmd.freeText')
        graph.addEdge('gmd.freeText', 'gco.gcoBase')
        graph.addEdge('gmd.freeText', 'gco.basicTypes')
        graph.addEdge('gmd.freeText', 'gmd.citation')
        graph.addEdge('gmd.freeText', 'gmd.identification')
        graph.addEdge('gmd.freeText', 'gml.basicTypes')
        graph.addEdge('gmd.freeText', 'xlink.xlinks')
        graph.addEdge('gmd.dataQuality', 'gco.basicTypes')
        graph.addEdge('gmd.dataQuality', 'xlink.xlinks')
        graph.addEdge('gmd.dataQuality', 'gco.gcoBase')
        graph.addEdge('gmd.dataQuality', 'gmd.referenceSystem')
        graph.addEdge('gmd.dataQuality', 'gmd.maintenance')
        graph.addEdge('gmd.dataQuality', 'gmd.extent')
        graph.addEdge('gmd.dataQuality', 'gmd.citation')
        graph.addEdge('gmd.dataQuality', 'gmd.identification')
        graph.addEdge('gmd.dataQuality', 'gml.basicTypes')
        graph.addEdge('gmd.dataQuality', 'gmd.dataQuality')
        graph.addEdge('gmd.metadataApplication', 'gml.basicTypes')
        graph.addEdge('gmd.metadataApplication', 'gco.gcoBase')
        graph.addEdge('gmd.metadataApplication', 'gmd.metadataEntity')
        graph.addEdge('gmd.metadataApplication', 'gmd.metadataApplication')
        graph.addEdge('gmd.metadataApplication', 'xlink.xlinks')
        graph.addEdge('gmd.spatialRepresentation', 'gco.gcoBase')
        graph.addEdge('gmd.spatialRepresentation', 'gss.geometry')
        graph.addEdge('gmd.spatialRepresentation', 'gml.basicTypes')
        graph.addEdge('gmd.spatialRepresentation', 'gco.basicTypes')
        graph.addEdge('gmd.spatialRepresentation', 'gmd.citation')
        graph.addEdge('gmd.spatialRepresentation', 'xlink.xlinks')
        graph.addEdge('gmd.spatialRepresentation', 'gmd.spatialRepresentation')
        graph.addEdge('gmd.extent', 'gco.basicTypes')
        graph.addEdge('gmd.extent', 'gts.temporalObjects')
        graph.addEdge('gmd.extent', 'gco.gcoBase')
        graph.addEdge('gmd.extent', 'gmd.extent')
        graph.addEdge('gmd.extent', 'gml.basicTypes')
        graph.addEdge('gmd.extent', 'gmd.referenceSystem')
        graph.addEdge('gmd.extent', 'xlink.xlinks')
        graph.addEdge('gmd.extent', 'gss.geometry')
        graph.addEdge('gmd.extent', 'gsr.spatialReferencing')
        graph.addEdge('gmd.distribution', 'gmd.distribution')
        graph.addEdge('gmd.distribution', 'gml.basicTypes')
        graph.addEdge('gmd.distribution', 'gco.gcoBase')
        graph.addEdge('gmd.distribution', 'gco.basicTypes')
        graph.addEdge('gmd.distribution', 'gmd.citation')
        graph.addEdge('gmd.distribution', 'xlink.xlinks')
        graph.addEdge('gmd.metadataExtension', 'gml.basicTypes')
        graph.addEdge('gmd.metadataExtension', 'gco.gcoBase')
        graph.addEdge('gmd.metadataExtension', 'gco.basicTypes')
        graph.addEdge('gmd.metadataExtension', 'gmd.metadataExtension')
        graph.addEdge('gmd.metadataExtension', 'gmd.citation')
        graph.addEdge('gmd.metadataExtension', 'xlink.xlinks')
        graph.addEdge('gmd.maintenance', 'gts.temporalObjects')
        graph.addEdge('gmd.maintenance', 'gco.gcoBase')
        graph.addEdge('gmd.maintenance', 'gmd.maintenance')
        graph.addEdge('gmd.maintenance', 'gco.basicTypes')
        graph.addEdge('gmd.maintenance', 'gmd.citation')
        graph.addEdge('gmd.maintenance', 'gml.basicTypes')
        graph.addEdge('gmd.maintenance', 'xlink.xlinks')
        graph.addEdge('gmd.identification', 'gco.basicTypes')
        graph.addEdge('gmd.identification', 'xlink.xlinks')
        graph.addEdge('gmd.identification', 'gco.gcoBase')
        graph.addEdge('gmd.identification', 'gmd.referenceSystem')
        graph.addEdge('gmd.identification', 'gmd.maintenance')
        graph.addEdge('gmd.identification', 'gmd.extent')
        graph.addEdge('gmd.identification', 'gmd.distribution')
        graph.addEdge('gmd.identification', 'gmd.citation')
        graph.addEdge('gmd.identification', 'gmd.identification')
        graph.addEdge('gmd.identification', 'gml.basicTypes')
        graph.addEdge('gmd.identification', 'gmd.constraints')
        graph.addEdge('gmd.metadataEntity', 'gmd.content')
        graph.addEdge('gmd.metadataEntity', 'gco.basicTypes')
        graph.addEdge('gmd.metadataEntity', 'gmd.portrayalCatalogue')
        graph.addEdge('gmd.metadataEntity', 'gmd.metadataApplication')
        graph.addEdge('gmd.metadataEntity', 'gco.gcoBase')
        graph.addEdge('gmd.metadataEntity', 'gml.basicTypes')
        graph.addEdge('gmd.metadataEntity', 'gmd.applicationSchema')
        graph.addEdge('gmd.metadataEntity', 'gmd.metadataEntity')
        graph.addEdge('gmd.metadataEntity', 'gmd.referenceSystem')
        graph.addEdge('gmd.metadataEntity', 'gmd.maintenance')
        graph.addEdge('gmd.metadataEntity', 'gmd.metadataExtension')
        graph.addEdge('gmd.metadataEntity', 'gmd.distribution')
        graph.addEdge('gmd.metadataEntity', 'gmd.freeText')
        graph.addEdge('gmd.metadataEntity', 'gmd.identification')
        graph.addEdge('gmd.metadataEntity', 'gmd.constraints')
        graph.addEdge('gmd.metadataEntity', 'xlink.xlinks')
        graph.addEdge('gmd.metadataEntity', 'gmd.citation')
        graph.addEdge('gmd.metadataEntity', 'gmd.dataQuality')
        graph.addEdge('gmd.metadataEntity', 'gmd.spatialRepresentation')
        graph.addEdge('gmd.constraints', 'gco.gcoBase')
        graph.addEdge('gmd.constraints', 'gco.basicTypes')
        graph.addEdge('gmd.constraints', 'gmd.constraints')
        graph.addEdge('gmd.constraints', 'xlink.xlinks')
        graph.addEdge('gmd.constraints', 'gml.basicTypes')
        graph.addEdge('gmd.content', 'gmd.content')
        graph.addEdge('gmd.content', 'gco.basicTypes')
        graph.addEdge('gmd.content', 'xlink.xlinks')
        graph.addEdge('gmd.content', 'gco.gcoBase')
        graph.addEdge('gmd.content', 'gmd.referenceSystem')
        graph.addEdge('gmd.content', 'gmd.citation')
        graph.addEdge('gmd.content', 'gml.basicTypes')
        graph.addEdge('gmd.referenceSystem', 'gco.gcoBase')
        graph.addEdge('gmd.referenceSystem', 'gco.basicTypes')
        graph.addEdge('gmd.referenceSystem', 'gmd.referenceSystem')
        graph.addEdge('gmd.referenceSystem', 'gmd.extent')
        graph.addEdge('gmd.referenceSystem', 'gmd.citation')
        graph.addEdge('gmd.referenceSystem', 'gml.basicTypes')
        graph.addEdge('gmd.referenceSystem', 'xlink.xlinks')
        graph.addEdge('gmd.citation', 'gco.gcoBase')
        graph.addEdge('gmd.citation', 'gml.basicTypes')
        graph.addEdge('gmd.citation', 'gco.basicTypes')
        graph.addEdge('gmd.citation', 'gmd.referenceSystem')
        graph.addEdge('gmd.citation', 'gmd.citation')
        graph.addEdge('gmd.citation', 'xlink.xlinks')

        self.assertEqual(23, len(graph.nodes()))
        self.assertEqual(123, len(graph.edges()))
        self.assertRaises(Exception, graph.dfsOrder)
        
    def testDFSOrder5 (self):
        graph = Graph()
        graph.addEdge(1, 2)
        graph.addEdge(1, 3)
        graph.addEdge(3, 4)
        graph.addEdge(3, 5)
        graph.addEdge(5, 1)
        graph.addEdge(5, 6)
        graph.addEdge(6, 2)
        self.assertRaises(Exception, graph.scc)
        self.assertRaises(Exception, graph.dfsOrder)
        graph.addRoot(1)
        order = graph.sccOrder(reset=True)
        self.assertEqual(4, len(order))
        self.assertEqual(1, len(graph.scc()))
        self.assertEqual(set([1, 3, 5]), set(graph.scc()[0]))

class TestConstrainedSequence (unittest.TestCase):

    def testCTOR (self):
        x = ConstrainedSequence(member_type=int)
        self.assertEquals(0, len(x))
        x = ConstrainedSequence([0,1,2], member_type=int)
        self.assertEquals(3, len(x))
        self.assertEquals(1, x[1])
        x = ConstrainedSequence([0.3,"1",long(2)], member_type=int)
        self.assertEquals(3, len(x))
        self.assertEquals(0, x[0])
        self.assertEquals(1, x[1])
        self.assertEquals(2, x[2])
        self.assert_(reduce(lambda _l,_r: _l and isinstance(_r, x.memberType()), x, True))
        
    def testAppend (self):
        x = ConstrainedSequence(member_type=int)
        x.append(2)
        self.assertEqual(2, x[-1])
        x.append("4")
        self.assertEqual(4, x[-1])
        x.append(5L)
        self.assertEqual(5, x[-1])
        self.assert_(reduce(lambda _l,_r: _l and isinstance(_r, x.memberType()), x, True))

    def testSet (self):
        x = ConstrainedSequence([0.3, "1", 2L], member_type=int)
        self.assertEquals(3, len(x))
        self.assertEquals(0, x[0])
        self.assertEquals(1, x[1])
        self.assertEquals(2, x[2])
        self.assert_(reduce(lambda _l,_r: _l and isinstance(_r, x.memberType()), x, True))
        x[1] = '432'
        self.assertEquals(432, x[1])
        x[0:2] = [ '67' ]
        self.assertEquals(2, len(x))
        self.assertEquals(67, x[0])
        self.assertEquals(2, x[1])
        self.assert_(reduce(lambda _l,_r: _l and isinstance(_r, x.memberType()), x, True))

    def testTuple (self):
        x = ConstrainedSequence((1, '2', 3L), member_type=int, sequence_type=tuple)
        self.assertEqual(3, len(x))
        self.assert_(reduce(lambda _l,_r: _l and isinstance(_r, x.memberType()), x, True))
        self.assertEqual(hash(x), hash((1,2,3)))

    def testCount (self):
        x = ConstrainedSequence([0.3, '1', 2L, 1.1, 1L], member_type=int)
        self.assertEqual(5, len(x))
        self.assertEqual(3, x.count(1))
        self.assertEqual(3, x.count("1"))

    def testIndex (self):
        x = ConstrainedSequence([0.3, '1', 2L, 1.1, 1L], member_type=int)
        self.assertEqual(1, x.index('1'))

    def testMembership (self):
        x = ConstrainedSequence([0.3, '1', 2L, 1.1, 1L], member_type=int)
        self.assert_("2" in x)

    def testExtrema (self):
        x = ConstrainedSequence([0.3, '1', 2L, 1.1, 1L], member_type=int)
        self.assertEqual(0, min(x))
        self.assertEqual(2, max(x))

    def testSort (self):
        x = ConstrainedSequence([0.3, '-10', 2L, 1.1, 1L], member_type=int)
        x.sort()
        self.assertEqual([-10, 0, 1, 1, 2], x)
        y = ConstrainedSequence([-10L, "0", 1.1, 1, "2"], member_type=int)
        self.assertEqual(y, x)

if '__main__' == __name__:
    unittest.main()
            
        
