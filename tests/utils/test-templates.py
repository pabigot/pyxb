import unittest
from pyxb.utils.templates import *

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
