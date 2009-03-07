import PyWXSB.XMLSchema as xs
print xs.datatypes

from PyWXSB.exceptions_ import *
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
        return 'datatypes.%s' % (text,)
    if value.__module__ == xs.facets.__name__:
        return 'facets.%s' % (text,)
    raise IncompleteImplementationError('PrefixModule needs support for non-builtin instances')

class ReferenceLiteral (object):

    # Either a STD or a subclass of _Enumeration_mixin, this is the
    # class in which the referenced object is a member.
    __ownerClass = None
    def __init__ (self, **kw):
        self.__ownerClass = kw.get('type_definition', None)

    def _addTypePrefix (self, text):
        if self.__ownerClass is not None:
            text = '%s.%s' % (pythonLiteral(self.__ownerClass), text)
        return text

class ReferenceFacetMember (ReferenceLiteral):
    __facetClass = None

    def __init__ (self, **kw):
        super(ReferenceFacetMember, self).__init__(**kw)
        self.__facetClass = kw['facet_class']

    def asLiteral (self, **kw):
        return self._addTypePrefix('_CF_%s' % (self.__facetClass.Name(),))

class ReferenceEnumerationMember (ReferenceLiteral):
    enumerationElement = None
    
    def __init__ (self, **kw):
        # NB: Pre-extended __init__
        
        # All we really need is the enumeration element, so we can get
        # its tag, and a type definition or datatype, so we can create
        # the proper prefix.

        # See if we were given a value, from which we can extract the
        # other information.
        value = kw.get('value', None)
        assert (value is None) or isinstance(value, xs.facets._Enumeration_mixin)

        # Must provide facet_instance, or a value from which it can be
        # obtained.
        facet_instance = kw.get('facet_instance', None)
        if facet_instance is None:
            assert isinstance(value, xs.facets._Enumeration_mixin)
            facet_instance = value._CF_enumeration
        assert isinstance(facet_instance, xs.facets.CF_enumeration)

        # Must provide the enumeration_element, or a facet_instance
        # and value from which it can be identified.
        self.enumerationElement = kw.get('enumeration_element', None)
        if self.enumerationElement is None:
            assert value is not None
            self.enumerationElement = facet_instance.elementForValue(value)
        assert isinstance(self.enumerationElement, xs.facets._EnumerationElement)

        # If no type definition was provided, use the value datatype
        # for the facet.
        kw.setdefault('type_definition', facet_instance.valueDatatype())

        super(ReferenceEnumerationMember, self).__init__(**kw)

    def asLiteral (self, **kw):
        return self._addTypePrefix(self.enumerationElement.tag())

def pythonLiteral (value):
    # For dictionaries, apply translation to all values (not keys)
    if isinstance(value, types.DictionaryType):
        return ', '.join([ '%s=%s' % (k, pythonLiteral(v)) for (k, v) in value.items() ])

    # For tuples, apply translation to all members
    if isinstance(value, types.TupleType):
        return tuple([ pythonLiteral(_v) for _v in value ])

    # Value is a binding value for which there should be an
    # enumeration constant.  Return that constant.
    if isinstance(value, xs.facets._Enumeration_mixin):
        return pythonLiteral(ReferenceEnumerationMember(value=value))

    # Value is an instance of a Python binding, e.g. one of the
    # XMLSchema datatypes.  Use its value, applying the proper prefix
    # for the module.
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
        return pythonLiteral(value.pattern)
    if isinstance(value, xs.facets._EnumerationElement):
        return pythonLiteral(value.value())
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
                vdt = td
                if fc.LateDatatypeBindsSuperclass():
                    vdt = vdt.baseTypeDefinition()
                argset['value_datatype'] = vdt
            if fi is not None:
                if not is_collection:
                    argset['value'] = fi.value()
                if fi.superFacet() is not None:
                    argset['super_facet'] = fi.superFacet()
                if isinstance(fi, xs.facets.CF_enumeration):
                    argset['enum_prefix'] = fi.enumPrefix()
            facet_var = ReferenceFacetMember(type_definition=td, facet_class=fc)
            outf.write("%s = %s(%s)\n" % pythonLiteral( (facet_var, fc, argset )))
            if (fi is not None) and is_collection:
                for i in fi.items():
                    if isinstance(i, xs.facets._EnumerationElement):
                        enum_member = ReferenceEnumerationMember(type_definition=td, facet_instance=fi, enumeration_element=i)
                        outf.write("%s = %s.addKeyword(unicode_value=%s)\n" % pythonLiteral( (enum_member, facet_var, i.unicodeValue() )))
                    if isinstance(i, xs.facets._PatternElement):
                        outf.write("%s.addPattern(pattern=%s)\n" % pythonLiteral( (facet_var, i.pattern )))

except Exception, e:
    sys.stderr.write("%s processing %s:\n" % (e.__class__, file))
    traceback.print_exception(*sys.exc_info())

