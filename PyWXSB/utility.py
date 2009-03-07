"""Utility functions and classes."""

import re

def QuotedEscaped (s):
    """Convert a string into a literal value that can be used in Python source.

    This just calls repr.  No point in getting all complex when the language
    already gives us what we need.
    """
    return repr(s)

_UnderscoreSubstitute_re = re.compile(r'[- .]')
_NonIdentifier_re = re.compile(r'[^a-zA-Z0-9_]')
_PrefixUnderscore_re = re.compile(r'^_+')

def MakeIdentifier (s):
    """Convert a string into something suitable to be a Python identifier.

    The string is converted to unicode; spaces and periods replaced by
    underscores; non-printables stripped.  Furthermore, any leading
    underscores are removed.  No check is made for conflicts with
    keywords.
    """
    return _PrefixUnderscore_re.sub('', _NonIdentifier_re.sub('',_UnderscoreSubstitute_re.sub('_', str(s))))

_Keywords = frozenset( ( "and", "del", "from", "not", "while", "as", "elif", "global",
              "or", "with", "assert", "else", "if", "pass", "yield",
              "break", "except", "import", "print", "class", "exec",
              "in", "raise", "continue", "finally", "is", "return",
              "def", "for", "lambda", "try" ) )
def DeconflictKeyword (s):
    """If the provide string matches a keyword, append an underscore to distinguish them."""
    if s in _Keywords:
        return '%s_' % (s,)
    return s

def MakeUnique (s, in_use):
    """Return an identifier based on s that is not in the given set.

    in_use must be an instance of set().  in_use is updated to contain
    the returned identifier.  The returned identifier is made unique
    by appending an underscore and, if necessary, a serial number.
    """
    if s in in_use:
        candidate = '%s_' % (s,)
        ctr = 2
        while candidate in in_use:
            candidate = '%s_%d' % (s, ctr)
            ctr += 1
        s = candidate
    in_use.add(s)
    return s

if '__main__' == __name__:
    import unittest

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

    unittest.main()
    
