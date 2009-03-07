"""Utility functions and classes."""

import re

# Define the characters to be escaped, which is everything that we don't
# want to keep as its literal form."
_EscapedChars = r"[^-.~!@#$%^&*()_+={}\[\]|:;<>,?/'a-zA-Z0-9]"
_SpecialEscapes = { "\n" : r'\n' }

_Escape_re = re.compile(_EscapedChars, re.UNICODE)
#_ASCII_fn = lambda _c: _SpecialEscapes.get(_c.group()[0], r'\x%02x' % ord(_c.group()[0]))
_ASCII_fn = lambda _c:  r'\x%02x' % ord(_c.group()[0])
_Unicode_fn = lambda _c: r'\u%04x' % ord(_c.group()[0])

def QuotedEscaped (s):
    """Convert a string into a literal value that can be used in Python source.

    The string can be ASCII or unicode.  Most printable characters are
    retained; non-printables are escaped."""
    if isinstance(s, unicode):
        return 'u"%s"' % (_Escape_re.sub(_Unicode_fn, s),)
    return '"%s"' % (_Escape_re.sub(_ASCII_fn, s),)

if '__main__' == __name__:
    import unittest

    class BasicTest (unittest.TestCase):
        
        cases = ( ( r'"1\x042"', "1\0042" )
                , ( r'"1\x222&3"', '1"2&3' )
                , ( r'"one' + "'" + r'two"', "one'two" )
                , ( r'"1\0d2"', "1\n2" )
                , ( r'u"1\u00042"', u"1\0042" )
                , ( r'u"1\u00222&3"', u'1"2&3' )
                , ( r'u"one' + "'" + r'two"', u"one'two" )
                  )

        def testStuff (self):
            self.assertEquals(r'"1\x042"', QuotedEscaped("1\0042"))
            self.assertEquals(r'"1\x222&3"', QuotedEscaped('1"2&3'))
            self.assertEquals(r'"one' + "'" + r'two"', QuotedEscaped("one'two"))
            #self.assertEquals(r'"1\0d2"', QuotedEscaped("1\n2"))
            self.assertEquals(r'u"1\u00042"', QuotedEscaped(u"1\0042"))
            self.assertEquals(r'u"1\u00222&3"', QuotedEscaped(u'1"2&3'))
            self.assertEquals(r'u"one' + "'" + r'two"', QuotedEscaped(u"one'two"))

    unittest.main()
    
