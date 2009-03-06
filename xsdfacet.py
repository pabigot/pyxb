import PyWXSB.XMLSchema as xs
import PyWXSB.Namespace as Namespace
#from PyWXSB.generate import PythonGenerator as Generator

import types
import sys
import traceback
from xml.dom import minidom
from xml.dom import Node

Namespace.XMLSchema.modulePath(None)

def facetLiteral (value):
    if isinstance(value, xs.datatypes._PST_mixin):
        return value.pythonLiteral()
    if isinstance(value, xs.facets.Facet):
        #return '%s.XsdSuperType()._CF_%s' % (value.ownerTypeDefinition().ncName(), value.Name())
        return '%s._CF_%s' % (value.ownerTypeDefinition().ncName(), value.Name())
    if isinstance(value, types.StringType):
        return "'%s'" % (value,)
    if isinstance(value, types.UnicodeType):
        return "u'%s'" % (value,)
    if isinstance(value, xs.facets._PatternElement):
        return facetLiteral(value.pattern)
    if isinstance(value, xs.facets._EnumerationElement):
        return facetLiteral(value.value)
    if isinstance(value, xs.structures.SimpleTypeDefinition):
        return value.ncName()
    print type(value)
    return str(value)

try:
    wxs = xs.schema().CreateFromDOM(minidom.parse('schemas/XMLSchema.xsd'))
    ns = wxs.getTargetNamespace()

    type_defs = ns.typeDefinitions()
    emit_order = []
    while 0 < len(type_defs):
        new_type_defs = []
        for td in type_defs:
            if not isinstance(td, xs.structures.SimpleTypeDefinition):
                continue
            if not td.isBuiltin():
                continue
            dep_types = td.dependentTypeDefinitions()
            ready = True
            for dtd in dep_types:
                if dtd == td:
                    print 'Direct loop for %s' % (td,)
                    continue
                if not (dtd in emit_order):
                    print '%s fails due to %s' % (td, dtd)
                    ready = False
                    break
            if ready:
                emit_order.append(td)
            else:
                new_type_defs.append(td)
        type_defs = new_type_defs

    outf = file('datatypesi.py', 'w')
    outf.write("from datatypes import *\n")

    for td in emit_order:
        if not isinstance(td, xs.structures.SimpleTypeDefinition):
            continue
        if td.isBuiltin():
            for (fc, fi) in td.facets().items():
                if (fi is None) and (fc in td.baseTypeDefinition().facets()):
                    # Nothing new here
                    continue
                if (fi is not None) and (fi.ownerTypeDefinition() != td):
                    # Did this one in an ancestor
                    continue
                argset = { }
                is_collection = issubclass(fc, xs.facets._CollectionFacet_mixin)
                if issubclass(fc, xs.facets._LateDatatype_mixin):
                    argset['value_datatype'] = td.baseTypeDefinition()
                if fi is not None:
                    if not is_collection:
                        argset['value'] = fi.value()
                    if fi.superFacet() is not None:
                        argset['super_facet'] = fi.superFacet()
                facet_var = '%s._CF_%s' % (td.ncName(), fc.Name())
                outf.write("%s = facets.CF_%s(%s)\n" % (facet_var, fc.Name(), ', '.join([ '%s=%s' % (key, facetLiteral(val)) for (key, val) in argset.items() ])))
                if (fi is not None) and is_collection:
                    for i in fi.items():
                        outf.write("%s.setFromKeywords(value=%s)\n" % (facet_var, facetLiteral(i)))

except Exception, e:
    sys.stderr.write("%s processing %s:\n" % (e.__class__, file))
    traceback.print_exception(*sys.exc_info())


