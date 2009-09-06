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
        ValueError.__init__(description)

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
        if np >= len(text):
            raise RegularExpressionError(np, "Missing escape identifier after '\\'")
        nc = text[np]
        cs = unicode.SingleCharEsc.get(nc)
        if cs is None:
            cs = unicode.MultiCharEsc.get(nc)
        if cs is not None:
            return (cs, np+1)
        if 'p' == nc:
            pass
        elif 'P' == nc:
            pass
        else:
            raise RegularExpressionError(np, "Unrecognized escape identifier '\\%s'" % (cs,))
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

if __name__ == '__main__':
    unittest.main()
