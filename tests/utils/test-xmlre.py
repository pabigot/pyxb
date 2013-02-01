# -*- coding: utf-8 -*-
import logging
if __name__ == '__main__':
    logging.basicConfig()
_log = logging.getLogger(__name__)
import pyxb.utils.xmlre as xmlre
import pyxb.utils.unicode as unicode
import re

import unittest

class TestXMLRE (unittest.TestCase):
    def assertMatches(self, xml_pattern, value):
        '''Helper function to assert a value matches an XSD regexp pattern.'''
        py_pattern = xmlre.XMLToPython(xml_pattern)
        compiled = re.compile(py_pattern)
        mo = compiled.match(value)
        self.assertTrue(mo is not None, 'XML re %r Python %r should match %r' % (xml_pattern, py_pattern, value))

    def assertNoMatch(self, xml_pattern, value):
        '''Helper function to assert a value does not matche an XSD regexp
        pattern.'''
        py_pattern = xmlre.XMLToPython(xml_pattern)
        compiled = re.compile(py_pattern)
        mo = compiled.match(value)
        self.assertTrue(mo is None, 'XML re %r Python %r shoudl not match %r' % (xml_pattern, py_pattern, value))

    def testRangeErrors (self):
        self.assertTrue(xmlre.MaybeMatchCharacterClass('', 1) is None)

    def testWildcardEscape (self):
        (charset, position) = xmlre.MaybeMatchCharacterClass('.', 0)
        self.assertEqual(charset, unicode.WildcardEsc)
        self.assertEqual(position, 1)

    def testSingleCharEscapes (self):
        # 17 chars recognized as escapes
        self.assertEqual(len(unicode.SingleCharEsc), 17)

        (charset, position) = xmlre.MaybeMatchCharacterClass(r'\t', 0)
        self.assertEqual(charset.asTuples(), [ (9, 9) ])
        self.assertEqual(2, position)

        (charset, position) = xmlre.MaybeMatchCharacterClass(r'\?', 0)
        self.assertEqual(charset.asTuples(), [ (ord('?'), ord('?')) ])
        self.assertEqual(2, position)

        (charset, position) = xmlre.MaybeMatchCharacterClass(r'\\', 0)
        self.assertEqual(charset.asTuples(), [ (ord('\\'), ord('\\')) ])
        self.assertEqual(2, position)

    def testMultiCharEscapes (self):
        # 5*2 chars recognized as escapes
        self.assertEqual(len(unicode.MultiCharEsc), 10)
        (charset, position) = xmlre.MaybeMatchCharacterClass(r'\s', 0)
        self.assertEqual(charset.asTuples(), [ (9, 10), (13, 13), (32, 32) ])
        self.assertEqual(2, position)

    def testMatchCharProperty (self):
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassEsc, "\pL", 0)
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassEsc, "\p{L", 0)
        text = "\p{L}"
        (charset, position) = xmlre._MatchCharClassEsc(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, unicode.PropertyMap['L'])
        text = "\p{IsCyrillic}"
        (charset, position) = xmlre._MatchCharClassEsc(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, unicode.BlockMap['Cyrillic'])

    def testCharProperty (self):
        text = r'\p{D}'
        self.assertRaises(xmlre.RegularExpressionError, xmlre.MaybeMatchCharacterClass, text, 0)
        text = r'\P{D}'
        self.assertRaises(xmlre.RegularExpressionError, xmlre.MaybeMatchCharacterClass, text, 0)
        text = r'\p{N}'
        (charset, position) = xmlre.MaybeMatchCharacterClass(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, unicode.PropertyMap['N'])
        text = r'\P{N}'
        (charset, position) = xmlre.MaybeMatchCharacterClass(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset.negate(), unicode.PropertyMap['N'])
        text = r'\p{Sm}'
        (charset, position) = xmlre.MaybeMatchCharacterClass(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, unicode.PropertyMap['Sm'])

    def testCharBlock (self):
        text = r'\p{IsArrows}'
        (charset, position) = xmlre.MaybeMatchCharacterClass(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, unicode.BlockMap['Arrows'])
        text = r'\P{IsArrows}'
        (charset, position) = xmlre.MaybeMatchCharacterClass(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset.negate(), unicode.BlockMap['Arrows'])
        
        text = r'\p{IsWelsh}'
        self.assertRaises(xmlre.RegularExpressionError, xmlre.MaybeMatchCharacterClass, text, 0)
        text = r'\P{IsWelsh}'
        self.assertRaises(xmlre.RegularExpressionError, xmlre.MaybeMatchCharacterClass, text, 0)

    def testCharGroup (self):
        self.assertRaises(xmlre.RegularExpressionError, xmlre.MaybeMatchCharacterClass, '[]', 0)
        self.assertRaises(xmlre.RegularExpressionError, xmlre.MaybeMatchCharacterClass, '[A--]', 0)
        self.assertRaises(xmlre.RegularExpressionError, xmlre.MaybeMatchCharacterClass, '[A--]', 0)
        text = r'[A-Z]'
        #(charset, position) = xmlre.MaybeMatchCharacterClass(text, 0)
        #self.assertEqual(position, len(text))
        #self.assertEqual(charset, unicode.CodePointSet((ord('A'), ord('Z'))))

    def testCharOrSCE (self):
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassEsc, '[', 0)
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassEsc, ']', 0)
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassEsc, '-', 0)
        (charset, position) = xmlre._MatchCharClassEsc(r'\t', 0)
        self.assertEqual(2, position)
        self.assertEqual(unicode.CodePointSet("\t"), charset)

    def testMatchPosCharGroup (self):
        text = u'A]'
        (charset, has_sub, position) = xmlre._MatchPosCharGroup(text, 0)
        self.assertEqual(position, 1)
        self.assertEqual(charset, unicode.CodePointSet(ord('A')))
        text = ur'\n]'
        (charset, has_sub, position) = xmlre._MatchPosCharGroup(text, 0)
        self.assertEqual(position, 2)
        self.assertEqual(charset, unicode.CodePointSet(10))
        text = ur'-]'
        (charset, has_sub, position) = xmlre._MatchPosCharGroup(text, 0)
        self.assertEqual(position, 1)
        self.assertEqual(charset, unicode.CodePointSet(ord('-')))
        text = u'A-Z]'
        (charset, has_sub, position) = xmlre._MatchPosCharGroup(text, 0)
        self.assertEqual(position, 3)
        self.assertEqual(charset, unicode.CodePointSet((ord('A'), ord('Z'))))
        text = ur'\t-\r]'
        (charset, has_sub, position) = xmlre._MatchPosCharGroup(text, 0)
        self.assertEqual(position, 5)
        self.assertEqual(charset, unicode.CodePointSet((9, 13)))
        text = ur'\t-A]'
        (charset, has_sub, position) = xmlre._MatchPosCharGroup(text, 0)
        self.assertEqual(position, 4)
        self.assertEqual(charset, unicode.CodePointSet((9, ord('A'))))
        text = ur'Z-\]]'
        (charset, has_sub, position) = xmlre._MatchPosCharGroup(text, 0)
        self.assertEqual(position, 4)
        self.assertEqual(charset, unicode.CodePointSet((ord('Z'), ord(']'))))
        text = u'Z-A]'
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchPosCharGroup, text, 0)
        
    def testMatchCharClassExpr (self):
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassExpr, 'missing open', 0)
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassExpr, '[missing close', 0)
        first_five = unicode.CodePointSet( (ord('A'), ord('E')) )
        text = ur'[ABCDE]'
        (charset, position) = xmlre._MatchCharClassExpr(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, first_five)
        text = ur'[^ABCDE]'
        (charset, position) = xmlre._MatchCharClassExpr(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset.negate(), first_five)
        text = ur'[A-Z-[GHI]]'
        expected = unicode.CodePointSet( (ord('A'), ord('Z')) )
        expected.subtract( (ord('G'), ord('I') ))
        (charset, position) = xmlre._MatchCharClassExpr(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, expected)
        text = ur'[\p{L}-\p{Lo}]'
        self.assertRaises(xmlre.RegularExpressionError, xmlre._MatchCharClassExpr, text, 0)
        text = ur'[\p{L}-[\p{Lo}]]'
        (charset, position) = xmlre._MatchCharClassExpr(text, 0)
        expected = unicode.CodePointSet(unicode.PropertyMap['L'])
        expected.subtract(unicode.PropertyMap['Lo'])
        self.assertEqual(position, len(text))
        self.assertEqual(charset, expected)
        
    def testXMLToPython (self):
        self.assertEqual(r'^123$', xmlre.XMLToPython(u'123'))
        # Note that single-char escapes in the expression are
        # converted to character classes.
        self.assertEqual(r'^Why[ ]not[?]$', xmlre.XMLToPython(ur'Why[ ]not\?'))

    def testRegularExpressions (self):
        text = u'[\i-[:]][\c-[:]]*'
        compiled_re = re.compile(xmlre.XMLToPython(text))
        self.assertTrue(compiled_re.match(u'identifier'))
        self.assertFalse(compiled_re.match(u'0bad'))
        self.assertFalse(compiled_re.match(u' spaceBad'))
        self.assertFalse(compiled_re.match(u'qname:bad'))
        text = u'\\i\\c*'
        text_py = xmlre.XMLToPython(text)
        compiled_re = re.compile(text_py)
        self.assertTrue(compiled_re.match(u'identifier'))
        self.assertTrue(compiled_re.match(u'_underscore'))

    def testTrivialLiteral(self):
        # Simplest sanity check for assertMatches / assertNoMatch
        self.assertMatches(u"hello", u"hello")
        self.assertNoMatch(u"hello", u"hhello")
        self.assertNoMatch(u"hello", u"helloo")
        self.assertNoMatch(u"hello", u"goodbye")

    def testConvertingRangesToPythonWithDash(self):
        # It's really easy to convert this RE into u"foo[&-X]bar", if
        # sorting characters in ASCII order without special-casing "-"
        self.assertNoMatch(u"foo[-&X]bar", u"fooWbar")
        self.assertMatches(u"foo[-&X]bar", u"foo-bar")
        self.assertMatches(u"foo[-&X]bar", u"foo&bar")
        self.assertMatches(u"foo[-&X]bar", u"fooXbar")

    def testConvertingRangesToPythonWithCaret(self):
        # It's really easy to convert this RE into u"foo[^z]bar", if
        # sorting characters in ASCII order without special-casing "^"
        self.assertNoMatch(u"foo[z^]bar", u"fooWbar")
        self.assertMatches(u"foo[z^]bar", u"foozbar")
        self.assertMatches(u"foo[z^]bar", u"foo^bar")

    def testConvertingRangesToPythonWithBackslash(self):
        # It's really easy to convert this RE into u"foo[A\n]bar", if
        # you forget to special-case r"\"
        self.assertNoMatch(u"foo[A\\\\n]bar", u"fooWbar")
        self.assertNoMatch(u"foo[A\\\\n]bar", u"foo\nbar")
        self.assertMatches(u"foo[A\\\\n]bar", u"fooAbar")
        self.assertMatches(u"foo[A\\\\n]bar", u"foo\\bar")
        self.assertMatches(u"foo[A\\\\n]bar", u"foonbar")

    def testCnUnicodeClass(self):
        # The Cn class is basically "everything that is not included in the
        # Unicode character database".  So it requires special handling when
        # you parse the Unicode character database.  It is really easy to
        # miss this and leave the Cn class empty.
        self.assertNoMatch(u"foo\\p{Cn}bar", u"fooWbar")
        self.assertMatches(u"foo\\p{Cn}bar", u"foo\ufffebar")
        self.assertMatches(u"foo\\P{Cn}bar", u"fooWbar")
        self.assertNoMatch(u"foo\\P{Cn}bar", u"foo\ufffebar")

    def testCnUnicodeClassInC(self):
        # If the Cn class is wrong (see above), then C will probably be wrong
        # too.
        self.assertNoMatch(u"foo\\p{C}bar", u"fooWbar")
        self.assertMatches(u"foo\\p{C}bar", u"foo\ufffebar")
        self.assertMatches(u"foo\\P{C}bar", u"fooWbar")
        self.assertNoMatch(u"foo\\P{C}bar", u"foo\ufffebar")

    def testMultiCharEscape_s(self):
        self.assertNoMatch(u"foo\\sbar", u"fooWbar")
        self.assertMatches(u"foo\\sbar", u"foo bar")

    def testMultiCharEscape_S(self):
        self.assertMatches(u"foo\\Sbar", u"fooWbar")
        self.assertNoMatch(u"foo\\Sbar", u"foo bar")

    def testMultiCharEscape_i(self):
        self.assertNoMatch(u"foo\\ibar", u"foo bar")
        self.assertMatches(u"foo\\ibar", u"fooWbar")
        self.assertMatches(u"foo\\ibar", u"foo:bar")
        self.assertMatches(u"foo\\ibar", u"foo_bar")
        self.assertMatches(u"foo\\ibar", u"foo\u0D0Cbar")
        self.assertNoMatch(u"foo\\ibar", u"foo-bar")
        self.assertNoMatch(u"foo\\ibar", u"foo.bar")
        self.assertNoMatch(u"foo\\ibar", u"foo\u203Fbar")
        self.assertNoMatch(u"foo\\ibar", u"foo\u3005bar")

    def testMultiCharEscape_I(self):
        self.assertMatches(u"foo\\Ibar", u"foo bar")
        self.assertNoMatch(u"foo\\Ibar", u"fooWbar")
        self.assertNoMatch(u"foo\\Ibar", u"foo:bar")
        self.assertNoMatch(u"foo\\Ibar", u"foo_bar")
        self.assertNoMatch(u"foo\\Ibar", u"foo\u0D0Cbar")
        self.assertMatches(u"foo\\Ibar", u"foo-bar")
        self.assertMatches(u"foo\\Ibar", u"foo.bar")
        self.assertMatches(u"foo\\Ibar", u"foo\u203Fbar")
        self.assertMatches(u"foo\\Ibar", u"foo\u3005bar")

    def testMultiCharEscape_c(self):
        self.assertNoMatch(u"foo\\cbar", u"foo bar")
        self.assertMatches(u"foo\\cbar", u"fooWbar")
        self.assertMatches(u"foo\\cbar", u"foo:bar")
        self.assertMatches(u"foo\\cbar", u"foo_bar")
        self.assertMatches(u"foo\\cbar", u"foo\u0D0Cbar")
        self.assertMatches(u"foo\\cbar", u"foo-bar")
        self.assertMatches(u"foo\\cbar", u"foo.bar")
        self.assertNoMatch(u"foo\\cbar", u"foo\u203Fbar")
        self.assertMatches(u"foo\\cbar", u"foo\u3005bar")

    def testMultiCharEscape_C(self):
        self.assertMatches(u"foo\\Cbar", u"foo bar")
        self.assertNoMatch(u"foo\\Cbar", u"fooWbar")
        self.assertNoMatch(u"foo\\Cbar", u"foo:bar")
        self.assertNoMatch(u"foo\\Cbar", u"foo_bar")
        self.assertNoMatch(u"foo\\Cbar", u"foo\u0D0Cbar")
        self.assertNoMatch(u"foo\\Cbar", u"foo-bar")
        self.assertNoMatch(u"foo\\Cbar", u"foo.bar")
        self.assertMatches(u"foo\\Cbar", u"foo\u203Fbar")
        self.assertNoMatch(u"foo\\Cbar", u"foo\u3005bar")

    def testMultiCharEscape_d(self):
        self.assertNoMatch(u"foo\\dbar", u"foo bar")
        self.assertNoMatch(u"foo\\dbar", u"foozbar")
        self.assertMatches(u"foo\\dbar", u"foo5bar")
        self.assertMatches(u"foo\\dbar", u"foo\u0669bar")

    def testMultiCharEscape_D(self):
        self.assertMatches(u"foo\\Dbar", u"foo bar")
        self.assertMatches(u"foo\\Dbar", u"foozbar")
        self.assertNoMatch(u"foo\\Dbar", u"foo5bar")
        self.assertNoMatch(u"foo\\Dbar", u"foo\u0669bar")

    def testMultiCharEscape_w(self):
        self.assertNoMatch(u"foo\\wbar", u"foo bar")
        self.assertNoMatch(u"foo\\wbar", u"foo&bar")
        self.assertMatches(u"foo\\wbar", u"fooWbar")
        self.assertMatches(u"[\\w]*", u"fooWboar")

    def testMultiCharEscape_W(self):
        self.assertMatches(u"foo\\Wbar", u"foo bar")
        self.assertMatches(u"foo\\Wbar", u"foo&bar")
        self.assertNoMatch(u"foo\\Wbar", u"fooWbar")

    def testUnicodeClass(self):
        self.assertMatches(u"\\p{L}*", u"hello")
        self.assertNoMatch(u"\\p{L}*", u"hell7")

    def testQuotedOpenBrace(self):
        self.assertMatches(u"foo\\[bar", u"foo[bar")
        self.assertNoMatch(u"foo\\[bar", u"foo\\[bar")
        self.assertNoMatch(u"foo\\[bar", u"foob")

    def testQuotedCloseBrace(self):
        self.assertMatches(u"foo\\]bar", u"foo]bar")
        self.assertNoMatch(u"foo\\]bar", u"foo\\]bar")
        self.assertNoMatch(u"foo\\]bar", u"foob")

    def testQuotedAndUnquotedCloseBrace(self):
        self.assertMatches(u"foo[b\\]c]ar", u"foobar")
        self.assertMatches(u"foo[b\\]c]ar", u"foo]ar")
        self.assertMatches(u"foo[b\\]c]ar", u"foocar")
        self.assertNoMatch(u"foo[b\\]c]ar", u"fooar")

    def testUnquotedAndQuotedCloseBrace(self):
        self.assertMatches(u"foo[zb]c\\]ar", u"foobc]ar")
        self.assertMatches(u"foo[zb]c\\]ar", u"foozc]ar")
        self.assertNoMatch(u"foo[zb]c\\]ar", u"foozar")

    def testQuotedOpenCloseBraces(self):
        self.assertMatches(u"foo\\[bar\\]", u"foo[bar]")
        self.assertNoMatch(u"foo\\[bar\\]", u"foo\\[bar]")
        self.assertNoMatch(u"foo\\[bar\\]", u"foobar")

    def testQuotedAndUnquotedOpenBrace(self):
        self.assertMatches(u"foo\\[b[az]r", u"foo[bar")
        self.assertMatches(u"foo\\[b[az]r", u"foo[bzr")
        self.assertNoMatch(u"foo\\[b[az]r", u"foobr")

    def testUnquotedAndQuotedOpenBrace(self):
        self.assertMatches(u"foo[b\\[az]r", u"foobr")
        self.assertMatches(u"foo[b\\[az]r", u"foo[r")
        self.assertNoMatch(u"foo[b\\[az]r", u"foobar")

    def testFoo(self):
        self.assertMatches(u"foo\\\\[bc\\]a]r", u"foo\\br")
        self.assertNoMatch(u"foo\\\\[bc\\]a]r", u"foo\\bar")
        self.assertNoMatch(u"foo\\\\[bc\\]a]r", u"foobar")

    def testDashStartRangeWithRange(self):
        # Spec says: The - character is a valid character range only at the
        # beginning or end of a positive character group.
        self.assertMatches(u"foo[-a-z]bar", u"fooabar")
        self.assertMatches(u"foo[-a-z]bar", u"foo-bar")
        self.assertMatches(u"foo[-a-z]bar", u"foonbar")
        self.assertMatches(u"foo[-a-z]bar", u"foozbar")
        self.assertNoMatch(u"foo[-a-z]bar", u"fooWbar")

    def testDashStartRangeOneLetter(self):
        self.assertMatches(u"foo[-a]bar", u"fooabar")
        self.assertMatches(u"foo[-a]bar", u"foo-bar")
        self.assertNoMatch(u"foo[-a]bar", u"fooWbar")

    def testDashStartRangeSeveralLetters(self):
        self.assertMatches(u"foo[-abc]bar", u"fooabar")
        self.assertMatches(u"foo[-abc]bar", u"foobbar")
        self.assertMatches(u"foo[-abc]bar", u"foocbar")
        self.assertMatches(u"foo[-abc]bar", u"foo-bar")
        self.assertNoMatch(u"foo[-abc]bar", u"fooWbar")

    def testDashOnlyRange(self):
        self.assertMatches(u"foo[-]bar", u"foo-bar")
        self.assertNoMatch(u"foo[-a-z]bar", u"fooWbar")

    def testDashEndRange(self):
        self.assertMatches(u"foo[a-z-]bar", u"fooabar")
        self.assertMatches(u"foo[a-z-]bar", u"foo-bar")
        self.assertMatches(u"foo[a-z-]bar", u"foonbar")
        self.assertMatches(u"foo[a-z-]bar", u"foozbar")
        self.assertNoMatch(u"foo[a-z-]bar", u"fooWbar")

    def testDashEndRangeOneLetter(self):
        self.assertMatches(u"foo[a-]bar", u"fooabar")
        self.assertMatches(u"foo[a-]bar", u"foo-bar")
        self.assertNoMatch(u"foo[a-]bar", u"fooWbar")

    def testDashEndRangeSeveralLetters(self):
        self.assertMatches(u"foo[abc-]bar", u"fooabar")
        self.assertMatches(u"foo[abc-]bar", u"foobbar")
        self.assertMatches(u"foo[abc-]bar", u"foocbar")
        self.assertMatches(u"foo[abc-]bar", u"foo-bar")
        self.assertNoMatch(u"foo[abc-]bar", u"fooWbar")

    def testDashEndRangeWithSub(self):
        self.assertMatches(u"foo[a-z--[q]]bar", u"fooabar")
        self.assertMatches(u"foo[a-z--[q]]bar", u"foo-bar")
        self.assertMatches(u"foo[a-z--[q]]bar", u"foonbar")
        self.assertMatches(u"foo[a-z--[q]]bar", u"foozbar")
        self.assertNoMatch(u"foo[a-z--[q]]bar", u"fooWbar")
        self.assertNoMatch(u"foo[a-z--[q]]bar", u"fooqbar")

    def testDashEndRangeOneLetterWithSub(self):
        self.assertMatches(u"foo[a--[q]]bar", u"fooabar")
        self.assertMatches(u"foo[a--[q]]bar", u"foo-bar")
        self.assertNoMatch(u"foo[a--[q]]bar", u"fooWbar")

        self.assertMatches(u"foo[a--[a]]bar", u"foo-bar")
        self.assertNoMatch(u"foo[a--[a]]bar", u"fooabar")
        self.assertNoMatch(u"foo[a--[a]]bar", u"fooWbar")

    def testDashEndRangeSeveralLettersWithSub(self):
        self.assertMatches(u"foo[abc--[b]]bar", u"fooabar")
        self.assertMatches(u"foo[abc--[b]]bar", u"foocbar")
        self.assertMatches(u"foo[abc--[b]]bar", u"foo-bar")
        self.assertNoMatch(u"foo[abc--[b]]bar", u"foobbar")
        self.assertNoMatch(u"foo[abc--[b]]bar", u"fooWbar")

    def testCaret(self):
        self.assertMatches(u"foo^bar", u"foo^bar")
        self.assertNoMatch(u"foo^bar", u"foobar")
        self.assertNoMatch(u"foo^bar", u"barfoo")

    def testCaretStart(self):
        self.assertMatches(u"^foobar", u"^foobar")
        self.assertNoMatch(u"^foobar", u"foobar")

    def testDollar(self):
        self.assertMatches(u"foo$bar", u"foo$bar")
        self.assertNoMatch(u"foo$bar", u"foobar")
        self.assertNoMatch(u"foo$bar", u"barfoo")

    def testDollarEnd(self):
        self.assertMatches(u"foobar$", u"foobar$")
        self.assertNoMatch(u"foobar$", u"foobar")

    def testCaretInRangeSub(self):
        self.assertMatches(u"foo[a^-[a]]bar", u"foo^bar")
        self.assertNoMatch(u"foo[a^-[a]]bar", u"fooabar")
        self.assertNoMatch(u"foo[a^-[a]]bar", u"foobar")

    def testCaretInRange(self):
        self.assertMatches(u"foo[a^]bar", u"foo^bar")
        self.assertMatches(u"foo[a^]bar", u"fooabar")
        self.assertNoMatch(u"foo[a^]bar", u"foobar")

    def testSingleCharRange(self):
        self.assertMatches(u"foo[b]ar", u"foobar")

    def testQuotedSingleChar(self):
        self.assertMatches(u"foo\\\\bar", u"foo\\bar")

if __name__ == '__main__':
    unittest.main()
