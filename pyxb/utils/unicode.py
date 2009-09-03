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

def RangeUnion (seq1, seq2):
    seq = seq1[:]
    seq.extend(seq2)
    seq.sort()
    rv = []
    r = seq[0]
    for ri in xrange(1, len(seq)):
        nr = seq[ri]
        if r[1] < nr[0]:
            rv.append(r)
            r = nr
        else:
            r = (r[0], max(r[1], nr[1]))
    rv.append(r)
    return rv

def RangeDifference (seq1, seq2):
    rv = []
    i1 = i2 = 1
    k = seq1[0]
    d = seq2[0]
    while True:
        

                
            

    

print RangeUnion([ (0, 4) ], [ (3, 7) ])
print RangeUnion([ (0, 4) ], [ (7, 9) ])
print RangeUnion([ (0, 100) ], [ (7, 9), (21, 42), (84, 120) ])
