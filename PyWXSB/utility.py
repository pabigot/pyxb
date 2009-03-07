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
    underscores; non-printables stripped; and any leading underscores
    removed.  No check for conflicts with keywords is made.
    """
    return _PrefixUnderscore_re.sub('', _NonIdentifier_re.sub('',_UnderscoreSubstitute_re.sub('_', str(s))))

def TransformKeywords (s):
    pass

def MakeUnique (s, in_use):
    pass


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

    unittest.main()
    
