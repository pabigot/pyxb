import dict
import urllib2
import pyxb.utils.domutils as domutils
import sys

word = 'xml'
if 1 < len(sys.argv):
    word = sys.argv[1]

# Create a REST-style query to retrieve the information about this dictionary.
uri = 'http://services.aonaware.com/DictService/DictService.asmx/Define?word=%s' % (word,)
rxml = urllib2.urlopen(uri).read()
resp = dict.CreateFromDOM(domutils.StringToDOM(rxml))

print 'Definitions of %s:' % (resp.Word,)
for definition in resp.Definitions.Definition:
    print 'From %s (%s):' % (definition.Dictionary.Name, definition.Dictionary.Id)
    print definition.WordDefinition
    print
