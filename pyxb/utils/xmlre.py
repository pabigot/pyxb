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

"""Support for regular expressions conformant to the XML Schema specification.

For the most part, XML regular expressions are similar to the POSIX
ones, and can be handled by the Python C{re} module.  The exceptions
are for multi-character (C{\w}) and category escapes (e.g., C{\N} or
C{\p{IPAExtensions}}) and the character set subtraction capability.
This module supports those by scanning the regular expression,
replacing the category escapes with equivalent charset expressions.
It further detects the subtraction syntax and modifies the charset
expression to remove the unwanted code points.

The basic technique is to step through the characters of the regular
expression, entering a recursive-descent parser when one of the
translated constructs is encountered.

There is a nice set of XML regular expressions at
U{http://www.xmlschemareference.com/examples/Ch14/regexpDemo.xsd},
with a sample document at U{
http://www.xmlschemareference.com/examples/Ch14/regexpDemo.xml}"""

import unicode
import re

class RegularExpressionError (ValueError):
    """Raised when a regular expression cannot be processed.."""
    def __init__ (self, position, description):
        self.position = position
        ValueError.__init__(self, 'At %d: %s' % (position, description))

def _MatchCharPropBraced (text, position):
    """Match a U{character property
    <http://www.w3.org/TR/xmlschema-2/#nt-catEsc>}
    or U{multi-character escape
    <http://www.w3.org/TR/xmlschema-2/#nt-MultiCharEsc>} identifier,
    which will be enclosed in braces.

    @param text: The complete text of the regular expression being
    translated

    @param position: The offset of the opening brace of the character
    property

    @return: A pair C{(cps, p)} where C{cps} is a
    L{unicode.CodePointSet} containing the code points associated with
    the property, and C{p} is the text offset immediately following
    the closing brace.

    @raise RegularExpressionError: if opening or closing braces are
    missing, or if the text between them cannot be recognized as a
    property or block identifier.
    """
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
    """Attempt to match a U{character class escape
    <http://www.w3.org/TR/xmlschema-2/#nt-charClassEsc>}
    expression.

    @param text: The complete text of the regular expression being
    translated

    @param position: The offset of the backslash that would begin the
    potential character class escape

    @param include_sce: Optional directive to include single-character
    escapes in addition to character cllass escapes.  Default is
    C{True}.

    @return: C{None} if C{position} does not begin a character class
    escape; otherwise a pair C{(cps, p)} as in
    L{_MatchCharPropBraced}."""
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
"""The set of characters that cannot appear within a character class
expression unescaped."""

def _CharOrSCE (text, position):
    """Return the single character represented at the given position.

    @param text: The complete text of the regular expression being
    translated

    @param position: The offset of the character to return.  If this
    is a backslash, additional text is consumed in order to identify
    the U{single-character escape <http://www.w3.org/TR/xmlschema-2/#nt-SingleCharEsc>}
    that begins at the position.

    @return: A pair C{(c, p)} where C{c} is the Unicode character
    specified at the position, and C{p} is the text offset immediately
    following the closing brace.

    @raise RegularExpressionError: if the position has no character,
    or has a character in L{_NotXMLChar_set} or the position begins an
    escape sequence that is not resolvable as a single-character
    escape.
    """
    
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
    """Match a U{positive character
    group<http://www.w3.org/TR/xmlschema-2/#nt-posCharGroup>}
    that begins at the given position.

    @param text: The complete text of the regular expression being
    translated

    @param position: The offset of the start of the positive character
    group.
    
    @return: a pair C{(cps, p)} as in L{_MatchCharPropBraced}.

    @raise RegularExpressionError: if the expression is syntactically
    invalid.
    """
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
    """Match a U{character group<http://www.w3.org/TR/xmlschema-2/#nt-charGroup>}
    at the given position.

    @param text: The complete text of the regular expression being
    translated

    @param position: The offset of the start of the character group.
    
    @return: a pair C{(cps, p)} as in L{_MatchCharPropBraced}.

    @raise RegularExpressionError: if the expression is syntactically
    invalid.
    """

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
    """Match a U{character class expression<http://www.w3.org/TR/xmlschema-2/#nt-charClassExpr>}
    at the given position.

    @param text: The complete text of the regular expression being
    translated

    @param position: The offset of the start of the character group.
    
    @return: a pair C{(cps, p)} as in L{_MatchCharPropBraced}.

    @raise RegularExpressionError: if the expression is syntactically
    invalid.
    """
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

def MaybeMatchCharacterClass (text, position):
    """Attempt to match a U{character class expression
    <http://www.w3.org/TR/xmlschema-2/#nt-charClassExpr>}.

    @param text: The complete text of the regular expression being
    translated

    @param position: The offset of the start of the potential
    expression.
    
    @return: C{None} if C{position} does not begin a character class
    expression; otherwise a pair C{(cps, p)} as in
    L{_MatchCharPropBraced}."""
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
    """Convert the given pattern to the format required for Python
    regular expressions.

    @param pattern: A Unicode string defining a pattern consistent
    with U{XML regular
    expressions<http://www.w3.org/TR/xmlschema-2/index.html#regexs>}.

    @return: A Unicode string specifying a Python regular expression
    that matches the same language as C{pattern}."""
    new_pattern_elts = []
    new_pattern_elts.append('^')
    position = 0
    while position < len(pattern):
        cg = MaybeMatchCharacterClass(pattern, position)
        if cg is None:
            new_pattern_elts.append(pattern[position])
            position += 1
        else:
            (cps, position) = cg
            new_pattern_elts.append(cps.asPattern())
    new_pattern_elts.append('$')
    return ''.join(new_pattern_elts)
