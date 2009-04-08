import PyWXSB.XMLSchema as xs
import PyWXSB.Namespace as Namespace
from PyWXSB.generate import PythonGenerator as Generator

import sys
import traceback
from xml.dom import minidom
from xml.dom import Node

files = sys.argv[1:]
if 0 == len(files):
    files = [ 'schemas/kml21.xsd' ]

Namespace.XMLSchema.setModulePath('xs.datatypes')

for file in files:
    try:
        wxs = xs.schema().CreateFromDOM(minidom.parse(file))
        print "\nComponents in the schema:"
        for c in wxs.components():
            cd = c.dependentComponents()
            print 'Instance of %s depends on %d others' % (c.__class__.__name__, len(cd))
    except Exception, e:
        sys.stderr.write("%s processing %s:\n" % (e.__class__, file))
        traceback.print_exception(*sys.exc_info())


