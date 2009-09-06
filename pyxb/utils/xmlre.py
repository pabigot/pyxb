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
    pass

def MatchCharacterClass (text, position):
    if position >= len(text):
        return None
    c = text[position]
    if '.' == c:
        return (unicode.WildcardEsc, position+1)
    if '[' == c:
        cg = _MatchCharGroup(text, position+1)
        if cg is not None:
            (result, new_position) = cg
            if (new_position < len(text)) and (']' == text[new_position]):
                return (result, new_position+1)
            raise RegularExpressionError(new_position, "Character group missing closing ']'")
        raise RegularExpressionError(position, "Unable to identify character group after '['")
    if '\\' == c:
        pass
    return None

import unittest

class TestXMLRE (unittest.TestCase):
    def testRangeErrors (self):
        self.assertTrue(MatchCharacterClass('', 1) is None)

    def testWildcardEscape (self):
        (charset, position) = MatchCharacterClass('.', 0)
        self.assertEqual(charset, unicode.WildcardEsc)
        self.assertEqual(position, 1)

if __name__ == '__main__':
    unittest.main()
