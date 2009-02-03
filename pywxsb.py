import PyWXSB.XMLSchema as xs

import sys
import traceback
from xml.dom import minidom
from xml.dom import Node

files = sys.argv[1:]
if 0 == len(files):
    files = [ 'schemas/XMLSchema.xsd' ]

for file in files:
    wxs = xs.schema()
    try:
        wxs.processDocument(minidom.parse(file))
    except Exception, e:
        print '%s processing %s:' % (e.__class__, file)
        traceback.print_exception(*sys.exc_info())

