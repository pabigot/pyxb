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

UniqueInUse = set()

Namespace.XMLSchema.setModulePath('xs')

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

    # The value to be used as a literal for this object
    __literal = None

    def __init__ (self, **kw):
        # NB: Pre-extend __init__
        self.__ownerClass = kw.get('type_definition', None)

    def _literal (self, literal):
        self.__literal = literal

    def asLiteral (self):
        return self.__literal

    def _addTypePrefix (self, text, **kw):
        if self.__ownerClass is not None:
            text = '%s.%s' % (pythonLiteral(self.__ownerClass, **kw), text)
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

        self._literal(self._addTypePrefix('_CF_%s' % (self.__facetClass.Name(),), **kw))

class ReferenceClass (ReferenceLiteral):
    __namedComponent = None

    __GEN_Attr = '_ReferenceClass_asLiteral'
    __ComponentTagMap = {
        Namespace.XMLSchemaModule().structures.SimpleTypeDefinition: 'STD'
        , Namespace.XMLSchemaModule().structures.ComplexTypeDefinition: 'CTD'
        , Namespace.XMLSchemaModule().structures.ElementDeclaration: 'ED'
        }

    def __init__ (self, **kw):
        self.__namedComponent = kw['named_component']

        global UniqueInUse
        btns = kw['binding_target_namespace']
        tns = self.__namedComponent.targetNamespace()

        if btns == tns:
            rv = getattr(self.__namedComponent, self.__GEN_Attr, None)
            if rv is None:
                name = self.__namedComponent.ncName()
                if name is None:
                    name = '_%s_ANON' % (self.__ComponentTagMap.get(type(self.__namedComponent), 'COMPONENT'),)
                rv = utility.PrepareIdentifier(name, UniqueInUse)
                setattr(self.__namedComponent, self.__GEN_Attr, rv)
        else:
            if Namespace.XMLSchema == tns:
                mp = 'datatypes'
            else:
                mp = tns.modulePath()
            rv = self.__namedComponent.ncName()
            if mp is not None:
                rv = '%s.%s' % (mp, rv)
        self._literal(rv)
    
class ReferenceFacet (ReferenceLiteral):

    __facet = None

    def __init__ (self, **kw):
        self.__facet = kw['facet']
        super(ReferenceFacet, self).__init__(**kw)
        self._literal('%s._CF_%s' % (pythonLiteral(self.__facet.ownerTypeDefinition(), **kw), self.__facet.Name()))
        

class ReferenceEnumerationMember (ReferenceLiteral):
    enumerationElement = None
    
    def __init__ (self, **kw):
        # NB: Pre-extended __init__
        
        # All we really need is the enumeration element, so we can get
        # its tag, and a type definition or datatype, so we can create
        # the proper prefix.

        # See if we were given a value, from which we can extract the
        # other information.
        value = kw.get('enum_value', None)
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

        self._literal(self._addTypePrefix(self.enumerationElement.tag(), **kw))

def pythonLiteral (value, **kw):
    # For dictionaries, apply translation to all values (not keys)
    if isinstance(value, types.DictionaryType):
        return ', '.join([ '%s=%s' % (k, pythonLiteral(v, **kw)) for (k, v) in value.items() ])

    # For tuples, apply translation to all members
    if isinstance(value, types.TupleType):
        return tuple([ pythonLiteral(_v, **kw) for _v in value ])

    # Value is a binding value for which there should be an
    # enumeration constant.  Return that constant.
    if isinstance(value, xs.facets._Enumeration_mixin):
        return pythonLiteral(ReferenceEnumerationMember(enum_value=value, **kw))

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
        return pythonLiteral(ReferenceFacet(facet=value, **kw))

    # Treat pattern elements as their value
    if isinstance(value, xs.facets._PatternElement):
        return pythonLiteral(value.pattern)

    # Treat enumeration elements as their value
    if isinstance(value, xs.facets._EnumerationElement):
        return pythonLiteral(value.value())

    if isinstance(value, xs.structures._NamedComponent_mixin):
        return pythonLiteral(ReferenceClass(named_component=value, **kw))

    # Other special cases
    if isinstance(value, ReferenceLiteral):
        return value.asLiteral()

    if value is None:
        return 'None'

    raise Exception('Unexpected literal type %s' % (type(value),))
    print 'Unexpected literal type %s' % (type(value),)
    return str(value)


def GenerateFacets (outf, td, **kw):
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
        facet_var = ReferenceFacetMember(type_definition=td, facet_class=fc, **kw)
        outf.write("%s = %s(%s)\n" % pythonLiteral( (facet_var, fc, argset ), **kw))
        facet_instances.append(pythonLiteral(facet_var, **kw))
        if (fi is not None) and is_collection:
            for i in fi.items():
                if isinstance(i, xs.facets._EnumerationElement):
                    enum_member = ReferenceEnumerationMember(type_definition=td, facet_instance=fi, enumeration_element=i, **kw)
                    outf.write("%s = %s.addEnumeration(unicode_value=%s)\n" % pythonLiteral( (enum_member, facet_var, i.unicodeValue() ), **kw))
                    if fi.enumPrefix() is not None:
                        outf.write("%s_%s = %s\n" % (fi.enumPrefix(), i.tag(), pythonLiteral(enum_member, **kw)))
                if isinstance(i, xs.facets._PatternElement):
                    outf.write("%s.addPattern(pattern=%s)\n" % pythonLiteral( (facet_var, i.pattern ), **kw))
    if 2 <= len(facet_instances):
        map_args = ",\n   ".join(facet_instances)
    else:
        map_args = ','.join(facet_instances)
    outf.write("%s._InitializeFacetMap(%s)\n" % (pythonLiteral(td, **kw), map_args))

def GenerateSTD (std, **kw):
    generate_facets = kw.get('generate_facets', False)
    outf = StringIO.StringIO()

    parent_classes = [ pythonLiteral(std.baseTypeDefinition(), **kw) ]
    enum_facet = std.facets().get(xs.facets.CF_enumeration, None)
    if (enum_facet is not None) and (enum_facet.ownerTypeDefinition() == std):
        parent_classes.append('bindings.PyWXSB_enumeration_mixin')
        
    template_map = { }
    template_map['std'] = pythonLiteral(std, **kw)
    template_map['superclasses'] = ', '.join(parent_classes)
    template_map['name'] = pythonLiteral(std.ncName(), **kw)

    if xs.structures.SimpleTypeDefinition.VARIETY_absent == std.variety():
        assert False
        return None
    elif xs.structures.SimpleTypeDefinition.VARIETY_atomic == std.variety():
        template = '''
# Atomic SimpleTypeDefinition
class %{std} (%{superclasses}):
    """%{description}"""

    # The name of this type definition within the schema
    _XsdName = %{name}
'''
        template_map['description'] = ''
    elif xs.structures.SimpleTypeDefinition.VARIETY_list == std.variety():
        template = '''
class %{std} (datatypes._PST_list):
    """%{description}"""

    # The name of this type definition within the schema
    _XsdName = %{name}

    # Type for items in the list
    _ItemType = %{itemtype}
'''
        template_map['itemtype'] = pythonLiteral(std.itemTypeDefinition(), **kw)
        template_map['description'] = templates.replaceInText('Simple type that is a list of %{itemtype}', **template_map)
    elif xs.structures.SimpleTypeDefinition.VARIETY_union == std.variety():
        template = '''
class %{std} (datatypes._PST_union):
    """%{description}"""

    # The name of this type definition within the schema
    _XsdName = %{name}

    # Types of potential union members
    _MemberTypes = ( %{membertypes}, )
'''
        template_map['membertypes'] = ", ".join( [ pythonLiteral(_mt, **kw) for _mt in std.memberTypeDefinitions() ])
        template_map['description'] = templates.replaceInText('Simple type that is a union of %{membertypes}', **template_map)

    if 0 == len(template_map['description']):
        template_map['description'] = 'No information'
    outf.write(templates.replaceInText(template, **template_map))

    if generate_facets:
        # If generating datatype_facets, throw away the class garbage
        outf = StringIO.StringIO()
        if std.isBuiltin():
            GenerateFacets(outf, std, **kw)
    else:
        GenerateFacets(outf, std, **kw)
    return outf.getvalue()

def GenerateCTD (ctd, **kw):
    content_type = None
    prolog_template = None
    template_map = { }
    template_map['ctd'] = pythonLiteral(ctd, **kw)

    if (ctd.CT_EMPTY == ctd.contentType()):
        prolog_template = '''
# Complex type %{ctd} with empty content
class %{ctd} (bindings.PyWXSB_CTD_empty):
'''
        pass
    elif (ctd.CT_SIMPLE == ctd.contentType()[0]):
        content_type = ctd.contentType()[1]
        prolog_template = '''
# Complex type %{ctd} with simple content type %{basetype}
class %{ctd} (bindings.PyWXSB_CTD_simple):
    _TypeDefinition = %{basetype}
'''
        template_map['basetype'] = pythonLiteral(content_type, **kw)
    elif (ctd.CT_MIXED == ctd.contentType()[0]):
        content_type = ctd.contentType()[1]
        prolog_template = '''
# Complex type %{ctd} with mixed content
class %{ctd} (bindings.PyWXSB_CTD_mixed):
'''
    elif (ctd.CT_ELEMENT_ONLY == ctd.contentType()[0]):
        content_type = ctd.contentType()[1]
        prolog_template = '''
# Complex type %{ctd} with element-only content
class %{ctd} (bindings.PyWXSB_CTD_element):
'''

    attribute_init = []
    attribute_support = []
    class_keywords = frozenset([ '_TypeDefinition' ])
    class_unique = set()
    for au in ctd.attributeUses():
        ad = au.attributeDeclaration()
        au_map = { }
        au_map['attr_name'] = utility.PrepareIdentifier(ad.ncName(), class_unique, class_keywords)
        au_map['attr_tag'] = pythonLiteral(ad.ncName(), **kw)
        au_map['attr_type'] = pythonLiteral(ad.typeDefinition(), **kw)
        attribute_init.append(templates.replaceInText('%{attr_name} = None # %{attr_type}', **au_map))
        au_map['constraint_value'] = pythonLiteral(None, **kw)
        vc = au.valueConstraint()
        if vc is None:
            vc = ad.valueConstraint()
        aux_init = []
        if vc is not None:
            aux_init.append('default_value=%s' % (pythonLiteral(ad.valueConstraint()[0], **kw),))
        if au.required():
            aux_init.append('required=True')
        if au.prohibited():
            aux_init.append('prohibited=True')
        if 0 == len(aux_init):
            au_map['aux_init'] = ''
        else:
            aux_init.insert(0, '')
            au_map['aux_init'] = ', '.join(aux_init)
        attribute_support.append(templates.replaceInText("bindings.AttributeUse('%{attr_name}', %{attr_tag}, %{attr_type}%{aux_init})", **au_map))
    
    trailing_comma = ''
    if 1 == len(attribute_support):
        trailing_comma = ','
    template = ''.join( [prolog_template,
                         "    _Attributes = (\n    ", ",\n    ".join(attribute_support), trailing_comma, "\n    )\n\n"
                             ] )

    return templates.replaceInText(template, **template_map)

def GenerateED (ed, **kw):
    outf = StringIO.StringIO()
    template_map = { }
    template_map['class'] = pythonLiteral(ed, **kw)
    template_map['element_name'] = pythonLiteral(ed.ncName(), **kw)
    if (ed.SCOPE_global == ed.scope()):
        template_map['element_scope'] = pythonLiteral(None, **kw)
    else:
        template_map['element_scope'] = pythonLiteral(ed.scope(), **kw)
    template_map['base_datatype'] = pythonLiteral(ed.typeDefinition(), **kw)
    outf.write(templates.replaceInText('''
# ElementDeclaration
class %{class} (bindings.PyWXSB_element):
    _XsdName = %{element_name}
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

        generator_kw = kw.copy()
        generator_kw['binding_target_namespace'] = wxs.getTargetNamespace()

        emit_order = wxs.orderedComponents()
        outf = StringIO.StringIO()
    
        import_prefix = 'PyWXSB.XMLSchema.'
        if wxs.getTargetNamespace() == Namespace.XMLSchema:
            import_prefix = ''

        outf.write(templates.replaceInText('''
import %{import_prefix}facets as facets
import %{import_prefix}datatypes as datatypes
import PyWXSB.bindings as bindings
from xml.dom import minidom
from xml.dom import Node

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
    
        # Give priority for identifiers to element declarations
        for td in emit_order:
            if isinstance(td, xs.structures.ElementDeclaration):
                ReferenceClass(named_component=td, **generator_kw).asLiteral()

        for td in emit_order:
            generator = GeneratorMap.get(type(td), None)
            if generator is None:
                continue
            outf.write(generator(td, **generator_kw))
    
        return outf.getvalue()
    
    except Exception, e:
        sys.stderr.write("%s processing %s:\n" % (e.__class__, file))
        traceback.print_exception(*sys.exc_info())
        return None
    
