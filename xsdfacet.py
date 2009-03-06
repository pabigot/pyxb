import PyWXSB.XMLSchema as xs
import PyWXSB.Namespace as Namespace
#from PyWXSB.generate import PythonGenerator as Generator

import sys
import traceback
from xml.dom import minidom
from xml.dom import Node

Namespace.XMLSchema.modulePath('xs.datatypes')

try:
    wxs = xs.schema().CreateFromDOM(minidom.parse('schemas/XMLSchema.xsd'))
    ns = wxs.getTargetNamespace()
    for td in ns.typeDefinitions():
        if not isinstance(td, xs.structures.SimpleTypeDefinition):
            continue
        if td.isBuiltin():
            print 'class %s (%s):' % (td.ncName(), td.baseTypeDefinition().ncName())
            for (fc, fi) in td.facets().items():
                if fi is None:
                    if not (fc in td.baseTypeDefinition().facets()):
                        print '   _CF_%s = xs.facets.CF_%s()' % (fc.Name(), fc.Name())
                    continue
                if (fi.superFacet() is None) and (fi.baseTypeDefinition() == td):
                    continue
                if fi.ownerTypeDefinition() != td:
                    continue
                print '   %s' % (fi,)

except Exception, e:
    sys.stderr.write("%s processing %s:\n" % (e.__class__, file))
    traceback.print_exception(*sys.exc_info())


