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
