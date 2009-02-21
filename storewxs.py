import PyWXSB.XMLSchema as xs

import sys
import traceback
from xml.dom import minidom
from xml.dom import Node

files = sys.argv[1:]
if 0 == len(files):
    files = [ 'schemas/xml.xsd', 'xml.wxs' ]

xsd_file = files[0]
wxs_file = files[1]

wxs = xs.schema()
try:
    wxs.processDocument(minidom.parse(xsd_file))
    ns = wxs.getTargetNamespace()
    print 'Storing %s in %s' % (ns.uri(), wxs_file)
    ns.saveToFile(wxs_file)
except Exception, e:
    sys.stderr.write("%s processing %s:\n" % (e.__class__, xsd_file))
    traceback.print_exception(*sys.exc_info())

