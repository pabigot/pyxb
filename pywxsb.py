import PyWXSB.XMLSchema as xs

import sys
from xml.dom import minidom
from xml.dom import Node

schema_file = 'schemas/XMLSchema.xsd'
if 1 < len(sys.argv):
    schema_file = sys.argv[1]

wxs = xs.Schema()

wxs.processDocument(minidom.parse(schema_file))

