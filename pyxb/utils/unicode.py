"""Tnis module contains support for Unicode characters as required to
support the regular expression syntax defined in U{annex F
<http://www/Documentation/W3C/www.w3.org/TR/xmlschema-2/index.html#regexs>}
of the XML Schema definition.

In particular, we need to be able to identify character properties and
block escapes, as defined in F.1.1, by name.

Block data: http://www.unicode.org/Public/3.1-Update/Blocks-4.txt
Property list data: http://www.unicode.org/Public/3.1-Update/PropList-3.1.0.txt
Full dataset: http://www.unicode.org/Public/3.1-Update/UnicodeData-3.1.0.txt
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

    """The maximum value for a code point in the Unicode code point
    space.  This is normally 0xFFFF, because wide unicode characters
    are generally not enabled in Python builds.  If, however, they are
    enabled, this will be the full value of 0x10FFFF."""
    MaxCodePoint = 0x10FFFF
    if not SupportsWideUnicode:
        MaxCodePoint = 0xFFFF

    __codepoints = None

    def _codepoints (self):
        """For testing purrposes only, access to the codepoints
        internal representation."""
        return self.__codepoints

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
        if isinstance(value, tuple):
            (s, e) = value
            e += 1
        else:
            s = int(value)
            e = s+1
        if s > e:
            raise ValueError('codepoint range value order')
        if s > self.MaxCodePoint:
            return self
        li = bisect.bisect_left(self.__codepoints, s)
        ri = bisect.bisect_right(self.__codepoints, e)
        case = ((li & 1) << 1) | (ri & 1)
        if not do_add:
            case = 3 - case
        #print 'add %d %d to %s at %d %d' % (s, e, self.__codepoints, li, ri)
        if 0x03 == case:
            del self.__codepoints[li:ri]
        elif 0x02 == case:
            del self.__codepoints[li+1:ri]
            self.__codepoints[li] = e
        elif 0x01 == case:
            del self.__codepoints[li+1:ri]
            self.__codepoints[li] = s
        else:
            self.__codepoints[li:ri] = [s, e]
        return self

    def add (self, value):
        return self.__mutate(value, True)

    def subtract (self, value):
        return self.__mutate(value, False)

    def asTuples (self):
        """Return the codepoints as tuples denoting the ranges that
        are in the set.

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
        """Return an instance that represents the inverse of this
        set."""
        rv = type(self)()
        if (0 < len(self.__codepoints)) and (0 == self.__codepoints[0]):
            rv.__codepoints.extend(self.__codepoints[1:])
        else:
            rv.__codepoints.append(0)
            rv.__codepoints.extend(self.__codepoints)
        return rv
    
    def difference (self, other):
        pass

import unicode_data
