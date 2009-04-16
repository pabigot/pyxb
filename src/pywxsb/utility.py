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
def DeconflictKeyword (s, aux_keywords=frozenset()):
    """If the provide string matches a keyword, append an underscore to distinguish them."""
    if (s in _Keywords) or (s in aux_keywords):
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

def PrepareIdentifier (s, in_use, aux_keywords=frozenset(), private=False, protected=False):
    """Combine everything required to create a unique identifier.

    Leading and trailing underscores are stripped from all
    identifiers.

    in_use is the set of already used identifiers.  Upon return from
    this function, it is updated to include the returned identifier.

    aux_keywords is an optional set of additional symbols that are
    illegal in the given context; use this to prevent conflicts with
    known method names.

    If private is True, the returned identifier has two leading
    underscores, making it a private variable within a Python class.
    If private is False, all leading underscores are stripped,
    guaranteeing the identifier will not be private.

    NOTE: Only module-level identifiers should be treated as
    protected.  The class-level _ReservedSymbol infrastructure does
    not include protected symbols."""
    s = DeconflictKeyword(MakeIdentifier(s).strip('_'), aux_keywords)
    if private:
        s = '__' + s
    elif protected:
        s = '_' + s
    return MakeUnique(s, in_use)

class _DeconflictSymbols_mixin (object):
    """Mix-in used to deconflict public symbols in classes that may be
    inherited by generated binding classes.

    Some classes, like bindings._PST_element or datatypes._PST_mixin,
    have public symbols associated with functions and variables.  It
    is possible that an XML schema might include tags and attribute
    names that match these symbols.  To avoid conflict, the reserved
    symbols marked in this class are added to the pre-defined
    identifier set.

    Subclasses should create a class-level variable that contains a
    set of strings denoting the symbols reserved in this class,
    combined with those from any superclasses that also have reserved
    symbols.  Code like the following is suggested:
       # For base classes (direct mix-in):
        _ReservedSymbols = set([ 'one', 'two' ])
       # For subclasses:
        _ReservedSymbols = SuperClass._ReservedSymbols.union(set([ 'three' ]))

    Only public symbols (those with no underscores) are current
    supported.  (Private symbols can't be deconflict that easily, and
    no protected symbols that derive from the XML are created by the
    binding generator.)
    """

    # Base from mixin does not reserve anything.
    _ReservedSymbols = set()

if '__main__' == __name__:
    import unittest

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
    
