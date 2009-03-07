"""Utility functions and classes."""

import re

# Define the characters to be escaped, which is everything that we don't
# want to keep as its literal form."
_EscapedChars = r"[^-.~!@#$%^&*()_+={}\[\]|:;<>,?/'a-zA-Z0-9]"
_SpecialEscapes = { "\n" : r'\n'
                  , "\t" : r'\t'
                  }

_Escape_re = re.compile(_EscapedChars, re.UNICODE)
_ASCII_fn = lambda _c: _SpecialEscapes.get(_c.group()[0], r'\x%02x' % ord(_c.group()[0]))
#_ASCII_fn = lambda _c:  r'\x%02x' % ord(_c.group()[0])
_Unicode_fn = lambda _c: r'\u%04x' % ord(_c.group()[0])

def QuotedEscaped (s):
    """Convert a string into a literal value that can be used in Python source.

    The string can be ASCII or unicode.  Most printable characters are
    retained; non-printables are escaped."""
    if isinstance(s, unicode):
        return 'u"%s"' % (_Escape_re.sub(_Unicode_fn, s),)
    return '"%s"' % (_Escape_re.sub(_ASCII_fn, s),)

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
        
        cases = ( ( r'"1\x042"', "1\0042" )
                , ( r'"1\x222&3"', '1"2&3' )
                , ( r'"one' + "'" + r'two"', "one'two" )
                , ( r'"1\n2"', "1\n2" )
                , ( r'u"1\u00042"', u"1\0042" )
                , ( r'u"1\u00222&3"', u'1"2&3' )
                , ( r'u"one' + "'" + r'two"', u"one'two" )
                  )

        def testQuotedEscape (self):
            for ( expected, input ) in self.cases:
                result = QuotedEscaped(input)
                self.assertEquals(expected, result)
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
    
