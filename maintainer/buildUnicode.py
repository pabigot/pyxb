import textwrap
import re

# You'll need these:
# http://www.unicode.org/Public/3.1-Update/UnicodeData-3.1.0.txt
# http://www.unicode.org/Public/3.1-Update/Blocks-4.txt

def condenseCodepoints (codepoints):
    ranges = []
    codepoints = list(codepoints)
    codepoints.sort()
    range_last = range_min = codepoints[0]
    range_next = range_last + 1
    for ri in xrange(1, len(codepoints)):
        if codepoints[ri] == range_next:
            range_last = range_next
            range_next += 1
            continue
        ranges.append( (range_min, range_last) )
        range_last = range_min = codepoints[ri]
        range_next = range_last + 1
    ranges.append( (range_min, range_last) )
    return ranges

def rangesToPython (ranges, indent=11, width=67):
    text = ', '.join( [ '(0x%06x, 0x%06x)' % _r for _r in ranges ] )
    wrapped = textwrap.wrap(text, 67)
    return ("\n%s" % (' ' * indent,)).join(wrapped)

def emitCategoryMap (data_file='UnicodeData-3.1.0.txt'):
    category_map = { }
    unicode_data = file(data_file)
    while True:
        line = unicode_data.readline()
        fields = line.split(';')
        if 1 >= len(fields):
            break
        codepoint = int(fields[0], 16)
        category = fields[2]
    
        category_map.setdefault(category, set()).add(codepoint)
        category_map.setdefault(category[0], set()).add(codepoint)
    
    print '# Unicode general category properties: %d properties' % (len(category_map),)
    print 'PropertyMap = {'
    for k in sorted(category_map.keys()):
        v = category_map.get(k)
        print '  # %s: %d codepoints' % (k, len(v))
        print "  %-4s : ( %s )," % ("'%s'" % k, rangesToPython(condenseCodepoints(v), indent=11, width=67))
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
        block_map.setdefault(block, set()).add( (rmin, rmax) )

    print '# Unicode code blocks: %d blocks' % (len(block_map),)
    print 'BlockMap = {'
    for k in sorted(block_map.keys()):
        v = block_map.get(k)
        print '  %s : (' % (repr(k),)
        print '     %s' % (rangesToPython(v, indent=6, width=67),)
        print '  ),'
    print '  }'

emitBlockMap()
emitCategoryMap()
