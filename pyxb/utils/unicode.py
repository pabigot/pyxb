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

import unicode_data
import re

SupportsWideUnicode = False
try:
    re.compile('[\U1d7ce-\U1d7ff]')
    SupportsWideUnicode = True
except:
    pass

def RangeSetToRE (range_set):
    range_seqs = []
    for (rmin, rmax) in range_set:
        if (0x10000 <= rmin):
            if not SupportsWideUnicode:
                continue
            rmin_rep = '\U%04x' % (rmin,)
        else:
            rmin_rep = '\u%04x' % (rmin,)
        if rmin == rmax:
            range_seqs.append(rmin_rep)
            continue
        if (0x10000 <= rmax):
            if not SupportsWideUnicode:
                continue
            rmax_rep = '\U%04x' % (rmax,)
        else:
            rmax_rep = '\u%04x' % (rmax,)
        range_seqs.append('%s-%s' % (rmin_rep, rmax_rep))
    if 0 == len(range_seqs):
        return None
    return '[' + ''.join(range_seqs) + ']'

'''
for k in unicode_data.BlockMap.keys():
    pattern = RangeSetToRE(unicode_data.BlockMap[k])
    if pattern is None:
        print '%s is not representable' % (k,)
        continue
    print '%s = %s' % (k, pattern)
    re.compile(pattern)

for k in unicode_data.PropertyMap.keys():
    pattern = RangeSetToRE(unicode_data.PropertyMap[k])
    if pattern is None:
        print '%s is not representable' % (k,)
        continue
    print '%s = %s' % (k, pattern)
    try:
        re.compile(pattern)
    except Exception, e:
        print "%s: %s\n  %s" % (k, pattern, e)
        
'''
        
class CodePointSet (object):
    """Represent a set of Unicode code points.

    Each code point is an integral value between 0 and 0x10FFFF.  This
    class is used to represent a set of code points in a manner
    suitable for use as regular expression character sets."""

    __codepoints = None

    def __init__ (self, initial_codepoints=None):
        self.__codepoints = []
        if initial_codepoints is not None:
            self.__codepoints.extend(initial_codepoints)

    def asTuples (self):
        return []

    def negate (self):
        return None

    def difference (self, other):
        pass

