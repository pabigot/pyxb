# Copyright 2009, Peter A. Bigot
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain a
# copy of the License at:
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# http://www.xmlschemareference.com/examples/Ch14/regexpDemo.xsd
# http://www.xmlschemareference.com/examples/Ch14/regexpDemo.xml

import unicode
import re

class RegularExpressionError (ValueError):
    def __init__ (self, position, description):
        self.position = position
        ValueError.__init__(self, 'At %d: %s' % (position, description))

def _MatchCharPropBraced (text, position):
    if position >= len(text):
        raise RegularExpressionError(position, "Missing brace after category escape")
    if '{' != text[position]:
        raise RegularExpressionError(position, "Unexpected character '%s' after category escape" % (text[position],))
    ep = text.find('}', position+1)
    if 0 > ep:
        raise RegularExpressionError(position, "Unterminated category")
    char_prop = text[position+1:ep]
    if char_prop.startswith('Is'):
        char_prop = char_prop[2:]
        cs = unicode.BlockMap.get(char_prop)
        if cs is None:
            raise RegularExpressionError(position, "Unrecognized block name '%s'" % (char_prop,))
        return (cs, ep+1)
    cs = unicode.PropertyMap.get(char_prop)
    if cs is None:
        raise RegularExpressionError(position, "Unrecognized character property '%s'" % (char_prop,))
    return (cs, ep+1)

def _MaybeMatchCharClassEsc (text, position, include_sce=True):
    if '\\' != text[position]:
        return None
    position += 1
    if position >= len(text):
        raise RegularExpressionError(position, "Incomplete character escape")
    nc = text[position]
    np = position + 1
    cs = None
    if include_sce:
        cs = unicode.SingleCharEsc.get(nc)
    if cs is None:
        cs = unicode.MultiCharEsc.get(nc)
    if cs is not None:
        return (cs, np)
    if 'p' == nc:
        return _MatchCharPropBraced(text, np)
    if 'P' == nc:
        (cs, np) = _MatchCharPropBraced(text, np)
        return (cs.negate(), np)
    if (not include_sce) and (nc in unicode.SingleCharEsc):
        return None
    raise RegularExpressionError(np, "Unrecognized escape identifier '\\%s'" % (nc,))

_NotXMLChar_set = frozenset([ '-', '[', ']' ])
def _CharOrSCE (text, position):
    if position >= len(text):
        raise RegularExpressionError(position, "Missing character")
    rc = text[position]
    position += 1
    if rc in _NotXMLChar_set:
        raise RegularExpressionError(position, "Unexpected character '%s'" % (rc,))
    if '\\' == rc:
        if position >= len(text):
            raise RegularExpressionError(position, "Incomplete escape sequence")
        charset = unicode.SingleCharEsc.get(text[position])
        if charset is None:
            raise RegularExpressionError(position-1, "Unrecognized single-character escape '\\%s'" % (text[position],))
        rc = charset.asSingleCharacter()
        position += 1
    return (rc, position)

def _MatchPosCharGroup (text, position):
    cps = unicode.CodePointSet()
    if '-' == text[position]:
        cps.add(ord('-'))
        position += 1
    while position < len(text):
        # NB: This is not ideal, as we have to hack around matching SCEs
        if '\\' == text[position]:
            cg = _MaybeMatchCharClassEsc(text, position, include_sce=False)
            if cg is not None:
                (charset, position) = cg
                cps.extend(charset)
                continue
        if text[position] in _NotXMLChar_set:
            break
        (sc0, np) = _CharOrSCE(text, position)
        osc0 = ord(sc0)
        if (np < len(text)) and ('-' == text[np]):
            np += 1
            (sc1, np) = _CharOrSCE(text, np)
            osc1 = ord(sc1)
            if osc0 > osc1:
                raise RegularExpressionError(position, 'Character range must be non-decreasing')
            cps.add( (osc0, osc1) )
        else:
            cps.add(osc0)
        position = np

    return (cps, position)

def _MatchCharGroup (text, position):
    if position >= len(text):
        raise RegularExpressionError(position, 'Expected character group')
    np = position
    negative_group = ('^' == text[np])
    if negative_group:
        np += 1
    (cps, np) = _MatchPosCharGroup(text, np)
    if negative_group:
        cps = cps.negate()
    if (np < len(text)) and ('-' == text[np]):
        (ncps, np) = _MatchCharClassExpr(text, np+1)
        cps.subtract(ncps)
    return (cps, np)

def _MatchCharClassExpr (text, position):
    if position >= len(text):
        raise RegularExpressionError(position, 'Missing character class expression')
    nc = text[position]
    np = position + 1
    if '[' != nc:
        raise RegularExpressionError(position, "Expected start of character class expression, got '%s'" % (nc,))
    (cps, np) = _MatchCharGroup(text, np)
    if np >= len(text):
        raise RegularExpressionError(position, "Incomplete character class expression, missing closing ']'")
    if ']' != text[np]:
        raise RegularExpressionError(position, "Bad character class expression, ends with '%s'" % (text[np],))
    if 1 == (np - position):
        raise RegularExpressionError(position, "Empty character class not allowed")
    return (cps, np+1)

def MatchCharacterClass (text, position):
    if position >= len(text):
        return None
    c = text[position]
    np = position + 1
    if '.' == c:
        return (unicode.WildcardEsc, np)
    if '[' == c:
        return _MatchCharClassExpr(text, position)
    return _MaybeMatchCharClassEsc(text, position)

def XMLToPython (pattern):
    new_pattern_elts = []
    new_pattern_elts.append('^')
    position = 0
    while position < len(pattern):
        cg = MatchCharacterClass(pattern, position)
        if cg is None:
            new_pattern_elts.append(pattern[position])
            position += 1
        else:
            (cps, position) = cg
            new_pattern_elts.append(cps.asPattern())
    new_pattern_elts.append('$')
    return ''.join(new_pattern_elts)

import unittest

class TestXMLRE (unittest.TestCase):
    def testRangeErrors (self):
        self.assertTrue(MatchCharacterClass('', 1) is None)

    def testWildcardEscape (self):
        (charset, position) = MatchCharacterClass('.', 0)
        self.assertEqual(charset, unicode.WildcardEsc)
        self.assertEqual(position, 1)

    def testSingleCharEscapes (self):
        # 17 chars recognized as escapes
        self.assertEqual(len(unicode.SingleCharEsc), 17)

        (charset, position) = MatchCharacterClass(r'\t', 0)
        self.assertEqual(charset.asTuples(), [ (9, 9) ])
        self.assertEqual(2, position)

        (charset, position) = MatchCharacterClass(r'\?', 0)
        self.assertEqual(charset.asTuples(), [ (ord('?'), ord('?')) ])
        self.assertEqual(2, position)

        (charset, position) = MatchCharacterClass(r'\\', 0)
        self.assertEqual(charset.asTuples(), [ (ord('\\'), ord('\\')) ])
        self.assertEqual(2, position)

    def testMultiCharEscapes (self):
        # 5*2 chars recognized as escapes
        self.assertEqual(len(unicode.MultiCharEsc), 10)
        (charset, position) = MatchCharacterClass(r'\s', 0)
        self.assertEqual(charset.asTuples(), [ (9, 10), (13, 13), (32, 32) ])
        self.assertEqual(2, position)

    def testMatchCharProperty (self):
        self.assertRaises(RegularExpressionError, _MatchCharPropBraced, "L", 0)
        self.assertRaises(RegularExpressionError, _MatchCharPropBraced, "{L", 0)
        text = "{L}"
        (charset, position) = _MatchCharPropBraced(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, unicode.PropertyMap['L'])
        text = "{IsCyrillic}"
        (charset, position) = _MatchCharPropBraced(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, unicode.BlockMap['Cyrillic'])

    def testCharProperty (self):
        text = r'\p{D}'
        self.assertRaises(RegularExpressionError, MatchCharacterClass, text, 0)
        text = r'\P{D}'
        self.assertRaises(RegularExpressionError, MatchCharacterClass, text, 0)
        text = r'\p{N}'
        (charset, position) = MatchCharacterClass(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, unicode.PropertyMap['N'])
        text = r'\P{N}'
        (charset, position) = MatchCharacterClass(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset.negate(), unicode.PropertyMap['N'])
        text = r'\p{Sm}'
        (charset, position) = MatchCharacterClass(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, unicode.PropertyMap['Sm'])

        text = r'\p{IsArrows}'
        (charset, position) = MatchCharacterClass(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, unicode.BlockMap['Arrows'])
        text = r'\P{IsArrows}'
        (charset, position) = MatchCharacterClass(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset.negate(), unicode.BlockMap['Arrows'])

    def testCharGroup (self):
        self.assertRaises(RegularExpressionError, MatchCharacterClass, '[]', 0)
        self.assertRaises(RegularExpressionError, MatchCharacterClass, '[A-]', 0)
        self.assertRaises(RegularExpressionError, MatchCharacterClass, '[A-]', 0)
        text = r'[A-Z]'
        #(charset, position) = MatchCharacterClass(text, 0)
        #self.assertEqual(position, len(text))
        #self.assertEqual(charset, unicode.CodePointSet((ord('A'), ord('Z'))))

    def testCharOrSCE (self):
        self.assertRaises(RegularExpressionError, _CharOrSCE, '[', 0)
        self.assertRaises(RegularExpressionError, _CharOrSCE, ']', 0)
        self.assertRaises(RegularExpressionError, _CharOrSCE, '-', 0)
        (charset, position) = _CharOrSCE('A', 0)
        self.assertEqual(1, position)
        self.assertEqual(charset, 'A')
        (charset, position) = _CharOrSCE(r'\t', 0)
        self.assertEqual(2, position)
        self.assertEqual("\t", charset)
        (charset, position) = _CharOrSCE(u'\u0041', 0)
        self.assertEqual(1, position)
        self.assertEqual("A", charset)

    def testMatchPosCharGroup (self):
        text = 'A'
        (charset, position) = _MatchPosCharGroup(text, 0)
        self.assertEqual(position, 1)
        self.assertEqual(charset, unicode.CodePointSet(ord('A')))
        text = r'\n'
        (charset, position) = _MatchPosCharGroup(text, 0)
        self.assertEqual(position, 2)
        self.assertEqual(charset, unicode.CodePointSet(10))
        text = r'-'
        (charset, position) = _MatchPosCharGroup(text, 0)
        self.assertEqual(position, 1)
        self.assertEqual(charset, unicode.CodePointSet(ord('-')))
        text = 'A-Z'
        (charset, position) = _MatchPosCharGroup(text, 0)
        self.assertEqual(position, 3)
        self.assertEqual(charset, unicode.CodePointSet((ord('A'), ord('Z'))))
        text = r'\t-\r'
        (charset, position) = _MatchPosCharGroup(text, 0)
        self.assertEqual(position, 5)
        self.assertEqual(charset, unicode.CodePointSet((9, 13)))
        text = r'\t-A'
        (charset, position) = _MatchPosCharGroup(text, 0)
        self.assertEqual(position, 4)
        self.assertEqual(charset, unicode.CodePointSet((9, ord('A'))))
        text = r'Z-\]'
        (charset, position) = _MatchPosCharGroup(text, 0)
        self.assertEqual(position, 4)
        self.assertEqual(charset, unicode.CodePointSet((ord('Z'), ord(']'))))
        text = 'Z-A'
        self.assertRaises(RegularExpressionError, _MatchPosCharGroup, text, 0)
        
    def testMatchCharClassExpr (self):
        self.assertRaises(RegularExpressionError, _MatchCharClassExpr, 'missing open', 0)
        self.assertRaises(RegularExpressionError, _MatchCharClassExpr, '[missing close', 0)
        first_five = unicode.CodePointSet( (ord('A'), ord('E')) )
        text = r'[ABCDE]'
        (charset, position) = _MatchCharClassExpr(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, first_five)
        text = r'[^ABCDE]'
        (charset, position) = _MatchCharClassExpr(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset.negate(), first_five)
        text = r'[A-Z-[GHI]]'
        expected = unicode.CodePointSet( (ord('A'), ord('Z')) )
        expected.subtract( (ord('G'), ord('I') ))
        (charset, position) = _MatchCharClassExpr(text, 0)
        self.assertEqual(position, len(text))
        self.assertEqual(charset, expected)
        text = r'[\p{L}-\p{Lo}]'
        self.assertRaises(RegularExpressionError, _MatchCharClassExpr, text, 0)
        text = r'[\p{L}-[\p{Lo}]]'
        (charset, position) = _MatchCharClassExpr(text, 0)
        expected = unicode.CodePointSet(unicode.PropertyMap['L'])
        expected.subtract(unicode.PropertyMap['Lo'])
        self.assertEqual(position, len(text))
        self.assertEqual(charset, expected)
        
    def testXMLToPython (self):
        self.assertEqual(r'^123$', XMLToPython('123'))
        # Note that single-char escapes in the expression are
        # converted to character classes.
        self.assertEqual(r'^Why[ ]not[?]$', XMLToPython(r'Why[ ]not\?'))

    def testRegularExpressions (self):
        text = u'[\i-[:]][\c-[:]]*'
        compiled_re = re.compile(XMLToPython(text))
        self.assertTrue(compiled_re.match('identifier'))
        self.assertFalse(compiled_re.match('0bad'))
        self.assertFalse(compiled_re.match(' spaceBad'))
        self.assertFalse(compiled_re.match('qname:bad'))

if __name__ == '__main__':
    unittest.main()
