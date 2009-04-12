import PyWXSB.XMLSchema as xs
import StringIO
print xs.datatypes

from PyWXSB.exceptions_ import *
import PyWXSB.utility as utility
import PyWXSB.templates as templates

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
    """Base class for something that requires fairly complex activity
    in order to generate its literal value."""

    # Either a STD or a subclass of _Enumeration_mixin, this is the
    # class in which the referenced object is a member.
    __ownerClass = None
    def __init__ (self, **kw):
        # NB: Pre-extend __init__
        self.__ownerClass = kw.get('type_definition', None)

    def _addTypePrefix (self, text):
        if self.__ownerClass is not None:
            text = '%s.%s' % (pythonLiteral(self.__ownerClass), text)
        return text

class ReferenceFacetMember (ReferenceLiteral):
    __facetClass = None

    def __init__ (self, **kw):
        variable = kw.get('variable', None)
        assert (variable is None) or isinstance(variable, xs.facets.Facet)

        if variable is not None:
            kw.setdefault('type_definition', variable.ownerTypeDefinition())
            self.__facetClass = type(variable)
        self.__facetClass = kw.get('facet_class', self.__facetClass)

        super(ReferenceFacetMember, self).__init__(**kw)

    def asLiteral (self, **kw):
        return self._addTypePrefix('_CF_%s' % (self.__facetClass.Name(),))

class ReferenceClass (ReferenceLiteral):
    __namedComponent = None
    __AnonymousIndex = 0

    def __init__ (self, **kw):
        self.__namedComponent = kw['named_component']

    @classmethod
    def _NextAnonymousIndex (cls):
        rv = cls.__AnonymousIndex
        cls.__AnonymousIndex += 1
        return rv

    __GEN_Attr = '_ReferenceClass_asLiteral'
    __ComponentTagMap = {
        Namespace.XMLSchemaModule().structures.SimpleTypeDefinition: 'STD'
        , Namespace.XMLSchemaModule().structures.ComplexTypeDefinition: 'CTD'
        , Namespace.XMLSchemaModule().structures.ElementDeclaration: 'ED'
        }
    def asLiteral (self, **kw):
        rv = getattr(self.__namedComponent, self.__GEN_Attr, None)
        if rv is None:
            name = self.__namedComponent.ncName()
            if name is None:
                name = '_%s_ANON%d' % (self.__ComponentTagMap.get(type(self.__namedComponent), 'COMPONENT'), self._NextAnonymousIndex())
            #rv = '_STD_%s' % (name,)
            rv = name
            setattr(self.__namedComponent, self.__GEN_Attr, rv)
        return PrefixNamespace(self.__namedComponent.targetNamespace(), rv)

class ReferenceFacet (ReferenceLiteral):

    __facet = None

    def __init__ (self, **kw):
        self.__facet = kw['facet']
        super(ReferenceFacet, self).__init__(**kw)
        
    def asLiteral (self, **kw):
        return '%s._CF_%s' % (pythonLiteral(self.__facet.ownerTypeDefinition()), self.__facet.Name())
        

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

    # String instances go out as their representation
    if isinstance(value, types.StringTypes):
        return utility.QuotedEscaped(value,)

    if isinstance(value, xs.facets.Facet):
        return pythonLiteral(ReferenceFacet(facet=value))

    # Treat pattern elements as their value
    if isinstance(value, xs.facets._PatternElement):
        return pythonLiteral(value.pattern)

    # Treat enumeration elements as their value
    if isinstance(value, xs.facets._EnumerationElement):
        return pythonLiteral(value.value())

    if isinstance(value, (xs.structures.SimpleTypeDefinition, xs.structures.ComplexTypeDefinition) ):
        #return PrefixNamespace(value.targetNamespace(), value.ncName())
        return pythonLiteral(ReferenceClass(named_component=value))

    # Other special cases
    if isinstance(value, ReferenceLiteral):
        return value.asLiteral()

    if value is None:
        return 'None'

    raise Exception('Unexpected literal type %s' % (type(value),))
    print 'Unexpected literal type %s' % (type(value),)
    return str(value)


def GenerateFacets (outf, td):
    facet_instances = []
    for (fc, fi) in td.facets().items():
        #if (fi is None) or (fi.ownerTypeDefinition() != td):
        #    continue
        if (fi is None) and (fc in td.baseTypeDefinition().facets()):
            # Nothing new here
            continue
        if (fi is not None) and (fi.ownerTypeDefinition() != td):
            # Did this one in an ancestor
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
            if (fi.superFacet() is not None):
                argset['super_facet'] = fi.superFacet()
            if isinstance(fi, xs.facets.CF_enumeration):
                argset['enum_prefix'] = fi.enumPrefix()
        facet_var = ReferenceFacetMember(type_definition=td, facet_class=fc)
        outf.write("%s = %s(%s)\n" % pythonLiteral( (facet_var, fc, argset )))
        facet_instances.append(pythonLiteral(facet_var))
        if (fi is not None) and is_collection:
            for i in fi.items():
                if isinstance(i, xs.facets._EnumerationElement):
                    enum_member = ReferenceEnumerationMember(type_definition=td, facet_instance=fi, enumeration_element=i)
                    outf.write("%s = %s.addEnumeration(unicode_value=%s)\n" % pythonLiteral( (enum_member, facet_var, i.unicodeValue() )))
                    if fi.enumPrefix() is not None:
                        outf.write("%s_%s = %s\n" % (fi.enumPrefix(), i.tag(), pythonLiteral(enum_member)))
                if isinstance(i, xs.facets._PatternElement):
                    outf.write("%s.addPattern(pattern=%s)\n" % pythonLiteral( (facet_var, i.pattern )))
    if 2 <= len(facet_instances):
        map_args = ",\n   ".join(facet_instances)
    else:
        map_args = ','.join(facet_instances)
    outf.write("%s._InitializeFacetMap(%s)\n" % (pythonLiteral(td), map_args))

def GenerateSTD (std, **kw):
    generate_facets = kw.get('generate_facets', False)
    outf = StringIO.StringIO()

    parent_classes = [ pythonLiteral(std.baseTypeDefinition()) ]
    enum_facet = std.facets().get(xs.facets.CF_enumeration, None)
    if (enum_facet is not None) and (enum_facet.ownerTypeDefinition() == std):
        parent_classes.append('bindings.PyWXSB_enumeration_mixin')
        
    template_map = { }
    template_map['std'] = pythonLiteral(std)
    template_map['superclasses'] = ', '.join(parent_classes)

    if xs.structures.SimpleTypeDefinition.VARIETY_absent == std.variety():
        assert False
        return None
    elif xs.structures.SimpleTypeDefinition.VARIETY_atomic == std.variety():
        template = '''
# Atomic SimpleTypeDefinition
class %{std} (%{superclasses}):
    """%{description}"""
    pass
'''
        template_map['description'] = ''
    elif xs.structures.SimpleTypeDefinition.VARIETY_list == std.variety():
        template = '''
class %{std} (datatypes._PST_list):
    """%{description}"""

    # Type for items in the list
    _ItemType = %{itemtype}
'''
        template_map['itemtype'] = pythonLiteral(std.itemTypeDefinition())
        template_map['description'] = templates.replaceInText('Simple type that is a list of %{itemtype}', **template_map)
    elif xs.structures.SimpleTypeDefinition.VARIETY_union == std.variety():
        template = '''
class %{std} (datatypes._PST_union):
    """%{description}"""
    # Types of potential union members
    _MemberTypes = ( %{membertypes}, )
'''
        template_map['membertypes'] = ", ".join( [ pythonLiteral(_mt) for _mt in std.memberTypeDefinitions() ])
        template_map['description'] = templates.replaceInText('Simple type that is a union of %{membertypes}', **template_map)

    if 0 == len(template_map['description']):
        template_map['description'] = 'No information'
    outf.write(templates.replaceInText(template, **template_map))

    if generate_facets:
        # If generating datatype_facets, throw away the class garbage
        outf = StringIO.StringIO()
        if std.isBuiltin():
            GenerateFacets(outf, std)
    else:
        GenerateFacets(outf, std)
    return outf.getvalue()

def GenerateCTD (ctd, **kw):
    return templates.replaceInText('''
# Complex type %{ctd}
class %{ctd}:
    pass
''', ctd=pythonLiteral(ctd))

def GenerateED (ed, **kw):
    outf = StringIO.StringIO()
    template_map = { }
    template_map['class'] = pythonLiteral(ReferenceClass(named_component=ed))
    template_map['element_name'] = pythonLiteral(ed.ncName())
    if (ed.SCOPE_global == ed.scope()):
        template_map['element_scope'] = pythonLiteral(None)
    else:
        template_map['element_scope'] = pythonLiteral(ed.scope())
    template_map['base_datatype'] = pythonLiteral(ReferenceClass(named_component=ed.typeDefinition()))
    outf.write(templates.replaceInText('''
# ElementDeclaration
class %{class} (bindings.PyWXSB_element):
    _ElementName = %{element_name}
    _ElementScope = %{element_scope}
    _TypeDefinition = %{base_datatype}
''', **template_map))
    return outf.getvalue()


GeneratorMap = {
    xs.structures.SimpleTypeDefinition : GenerateSTD
  , xs.structures.ElementDeclaration : GenerateED
  , xs.structures.ComplexTypeDefinition : GenerateCTD
}

def GeneratePython (input, **kw):
    try:
        wxs = xs.schema().CreateFromDOM(minidom.parse(input))
        TargetNamespace = wxs.getTargetNamespace()
        emit_order = wxs.orderedComponents()
        outf = StringIO.StringIO()
    
        import_prefix = 'PyWXSB.XMLSchema.'
        if TargetNamespace == Namespace.XMLSchema:
            import_prefix = ''
        
        outf.write(templates.replaceInText('''
import %{import_prefix}facets as facets
import %{import_prefix}datatypes as datatypes
import PyWXSB.bindings as bindings

NamespacePrefix = 'tns'

def CreateFromDocument (xml):
    """Parse the given XML and use the document element to create a Python instance."""
    dom = minidom.parseString(xml)
    return CreateFromDOM(dom.documentElement)

def CreateFromDOM (node):
    """Create a Python instance from the given DOM node.
    The node tag must correspond to an element declaration in this module."""
    ncname = node.tagName
    if 0 <= ncname.find(':'):
        ncname = name.split(':', 1)[1]
    cls = globals().get(ncname, None)
    if cls is None:
        raise UnrecognizedElementError('No class available for %s' % (ncname,))
    if not issubclass(cls, bindings.PyWXSB_element):
        raise NotAnElementError('Tag %s does not exist as element in module' % (ncname,))
    return cls.CreateFromDOM(node)

''', import_prefix=import_prefix))
    
        for td in emit_order:
            generator = GeneratorMap.get(type(td), None)
            if generator is None:
                continue
            outf.write(generator(td, **kw))
    
        return outf.getvalue()
    
    except Exception, e:
        sys.stderr.write("%s processing %s:\n" % (e.__class__, file))
        traceback.print_exception(*sys.exc_info())
        return None
    
