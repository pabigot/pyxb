import re
import unittest

# This expression replaces markers in template text with the value
# obtained by looking up the marker in a dictionary.
_substIdPattern = re.compile("%{(?P<id>\w+)}")

# This expression performs conditional substitution: if the expression
# provided evaluates to true in a given context, then one value is
# substituted, otherwise the alternative value is substituted.
# %{?1 == 2??true?:false?}
_substConditionalPattern = re.compile("%{\?(?P<expr>.+?)\?\?(?P<true>.*?)(\?:(?P<false>.*?))?\?}", re.MULTILINE + re.DOTALL)

# This expression tests whether an identifier is defined to a non-None
# value in the context; if so, it replaces the marker with template
# text.  In that replacement text, the value ?@ is replaced by the
# test expression.
# Note: NOT by the value of the test expression.  If no replacement
# text is given, the replacement '%{?@}' is used, which replaces it
# with the value of the test expression.
# %{?maybe_text?+?@ is defined to be %{?@}?}
_substIfDefinedPattern = re.compile("%{\?(?P<id>\w+)(\?\+(?P<repl>.*?))?(\?\-(?P<ndrepl>.*?))?\?}", re.MULTILINE + re.DOTALL)

# The pattern which, if present in the body of a IfDefined block, is
# replaced by the test expression.
_substDefinedBodyPattern = re.compile("\?@")

def _bodyIfDefinedPattern (match_object, dictionary):
    global _substDefinedBodyPattern
    id = match_object.group('id')
    repl = match_object.group('repl')
    ndrepl = match_object.group('ndrepl')
    value = dictionary.get(id, None)
    if value is not None:
        if repl:
            return _substDefinedBodyPattern.sub(id, repl)
        if ndrepl:
            return ''
        return _substDefinedBodyPattern.sub(id, '%{?@}')
    else:
        if ndrepl:
            return _substDefinedBodyPattern.sub(id, ndrepl)
        return ''

def _bodyConditionalPattern (match_object, dictionary):
    global _substDefinedBodyPattern
    expr = match_object.group('expr')
    true = match_object.group('true')
    false = match_object.group('false')
    value = None
    try:
        value = eval(expr, dictionary)
    except Exception, e:
        return '%%{EXCEPTION: %s}' % (e,)
    if value:
        return _substDefinedBodyPattern.sub(expr, true)
    if false is not None:
        return _substDefinedBodyPattern.sub(expr, false)
    return ''

def replaceInText (text, **dictionary):
    global _substIfDefinedPattern
    global _substConditionalPattern
    global _substIdPattern
    global _substDefinedBodyPattern
    rv = text
    rv = _substIfDefinedPattern.sub(lambda _x: _bodyIfDefinedPattern(_x, dictionary), rv)
    rv = _substConditionalPattern.sub(lambda _x: _bodyConditionalPattern(_x, dictionary), rv)
    rv =  _substIdPattern.sub(
        lambda _x,_map=dictionary:
           _map.get(_x.group('id'), '%%{MISSING:%s}' % (_x.group('id'),))
        , rv)
    return rv
    
_dictionary = { 'one' : 'un'
              , 'two' : 'dau'
              , 'three' : 'tri'
              , 'un' : 1
              , 'dau': 2
              , 'tri': 3
              , 'empty': ''
              , 'defined': 'value'
              }

class IfDefinedPatternTestCase (unittest.TestCase):
    dictionary = _dictionary

    def testNoSubst (self):
        self.assertEquals('un', replaceInText('%{?one?}', **self.dictionary))
        self.assertEquals('', replaceInText('%{?four?}', **self.dictionary))

    def testPlainSubst (self):
        self.assertEquals('one is defined', replaceInText('%{?one?+one is defined?}', **self.dictionary))
        self.assertEquals('', replaceInText('%{?four?+four is defined?}', **self.dictionary))
        self.assertEquals('four is not defined', replaceInText('%{?four?+@? is defined?-?@ is not defined?}', **self.dictionary))
        self.assertEquals('name', replaceInText('%{?context?+%{?@}.?}name'))
        self.assertEquals('name', replaceInText('%{?context?+%{?@}.?}name', context=None))
        self.assertEquals('owner.name', replaceInText('%{?context?+%{?@}.?}name', context='owner'))

    def testWithSubst (self):
        self.assertEquals('un and un are two', replaceInText('%{?one?+%{?@} and %{?@} are two?-what is ?@??}', **self.dictionary))
        self.assertEquals('what is "four"?', replaceInText('%{?four?+%{?@} and %{?@} are two?-what is "?@"??}', **self.dictionary))


class ConditionalPatternTestCase (unittest.TestCase):
    dictionary = _dictionary
    
    def testBasic (self):
        self.assertEquals('three is defined', replaceInText('%{?three??three is defined?:three is not defined?}', **self.dictionary))
        self.assertEquals("%{EXCEPTION: name 'four' is not defined}", replaceInText('%{?four??four is defined?:four is not defined?}', **self.dictionary))
        self.assertEquals('value', replaceInText('%{?defined??%{defined}?:pass?}', **self.dictionary))
        self.assertEquals('pass', replaceInText('%{?empty??%{empty}?:pass?}', **self.dictionary))

    def testHalfExpressions (self):
        self.assertEquals('value is three', replaceInText('%{?3 == un+dau??value is three?}', **self.dictionary))
        self.assertEquals('', replaceInText('%{?3 == un-dau??value is three?}', **self.dictionary))
        self.assertEquals('good 1 == un', replaceInText('%{?1 == un??good ?@?:bad ?@?}', **self.dictionary))
        self.assertEquals('bad 2 == un', replaceInText('%{?2 == un??good ?@?:bad ?@?}', **self.dictionary))
        self.assertEquals('''
        if runtime_test:
            print 'Good on 1 == un'
''', replaceInText('''
        %{?1 == un??if runtime_test:
            print 'Good on ?@'
?}''', **self.dictionary))

    def testExpressions (self):
        self.assertEquals('value is three', replaceInText('%{?3 == un+dau??value is three?:value is not three?}', **self.dictionary))
        self.assertEquals('value is not three', replaceInText('%{?3 == un-dau??value is three?:value is not three?}', **self.dictionary))

    def testNesting (self):
        self.assertEquals('tri', replaceInText('%{?3 == un+dau??%{three}?:not %{three}?}', **self.dictionary))

class IdPatternTestCase (unittest.TestCase):
    dictionary = _dictionary

    def testNoChange (self):
        cases = [ 'plain text'
                , '   leading whitespace'
                , 'trailing whitespace '
                , '''Multiline
text''' ] # '''
        for c in cases:
            self.assertEquals(c, replaceInText(c, **{}))

    def testSimpleSubstitution (self):
        self.assertEquals('un', replaceInText('%{one}', **self.dictionary))
        self.assertEquals('un and dau', replaceInText('%{one} and %{two}', **self.dictionary))
        self.assertEquals('''Line un
Line dau
Line tri
''', replaceInText('''Line %{one}
Line %{two}
Line %{three}
''', **self.dictionary))

    def testMissing (self):
        self.assertEquals('%{MISSING:four}', replaceInText('%{four}', **self.dictionary))

if __name__ == '__main__':
    #print replaceInText('%{?three%?three is defined%:three is not defined?}', ConditionalPatternTestCase.dictionary)
    #print "\n".join(_substConditionalPattern.match('%{?three%?three is defined%:three is not defined?}').groups())
    unittest.main()
