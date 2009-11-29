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

"""Utility to generate the code point sets defined by the Unicode standard.

You'll need these files:

 - U{http://www.unicode.org/Public/3.1-Update/UnicodeData-3.1.0.txt}
 - U{http://www.unicode.org/Public/3.1-Update/Blocks-4.txt}

Invoke this script, redirecting the output to
C{pyxb/utils/unicode_data.py}.

"""

import textwrap
import re

def condenseCodepoints (codepoints):
    ranges = []
    codepoints = list(codepoints)
    codepoints.sort()
    range_min = None
    for ri in xrange(len(codepoints)):
        codepoint = codepoints[ri]
        if not isinstance(codepoint, tuple):
            if range_min is None:
                range_last = range_min = codepoint
                range_next = range_last + 1
                continue
            if codepoint == range_next:
                range_last = codepoint
                range_next += 1
                continue
        if range_min is not None:
            ranges.append( (range_min, range_last) )
        if isinstance(codepoint, tuple):
            range_min = None
            ranges.append(codepoint)
        else:
            range_last = range_min = codepoints[ri]
            range_next = range_last + 1
    if range_min is not None:
        ranges.append( (range_min, range_last) )
    return ranges

def rangesToPython (ranges, indent=11, width=67):
    ranges.sort()
    text = ', '.join( [ '(0x%06x, 0x%06x)' % _r for _r in ranges ] )
    text += ','
    wrapped = textwrap.wrap(text, 67)
    return ("\n%s" % (' ' * indent,)).join(wrapped)

def emitCategoryMap (data_file='UnicodeData-3.1.0.txt'):
    category_map = {}
    unicode_data = file(data_file)
    range_first = None
    while True:
        line = unicode_data.readline()
        fields = line.split(';')
        if 1 >= len(fields):
            break
        codepoint = int(fields[0], 16)
        char_name = fields[1]
        category = fields[2]
    
        if char_name.endswith(', First>'):
            assert range_first is None
            range_first = codepoint
            continue
        if range_first is not None:
            assert char_name.endswith(', Last>')
            codepoint = ( range_first, codepoint )
            range_first = None
        category_map.setdefault(category, []).append(codepoint)
        category_map.setdefault(category[0], []).append(codepoint)
    
    print '# Unicode general category properties: %d properties' % (len(category_map),)
    print 'PropertyMap = {'
    for k in sorted(category_map.keys()):
        v = category_map.get(k)
        print '  # %s: %d codepoint markers (*not* codepoints)' % (k, len(v))
        print "  %-4s : CodePointSet([" % ("'%s'" % k,)
        print "           %s" % (rangesToPython(condenseCodepoints(v), indent=11, width=67),)
        print "         ]),"
    print '  }'

def emitBlockMap (data_file='Blocks-4.txt'):
    block_map = { }
    block_re = re.compile('(?P<min>[0-9A-F]+)\.\.(?P<max>[0-9A-F]+);\s(?P<block>.*)$')
    block_data = file(data_file)
    while True:
        line = block_data.readline()
        if 0 == len(line):
            break
        mo = block_re.match(line)
        if mo is None:
            continue
        rmin = int(mo.group('min'), 16)
        rmax = int(mo.group('max'), 16)
        block = mo.group('block').replace(' ', '')
        block_map.setdefault(block, []).append( (rmin, rmax) )

    print '# Unicode code blocks: %d blocks' % (len(block_map),)
    print 'BlockMap = {'
    for k in sorted(block_map.keys()):
        v = block_map.get(k)
        print '  %s : CodePointSet(' % (repr(k),)
        print '     %s' % (rangesToPython(v, indent=6, width=67),)
        print '  ),'
    print '  }'

print '''# Unicode property and category maps.

from unicode import CodePointSet
'''

emitBlockMap()
emitCategoryMap()
