import PyWXSB.XMLSchema as xs
print xs.datatypes

import PyWXSB.utility as utility

import PyWXSB.Namespace as Namespace
#from PyWXSB.generate import PythonGenerator as Generator

import types
import sys
import traceback
from xml.dom import minidom
from xml.dom import Node

Namespace.XMLSchema.setModulePath('xs')

def PrefixNamespace (ns, text):
    if Namespace.XMLSchema == ns:
        mp = 'datatypes'
    else:
        mp = ns.modulePath()
    if mp is not None:
        text = '%s.%s' % (mp, text)
    return text

def PrefixModule (value, text=None):
    if text is None:
        text = value.__name__
    if value.__module__ == xs.datatypes.__name__:
        text = 'datatypes.%s' % (text,)
    elif value.__module__ == xs.facets.__name__:
        text = 'facets.%s' % (text,)
    else:
        assert False
    return text

class ReferenceLiteral (object):
    typeDefinition = None
    def __init__ (self, **kw):
        self.typeDefinition = kw['type_definition']

    def _addTypePrefix (self, text):
        if self.typeDefinition is not None:
            text = '%s.%s' % (facetLiteral(self.typeDefinition), text)
        return text

class ReferenceFacetMember (ReferenceLiteral):
    typeDefinition = None
    facetClass = None

    def __init__ (self, **kw):
        super(ReferenceFacetMember, self).__init__(**kw)
        self.facetClass = kw.get('facet_class', None)

    def asLiteral (self, **kw):
        return self._addTypePrefix('_CF_%s' % (self.facetClass.Name(),))

class ReferenceEnumerationMember (ReferenceLiteral):
    typeDefinition = None
    facetInstance = None
    enumerationElement = None
    
    def __init__ (self, **kw):
        super(ReferenceEnumerationMember, self).__init__(**kw)
        self.facetInstance = kw.get('facet_instance', None)
        self.enumerationElement = kw.get('enumeration_element', None)

    def asLiteral (self, **kw):
        return self._addTypePrefix('%s_%s' % (self.facetInstance.enumPrefix(), self.enumerationElement.tag))


def facetLiteral (value):
    global TargetNamespace
    if isinstance(value, xs.facets._Enumeration_mixin):
        return PrefixModule(value, value._CF_enumeration.tagForValue(value))
    if isinstance(value, xs.datatypes._PST_mixin):
        return PrefixModule(value, value.pythonLiteral())
    if isinstance(value, type):
        if issubclass(value, xs.datatypes._PST_mixin):
            return PrefixModule(value)
        if issubclass(value, xs.facets.Facet):
            return PrefixModule(value)
    if isinstance(value, xs.facets.Facet):
        #return '%s.XsdSuperType()._CF_%s' % (value.ownerTypeDefinition().ncName(), value.Name())
        return '%s._CF_%s' % (value.ownerTypeDefinition().ncName(), value.Name())
    if isinstance(value, types.StringTypes):
        return utility.QuotedEscaped(value,)
    if isinstance(value, xs.facets._PatternElement):
        return facetLiteral(value.pattern)
    if isinstance(value, xs.facets._EnumerationElement):
        return facetLiteral(value.value)
    if isinstance(value, xs.structures.SimpleTypeDefinition):
        return PrefixNamespace(value.targetNamespace(), value.ncName())
    if isinstance(value, ReferenceLiteral):
        return value.asLiteral()
    raise Exception('Unexpected literal type %s' % (type(value),))
    print 'Unexpected literal type %s' % (type(value),)
    return str(value)

files = sys.argv[1:]
if 0 == len(files):
    files = [ 'schemas/XMLSchema.xsd' ]

try:
    wxs = xs.schema().CreateFromDOM(minidom.parse(files[0]))
    TargetNamespace = wxs.getTargetNamespace()
    #TargetNamespace.setModulePath(None)

    type_defs = TargetNamespace.typeDefinitions()
    emit_order = []
    while 0 < len(type_defs):
        new_type_defs = []
        for td in type_defs:
            if not isinstance(td, xs.structures.SimpleTypeDefinition):
                continue
            if td.targetNamespace() != TargetNamespace:
                continue
            if (Namespace.XMLSchema == TargetNamespace) and (not td.isBuiltin()):
                continue
            dep_types = td.dependentTypeDefinitions()
            ready = True
            for dtd in dep_types:
                if dtd.targetNamespace() != TargetNamespace:
                    continue
                if dtd == td:
                    continue
                if not (dtd in emit_order):
                    ready = False
                    break
            if ready:
                emit_order.append(td)
            else:
                new_type_defs.append(td)
        type_defs = new_type_defs

    outf = file('datatypesi.py', 'w')

    import_prefix = 'PyWXSB.XMLSchema.'
    if TargetNamespace == Namespace.XMLSchema:
        import_prefix = ''
    
    outf.write('''
import %sfacets as facets
import %sdatatypes as datatypes
''' % (import_prefix, import_prefix))

    for td in emit_order:
        #print 'Emitting %d facets in %s' % (len(td.facets()), td)
        for (fc, fi) in td.facets().items():
            if (fi is None) and (fc in td.baseTypeDefinition().facets()):
                # Nothing new here
                #print 'No instance'
                continue
            if (fi is not None) and (fi.ownerTypeDefinition() != td):
                # Did this one in an ancestor
                #print 'Parent instance'
                continue
            argset = { }
            is_collection = issubclass(fc, xs.facets._CollectionFacet_mixin)
            if issubclass(fc, xs.facets._LateDatatype_mixin):
                if fc.LateDatatypeBindsSuperclass():
                    vdt = td.baseTypeDefinition()
                else:
                    vdt = td
                argset['value_datatype'] = vdt
            if fi is not None:
                if not is_collection:
                    argset['value'] = fi.value()
                if fi.superFacet() is not None:
                    argset['super_facet'] = fi.superFacet()
                if isinstance(fi, xs.facets.CF_enumeration):
                    argset['enum_prefix'] = fi.enumPrefix()
            std_class = facetLiteral(td)
            facet_var = facetLiteral(ReferenceFacetMember(type_definition=td, facet_class=fc))
            outf.write("%s = %s(%s)\n" % (facet_var, facetLiteral(fc), ', '.join([ '%s=%s' % (key, facetLiteral(val)) for (key, val) in argset.items() ])))
            if (fi is not None) and is_collection:
                for i in fi.items():
                    argset = { }
                    if isinstance(i, xs.facets._EnumerationElement):
                        enum_member = ReferenceEnumerationMember(type_definition=td, facet_instance=fi, enumeration_element=i)
                        outf.write("%s = %s.addKeyword(unicode_value=%s)\n" % (facetLiteral(enum_member), facet_var, facetLiteral(i.unicodeValue)))

except Exception, e:
    sys.stderr.write("%s processing %s:\n" % (e.__class__, file))
    traceback.print_exception(*sys.exc_info())

