import PyWXSB.XMLSchema as xs

import sys
import traceback
from xml.dom import minidom
from xml.dom import Node

files = sys.argv[1:]
if 0 == len(files):
    files = [ 'schemas/XMLSchema.xsd' ]

for file in files:
    try:
        wxs = xs.schema.CreateFromDOM(minidom.parse(file))
    except Exception, e:
        sys.stderr.write("%s processing %s:\n" % (e.__class__, file))
        traceback.print_exception(*sys.exc_info())

