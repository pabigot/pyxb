import PyWXSB.XMLSchema as xs

import sys
from xml.dom import minidom
from xml.dom import Node

files = sys.argv[1:]
if 0 == len(files):
    files = [ 'schemas/XMLSchema.xsd' ]

for file in files:
    wxs = xs.schema()
    wxs.processDocument(minidom.parse(file))

