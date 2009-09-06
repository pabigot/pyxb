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

class RegularExpressionError (ValueError):
    def __init__ (self, position, description):
        self.position = position
        ValueError.__init__(self, description)

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

def _MatchCharClassEsc (text, position):
    if position >= len(text):
        raise RegularExpressionError(position, "Incomplete character escape")
    nc = text[position]
    np = position + 1
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
    raise RegularExpressionError(np, "Unrecognized escape identifier '\\%s'" % (nc,))

def _MatchCharGroup (text, position):
    pass

def MatchCharacterClass (text, position):
    if position >= len(text):
        return None
    c = text[position]
    np = position + 1
    if '.' == c:
        return (unicode.WildcardEsc, np)
    if '[' == c:
        cg = _MatchCharGroup(text, np)
        if cg is not None:
            (result, np) = cg
            if (np < len(text)) and (']' == text[np]):
                return (result, np+1)
            raise RegularExpressionError(np, "Character group missing closing ']'")
        raise RegularExpressionError(position, "Unable to identify character group after '['")
    if '\\' == c:
        cg = _MatchCharClassEsc(text, np)
        if np is None:
            raise RegularExpressionError(np, "Unable to identify character escape")
        return cg
    return None

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

if __name__ == '__main__':
    unittest.main()
