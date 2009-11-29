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

"""This module contains support for Unicode characters as required to
support the regular expression syntax defined in U{annex F
<http://www/Documentation/W3C/www.w3.org/TR/xmlschema-2/index.html#regexs>}
of the XML Schema definition.

In particular, we need to be able to identify character properties and
block escapes, as defined in F.1.1, by name.

 - Block data: U{http://www.unicode.org/Public/3.1-Update/Blocks-4.txt}
 - Property list data: U{http://www.unicode.org/Public/3.1-Update/PropList-3.1.0.txt}
 - Full dataset: U{http://www.unicode.org/Public/3.1-Update/UnicodeData-3.1.0.txt}

The Unicode database active at the time XML Schema 1.0 was defined is
archived at
U{http://www.unicode.org/Public/3.1-Update/UnicodeCharacterDatabase-3.1.0.html},
and refers to U{Unicode Standard Annex #27: Unicode 3.1
<http://www.unicode.org/unicode/reports/tr27/>}.
"""

import re

SupportsWideUnicode = False
try:
    re.compile('[\U1d7ce-\U1d7ff]')
    SupportsWideUnicode = True
except:
    pass

import bisect
        
class CodePointSetError (LookupError):
    """Raised when some abuse of a L{CodePointSet} is detected."""
    pass

class CodePointSet (object):
    """Represent a set of Unicode code points.

    Each code point is an integral value between 0 and 0x10FFFF.  This
    class is used to represent a set of code points in a manner
    suitable for use as regular expression character sets."""

    MaxCodePoint = 0x10FFFF
    """The maximum value for a code point in the Unicode code point
    space.  This is normally 0xFFFF, because wide unicode characters
    are generally not enabled in Python builds.  If, however, they are
    enabled, this will be the full value of 0x10FFFF."""

    MaxShortCodePoint = 0xFFFF
    if not SupportsWideUnicode:
        MaxCodePoint = MaxShortCodePoint

    # The internal representation of the codepoints is as a sorted
    # list where values at an even index denote the first codepoint in
    # a range that is in the set, and the immediately following value
    # indicates the next following codepoint that is not in the set.
    # A missing value at the end is interpreted as MaxCodePoint.  For
    # example, the sequence [ 12, 15, 200 ] denotes the set containing
    # codepoints 12, 13, 14, and everything above 199.
    __codepoints = None

    def _codepoints (self):
        """For testing purrposes only, access to the codepoints
        internal representation."""
        return self.__codepoints

    def __cmp__ (self, other):
        """Equality is delegated to the codepoints list."""
        return cmp(self.__codepoints, other.__codepoints)

    def __init__ (self, *args):
        self.__codepoints = []
        if 1 == len(args):
            if isinstance(args[0], CodePointSet):
                self.__codepoints.extend(args[0].__codepoints)
                return
            if isinstance(args[0], list):
                args = args[0]
        [ self.add(_a) for _a in args ]


    def __mutate (self, value, do_add):
        # Identify the start (inclusive) and end (exclusive) code
        # points of the value's range.
        if isinstance(value, tuple):
            (s, e) = value
            e += 1
        elif isinstance(value, basestring):
            if 1 < len(value):
                raise TypeError()
            s = ord(value)
            e = s+1
        else:
            s = int(value)
            e = s+1
        if s > e:
            raise ValueError('codepoint range value order')

        # Validate the range for the code points supported by this
        # Python interpreter
        if s > self.MaxCodePoint:
            return self
        if e > self.MaxCodePoint:
            e = self.MaxCodePoint
        e = min(e, self.MaxCodePoint)

        # Index of first code point equal to or greater than s
        li = bisect.bisect_left(self.__codepoints, s)
        # Index of last code point less than or equal to e
        ri = bisect.bisect_right(self.__codepoints, e)
        # There are four cases; if we're subtracting, they reflect.
        case = ((li & 1) << 1) | (ri & 1)
        if not do_add:
            case = 3 - case
        #print 'add %d %d to %s at %d %d' % (s, e, self.__codepoints, li, ri)
        if 0x03 == case:
            # Add: Incoming value begins and ends within existing ranges
            del self.__codepoints[li:ri]
        elif 0x02 == case:
            # Add: Incoming value extends into an excluded range
            del self.__codepoints[li+1:ri]
            self.__codepoints[li] = e
        elif 0x01 == case:
            # Add: Incoming value begins in an excluded range
            del self.__codepoints[li+1:ri]
            self.__codepoints[li] = s
        else:
            # Add: Incoming value begins and ends within excluded ranges
            self.__codepoints[li:ri] = [s, e]
        return self

    def add (self, value):
        """Add the given value to the code point set.

        @param value: An integral value denoting a code point, or a
        tuple C{(s,e)} denoting the start and end (inclusive) code
        points in a range.
        @return: C{self}"""
        return self.__mutate(value, True)

    def extend (self, values):
        """Add multiple values to a code point set.

        @param values: Either a L{CodePointSet} instance, or an iterable
        whose members are valid parameters to L{add}.

        @return: C{self}"""
        if isinstance(values, CodePointSet):
            self.extend(values.asTuples())
        else:
            [ self.__mutate(_v, True) for _v in values ]
        return self

    def subtract (self, value):
        """Remove the given value from the code point set.

        @param value: An integral value denoting a code point, or a tuple
        C{(s,e)} denoting the start and end (inclusive) code points in a
        range, or a L{CodePointSet}.

        @return: C{self}"""
        if isinstance(value, CodePointSet):
            [ self.subtract(_v) for _v in value.asTuples() ]
            return self
        return self.__mutate(value, False)

    # Characters that must not appear unescaped in regular expression
    # patterns
    __NotXMLChar_set = frozenset([ '-', '[', ']' ])

    # Return the given code point as a unicode character suitable for
    # use in a regular expression
    def __unichr (self, code_point):
        rv = unichr(code_point)
        if rv in self.__NotXMLChar_set:
            rv = u'\\' + rv
        return rv

    def asPattern (self, with_brackets=True):
        """Return the code point set as Unicode regular expression
        character group consisting of a sequence of characters or
        character ranges.

        @param with_brackets: If C{True} (default), square brackets
        are added to enclose the returned character group."""
        rva = []
        if with_brackets:
            rva.append(u'[')
        for (s, e) in self.asTuples():
            if s == e:
                rva.append(self.__unichr(s))
            else:
                rva.extend([self.__unichr(s), '-', self.__unichr(e)])
        if with_brackets:
            rva.append(u']')
        return u''.join(rva)

    def asTuples (self):
        """Return the codepoints as tuples denoting the ranges that are in
        the set.

        Each tuple C{(s, e)} indicates that the code points from C{s}
        (inclusive) to C{e}) (inclusive) are in the set."""
        
        rv = []
        start = None
        for ri in xrange(len(self.__codepoints)):
            if start is not None:
                rv.append( (start, self.__codepoints[ri]-1) )
                start = None
            else:
                start = self.__codepoints[ri]
        if start is not None:
            rv.append( (start, self.MaxCodePoint) )
        return rv

    def negate (self):
        """Return an instance that represents the inverse of this set."""
        rv = type(self)()
        if (0 < len(self.__codepoints)) and (0 == self.__codepoints[0]):
            rv.__codepoints.extend(self.__codepoints[1:])
        else:
            rv.__codepoints.append(0)
            rv.__codepoints.extend(self.__codepoints)
        return rv
    
    def asSingleCharacter (self):
        """If this set represents a single character, return it as its
        unicode string value."""
        if (2 != len(self.__codepoints)) or (1 < (self.__codepoints[1] - self.__codepoints[0])):
            raise CodePointSetError('CodePointSet does not represent single character')
        return unichr(self.__codepoints[0])

from unicode_data import *

# Some of the MultiCharEsc classes refer to the U{NameChar
# <http://www.w3.org/TR/REC-xml/#NT-NameChar>} production for base
# XML.  The XMLSchema 1.0 definition refers to the 2nd edition of XML,
# which defines in Annex B the set of relevant character classes based
# on Unicode 2.0.  However, the current (fifth, at this writing)
# edition uses a much simpler characterization, and I'm going with
# that one.
_NameStartChar = CodePointSet(ord(':'),
                              ( ord('A'), ord('Z') ),
                              ord('_'),
                              ( ord('a'), ord('z') ),
                              (    0xC0,    0xD6 ),
                              (    0xD8,    0xF6 ),
                              (    0xF8,   0x2FF ),
                              (   0x370,   0x37D ),
                              (   0x37F,  0x1FFF ),
                              (  0x200C,  0x200D ),
                              (  0x2070,  0x218F ),
                              (  0x2C00,  0x2FEF ),
                              (  0x3001,  0xD7FF ),
                              (  0xF900,  0xFDCF ),
                              (  0xFDF0,  0xFFFD ),
                              ( 0x10000, 0xEFFFF ) )

# Add in characters that can appear in names, just not at the start.
_NameChar = CodePointSet(_NameStartChar).extend([ ord('-'),
                                                  ord('.'),
                                                  ( ord('0'), ord('9') ),
                                                  0xB7,
                                                  ( 0x0300, 0x036F ),
                                                  ( 0x203F, 0x2040 ) ])

# Production 24 : Single Character Escapes
SingleCharEsc = { 'n' : CodePointSet(0x0A),
                  'r' : CodePointSet(0x0D),
                  't' : CodePointSet(0x09) }
for c in r'\|.-^?*+{}()[]':
    SingleCharEsc[c] = CodePointSet(ord(c))

# Production 37 : Multi-Character Escapes
WildcardEsc = CodePointSet(ord('\n'), ord('\r')).negate()
MultiCharEsc = { }
MultiCharEsc['s'] = CodePointSet(0x20, ord('\t'), ord('\n'), ord('\r'))
MultiCharEsc['S'] = MultiCharEsc['s'].negate()
MultiCharEsc['i'] = _NameStartChar
MultiCharEsc['I'] = MultiCharEsc['i'].negate()
MultiCharEsc['c'] = _NameChar
MultiCharEsc['C'] = MultiCharEsc['c'].negate()
MultiCharEsc['d'] = PropertyMap['Nd']
MultiCharEsc['D'] = MultiCharEsc['d'].negate()
MultiCharEsc['W'] = CodePointSet(PropertyMap['P']).extend(PropertyMap['Z']).extend(PropertyMap['C'])
MultiCharEsc['w'] = MultiCharEsc['W'].negate()
