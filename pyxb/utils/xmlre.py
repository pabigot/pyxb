# -*- coding: utf-8 -*-
# Copyright 2009-2013, Peter A. Bigot
# Copyright 2012,2018 Jon Foster
# Copyright 2018 Eurofins Digital Product Testing UK Ltd - https://www.eurofins-digitaltesting.com/
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
are for multi-character (C{\w}) and category escapes (e.g., C{\p{N}} or
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

import re
import logging
import pyxb.utils.unicode
from pyxb.utils import six

_log = logging.getLogger(__name__)

# ===========================================================================
# XML Schema character class parsing/conversion functions
# ===========================================================================

# AllEsc maps all the possible escape codes and wildcards in an XML schema
# regular expression into the corresponding CodePointSet.
_AllEsc = { }

def _InitializeAllEsc ():
    """Set the values in _AllEsc without introducing C{k} and C{v} into
    the module."""

    _AllEsc[six.u('.')] = pyxb.utils.unicode.WildcardEsc
    bs = b'\\'.decode('ascii')
    for k, v in six.iteritems(pyxb.utils.unicode.SingleCharEsc):
        _AllEsc[bs + six.text_type(k)] = v
    for k, v in six.iteritems(pyxb.utils.unicode.MultiCharEsc):
        _AllEsc[bs + six.text_type(k)] = v
    for k, v in six.iteritems(pyxb.utils.unicode.catEsc):
        _AllEsc[bs + six.text_type(k)] = v
    for k, v in six.iteritems(pyxb.utils.unicode.complEsc):
        _AllEsc[bs + six.text_type(k)] = v
    for k, v in six.iteritems(pyxb.utils.unicode.IsBlockEsc):
        _AllEsc[bs + six.text_type(k)] = v
_InitializeAllEsc()

class RegularExpressionError (ValueError):
    """Raised when a regular expression cannot be processed.."""
    def __init__ (self, position, description):
        self.position = position
        ValueError.__init__(self, 'At %d: %s' % (position, description))

_CharClassEsc_re = re.compile(r'\\(?:(?P<cgProp>[pP]{(?P<charProp>[-A-Za-z0-9]+)})|(?P<cgClass>[^pP]))')
def _MatchCharClassEsc(text, position):
    """Parse a U{charClassEsc<http://www.w3.org/TR/xmlschema-2/#nt-charClassEsc>} term.

    This is one of:

      - U{SingleCharEsc<http://www.w3.org/TR/xmlschema-2/#nt-SingleCharEsc>},
      an escaped single character such as C{E{\}n}

      - U{MultiCharEsc<http://www.w3.org/TR/xmlschema-2/#nt-MultiCharEsc>},
      an escape code that can match a range of characters,
      e.g. C{E{\}s} to match certain whitespace characters

      - U{catEsc<http://www.w3.org/TR/xmlschema-2/#nt-catEsc>}, the
      C{E{\}pE{lb}...E{rb}} Unicode property escapes including
      categories and blocks

      - U{complEsc<http://www.w3.org/TR/xmlschema-2/#nt-complEsc>},
      the C{E{\}PE{lb}...E{rb}} inverted Unicode property escapes

    If the parsing fails, throws a RegularExpressionError.

    @return: A pair C{(cps, p)} where C{cps} is a
    L{pyxb.utils.unicode.CodePointSet} containing the code points
    associated with the character class, and C{p} is the text offset
    immediately following the escape sequence.

    @raise RegularExpressionError: if the expression is syntactically
    invalid.
    """

    mo = _CharClassEsc_re.match(text, position)
    if mo:
        escape_code = mo.group(0)
        cps = _AllEsc.get(escape_code)
        if cps is not None:
            return (cps, mo.end())
        char_prop = mo.group('charProp')
        if char_prop is not None:
            if char_prop.startswith('Is'):
                raise RegularExpressionError(position, 'Unrecognized Unicode block %s in %s' % (char_prop[2:], escape_code))
            raise RegularExpressionError(position, 'Unrecognized character property %s' % (escape_code,))
        raise RegularExpressionError(position, 'Unrecognized character class %s' % (escape_code,))
    raise RegularExpressionError(position, "Unrecognized escape identifier at %s" % (text[position:],))

def _MatchPosCharGroup(text, position):
    '''Parse a U{posCharGroup<http://www.w3.org/TR/xmlschema-2/#nt-posCharGroup>} term.

    @return: A tuple C{(cps, fs, p)} where:
      - C{cps} is a L{pyxb.utils.unicode.CodePointSet} containing the code points associated with the group;
      - C{fs} is a C{bool} that is C{True} if the next character is the C{-} in a U{charClassSub<http://www.w3.org/TR/xmlschema-2/#nt-charClassSub>} and C{False} if the group is not part of a charClassSub;
      - C{p} is the text offset immediately following the closing brace.

    @raise RegularExpressionError: if the expression is syntactically
    invalid.
    '''

    start_position = position

    # DASH is just some unique object, used as a marker.
    # It can't be unicode or a CodePointSet.
    class DashClass:
        pass
    DASH = DashClass()

    # We tokenize first, then go back and stick the ranges together.
    tokens = []
    has_following_subtraction = False
    while True:
        if position >= len(text):
            raise RegularExpressionError(position, "Incomplete character class expression, missing closing ']'")
        ch = text[position]
        if ch == six.u('['):
            # Only allowed if this is a subtraction
            if not tokens or tokens[-1] is not DASH:
                raise RegularExpressionError(position, "'[' character not allowed in character class")
            has_following_subtraction = True
            # For a character class subtraction, the "-[" are not part of the
            # posCharGroup, so undo reading the dash
            tokens.pop()
            position = position - 1
            break
        elif ch == six.u(']'):
            # End
            break
        elif ch == b'\\'.decode('ascii'):
            cps, position = _MatchCharClassEsc(text, position)
            single_char = cps.asSingleCharacter()
            if single_char is not None:
                tokens.append(single_char)
            else:
                tokens.append(cps)
        elif ch == six.u('-'):
            # We need to distinguish between "-" and "\-".  So we use
            # DASH for a plain "-", and "-" for a "\-".
            tokens.append(DASH)
            position = position + 1
        else:
            tokens.append(ch)
            position = position + 1

    if not tokens:
        raise RegularExpressionError(position, "Empty character class not allowed")

    # At the start or end of the character group, a dash has to be a literal
    if tokens[0] is DASH:
        tokens[0] = six.u('-')
    if tokens[-1] is DASH:
        tokens[-1] = six.u('-')
    result_cps = pyxb.utils.unicode.CodePointSet()
    cur_token = 0
    while cur_token < len(tokens):
        start = tokens[cur_token]
        if cur_token + 2 < len(tokens) and tokens[cur_token + 1] is DASH:
            end = tokens[cur_token + 2]
            if not isinstance(start, six.text_type) or not isinstance(end, six.text_type):
                if start is DASH or end is DASH:
                    raise RegularExpressionError(start_position, 'Two dashes in a row is not allowed in the middle of a character class.')
                raise RegularExpressionError(start_position, 'Dashes must be surrounded by characters, not character class escapes. %r %r' %(start, end))
            if start > end:
                raise RegularExpressionError(start_position, 'Character ranges must have the lowest character first')
            result_cps.add((ord(start), ord(end)))
            cur_token = cur_token + 3
        else:
            if start is DASH:
                raise RegularExpressionError(start_position, 'Dash without an initial character')
            elif isinstance(start, six.text_type):
                result_cps.add(ord(start))
            else:
                assert isinstance(start, pyxb.utils.unicode.CodePointSet)
                result_cps.extend(start)
            cur_token = cur_token + 1

    return result_cps, has_following_subtraction, position

def _MatchCharClassExpr(text, position):
    '''Parse a U{charClassExpr<http://www.w3.org/TR/xmlschema-2/#nt-charClassExpr>}.

    These are XML regular expression classes such as C{[abc]}, C{[a-c]}, C{[^abc]}, or C{[a-z-[q]]}.

    @param text: The complete text of the regular expression being
    translated.  The first character must be the C{[} starting a
    character class.

    @param position: The offset of the start of the character group.

    @return: A pair C{(cps, p)} where C{cps} is a
    L{pyxb.utils.unicode.CodePointSet} containing the code points
    associated with the property, and C{p} is the text offset
    immediately following the closing brace.

    @raise RegularExpressionError: if the expression is syntactically
    invalid.
    '''
    if position >= len(text):
        raise RegularExpressionError(position, 'Missing character class expression')
    if six.u('[') != text[position]:
        raise RegularExpressionError(position, "Expected start of character class expression, got '%s'" % (text[position],))
    position = position + 1
    if position >= len(text):
        raise RegularExpressionError(position, 'Missing character class expression')
    negated = (text[position] == six.u('^'))
    if negated:
        position = position + 1

    result_cps, has_following_subtraction, position = _MatchPosCharGroup(text, position)

    if negated:
        result_cps = result_cps.negate()

    if has_following_subtraction:
        assert text[position] == six.u('-')
        assert text[position + 1] == six.u('[')
        position = position + 1
        sub_cps, position = _MatchCharClassExpr(text, position)
        result_cps.subtract(sub_cps)

    if position >= len(text) or text[position] != six.u(']'):
        raise RegularExpressionError(position, "Expected ']' to end character class")
    return result_cps, position + 1


# ===========================================================================
# Utilities for Python's RE module
# ===========================================================================

_python_re_escape_char_dict = {
    six.u('\000'): b'\\000'.decode('ascii'),
    six.u('\r'): b'\\r'.decode('ascii'),
    six.u('\n'): b'\\n'.decode('ascii'),
    six.u('.'): b'\\.'.decode('ascii'),
    six.u('^'): b'\\^'.decode('ascii'),
    six.u('$'): b'\\$'.decode('ascii'),
    six.u('*'): b'\\*'.decode('ascii'),
    six.u('+'): b'\\+'.decode('ascii'),
    six.u('?'): b'\\?'.decode('ascii'),
    six.u('{'): b'\\{'.decode('ascii'),
    six.u('}'): b'\\}'.decode('ascii'),
    b'\\'.decode('ascii'): b'\\\\'.decode('ascii'),
    six.u('['): b'\\['.decode('ascii'),
    six.u(']'): b'\\]'.decode('ascii'),
    six.u('|'): b'\\|'.decode('ascii'),
    six.u('('): b'\\('.decode('ascii'),
    six.u(')'): b'\\)'.decode('ascii'),
    six.u('-'): b'\\-'.decode('ascii'), # Needed inside [] blocks
    }

def _python_re_escape_char(char):
    '''Escape characters that need it.  Pass a single character only.

    Note: Python's re.escape() function it a little overeager to
    escape everything.  This only escapes things that need it.'''
    return _python_re_escape_char_dict.get(char, char)

def _AddQualifier(pattern, min_occurs, max_occurs):
    assert isinstance(pattern, six.text_type)
    assert len(pattern) >= 1
    assert isinstance(min_occurs, int)
    assert min_occurs >= 0
    assert max_occurs is None or isinstance(max_occurs, int)
    assert max_occurs is None or max_occurs >= 0

    if min_occurs == 1 and max_occurs == 1:
        pass
    elif max_occurs is None:
        if min_occurs == 0:
            pattern += six.u('*')
        elif min_occurs == 1:
            pattern += six.u('+')
        else:
            pattern = six.u('%s{%d,}') % (pattern, min_occurs)
    elif max_occurs == 1 and min_occurs == 0:
        pattern += six.u('?')
    elif max_occurs == 0:
        pattern = six.u('')
    elif min_occurs == max_occurs:
        pattern = six.u('%s{%d}') % (pattern, min_occurs)
    else:
        pattern = six.u('%s{%d,%d}') % (pattern, min_occurs, max_occurs)
    return pattern


# ===========================================================================
# Functions to parse a XSD regexp
# ===========================================================================

# Char ::= [^.\?*+()|#x5B#x5D]
# This appears to be a bug in the spec - the text says {} are invalid,
# but the grammar doesn't.  Excluding them because otherwise "a{4}" is
# ambiguous - does it only match the literal "aaaa" or only match the
# literal "a{4}"?  (We only actually need to exclude "{" to make the
# grammar unambiguous, but this is cleaner and matches the standard's
# text).
_invalid_literal_chars = frozenset(b'.\\?*+()|[]{}'.decode('ascii'))

def _MatchAtom(text, position):
    '''Parses an "atom".

    This is either:
     - "Char", a plain single character
     - A bracketed "regExp"
     - "charClassEsc" an escape code for either a single character or a range
       of characters
     - "WildcardEsc", the "." wildcard
     - "charClassExpr", a character class using the [] syntax

    Preconditions: Not at end of string.
    If the parsing fails, throws a RegularExpressionError.
    Returns a tuple with the Python regex that matches the atom, and the new
    position.
    Postconditions: None.
    '''
    assert position < len(text)
    start_position = position
    ch = text[position]
    if ch not in _invalid_literal_chars:
        atom_pattern = _python_re_escape_char(ch)
        position = position + 1
    elif ch == six.u('('):
        atom_pattern, position = _MatchSubRegex(text, position + 1)
        if position >= len(text) or text[position] != six.u(')'):
            raise RegularExpressionError(start_position, "Unmatched bracket")
        position = position + 1
    elif ch == b'\\'.decode('ascii'):
        char_class, position = _MatchCharClassEsc(text, position)
        single_char = char_class.asSingleCharacter()
        if single_char is not None:
            # E.g. '\\\\' isn't really a char range.
            atom_pattern = _python_re_escape_char(single_char)
        else:
            atom_pattern = char_class.asPattern()
    elif ch == six.u('.'):
        atom_pattern = pyxb.utils.unicode.WildcardEsc.asPattern()
        position = position + 1
    elif ch == six.u('['):
        char_class, position = _MatchCharClassExpr(text, position)
        atom_pattern = char_class.asPattern()
    else:
        raise RegularExpressionError(position, "Invalid character")
    return atom_pattern, position

_quantifier_curlybrace_re = re.compile(
        b'\\{(?:'
        b'(?P<exact_occurs>[0-9]+)' # {3} style
        b'|'
        b'(?:(?P<min_occurs>[0-9]+),(?P<max_occurs>[0-9]+)?)' # {3,4} or {3,}
        b')\\}'.decode('ascii'))

def _MatchQuantifier(text, position):
    '''Tries to parse a "quantifier", if present.
    If not, just returns the default quantifier of {1,1}.

    Preconditions: None.
    If there's a "{" character indicating the start of a quantifier, but
    parsing it fails, throws a RegularExpressionError.  Will not throw if
    there's no quantifier at all.
    Returns a tuple with the min and max occurs, and the new position.  Max
    occurs can be None for unlimited.
    Postconditions: None.
    '''

    min_occurs = 1
    max_occurs = 1
    if position < len(text):
        ch = text[position]
        if ch == six.u('?'):
            min_occurs = 0
            position = position + 1
        elif ch == six.u('*'):
            min_occurs = 0
            max_occurs = None
            position = position + 1
        elif ch == six.u('+'):
            max_occurs = None
            position = position + 1
        elif ch == six.u('{'):
            mo = _quantifier_curlybrace_re.match(text, position)
            if not mo:
                raise RegularExpressionError(position, "Cannot parse quantifier starting '{')")
            exact_occurs = mo.group('exact_occurs')
            if exact_occurs is not None:
                min_occurs = max_occurs = int(exact_occurs, 10)
            else:
                min_occurs = int(mo.group('min_occurs'), 10)
                max_occurs = mo.group('max_occurs')
                if max_occurs is not None:
                    max_occurs = int(max_occurs, 10)
            position = mo.end()
    return min_occurs, max_occurs, position

def _MatchBranch(text, position):
    '''Parses a "branch".  This is a series of "piece"s.  It doesn't contain
    the "|" character (unless it's bracketed or escaped).

    Each "piece" is an "atom" with an optional "qualifier".

    Preconditions: None
    If the parsing fails, throws a RegularExpressionError.
    Returns a tuple with the (possibly empty) Python regex that matches the
    branch and the new position.
    Postconditions: At end of string, or next character is '|' or ')'.
    '''
    pieces = []
    while position < len(text) and text[position] != six.u('|') and text[position] != six.u(')'):
        atom_pattern, position = _MatchAtom(text, position)
        min_occurs, max_occurs, position = _MatchQuantifier(text, position)
        pieces.append(_AddQualifier(atom_pattern, min_occurs, max_occurs))

    pattern = six.u('').join(pieces)
    return pattern, position

def _MatchSubRegex(text, position):
    '''Parses a "regExp".  This is one or more "branch"es, separated by "|"
    characters.

    Preconditions: None
    If the parsing fails, throws a RegularExpressionError.
    Returns a tuple with the Python regex that matches the XSD regex and the
    new position.
    Postconditions: At end of string, or next character is ')'.
    '''
    branches = []
    new_branch, position = _MatchBranch(text, position)
    branches.append(new_branch)
    while position < len(text) and text[position] == six.u('|'):
        new_branch, position = _MatchBranch(text, position + 1)
        branches.append(new_branch)
    pattern = six.u('(?:%s)') % (six.u('|').join(branches),)
    return pattern, position

# ===========================================================================
# Main XSD-to-Python regex conversion function
# ===========================================================================

def XMLToPython (pattern):
    """Convert the given pattern to the format required for Python
    regular expressions.

    @param pattern: A Unicode string defining a pattern consistent
    with U{XML regular
    expressions<http://www.w3.org/TR/xmlschema-2/index.html#regexs>}.

    @return: A Unicode string specifying a Python regular expression
    that matches the same language as C{pattern}."""
    assert isinstance(pattern, six.text_type)
    py_pattern, position = _MatchSubRegex(pattern, 0)
    if position != len(pattern):
        raise RegularExpressionError()
    return six.u("^%s$") % (py_pattern,)
