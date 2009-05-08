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
        self.assertEquals('Factory__', PrepareIdentifier('Factory', in_use, reserved))
        self.assertEquals('Factory__2', PrepareIdentifier('Factory', in_use, reserved))

        in_use = set()
        self.assertEquals('global_', PrepareIdentifier('global', in_use))
        self.assertEquals('global__', PrepareIdentifier('global', in_use))
        self.assertEquals('global__2', PrepareIdentifier('global', in_use))

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

if '__main__' == __name__:
    unittest.main()
    
