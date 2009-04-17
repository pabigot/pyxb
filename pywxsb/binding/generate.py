import pywxsb.xmlschema as xs
import StringIO
import datetime

from pywxsb.exceptions_ import *
import pywxsb.utils.utility as utility
import pywxsb.utils.templates as templates
import pywxsb.binding
import pywxsb.Namespace as Namespace

import types
import sys
import traceback
from xml.dom import minidom
from xml.dom import Node

UniqueInBinding = set()
PostscriptItems = []

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

    def setLiteral (self, literal):
        self.__literal = literal
        return literal

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

        self.setLiteral(self._addTypePrefix('_CF_%s' % (self.__facetClass.Name(),), **kw))

class ReferenceParticle (ReferenceLiteral):
    __particle = None

    def __init__ (self, particle, **kw):
        self.__particle = particle
        super(ReferenceParticle, self).__init__(**kw)

        template_map = { }
        template_map['min_occurs'] = pythonLiteral(int(particle.minOccurs()), **kw)
        if particle.maxOccurs() is None:
            template_map['max_occurs'] = pythonLiteral(particle.maxOccurs(), **kw)
        else:
            template_map['max_occurs'] = pythonLiteral(int(particle.maxOccurs()), **kw)
        assert particle.term() is not None
        template_map['term'] = pythonLiteral(particle.term(), **kw)
        self.setLiteral(templates.replaceInText('pywxsb.binding.content.Particle(%{min_occurs}, %{max_occurs}, %{term})', **template_map))

class ReferenceWildcard (ReferenceLiteral):
    __wildcard = None

    def __init__ (self, wildcard, **kw):
        self.__wildcard = wildcard
        super(ReferenceWildcard, self).__init__(**kw)
        
        template_map = { }
        template_map['Wildcard'] = 'pywxsb.binding.content.Wildcard'
        if (xs.structures.Wildcard.NC_any == wildcard.namespaceConstraint()):
            template_map['nc'] = templates.replaceInText('%{Wildcard}.NC_any', **template_map)
        elif isinstance(wildcard.namespaceConstraint(), set):
            namespaces = []
            for ns in wildcard.namespaceConstrant():
                if ns is None:
                    namespace.append(None)
                else:
                    namespace.append(ns.uri())
            template_map['nc'] = 'set(%s)' % (",".join( [ repr(_ns) for _ns in namespaces ]))
        else:
            assert isinstance(wildcard.namespaceConstraint(), tuple)
            ns = wildcard.namespaceConstrant()[1]
            if ns is not None:
                ns = ns.uri()
            template_map['nc'] = templates.replaceInText('(%{Wildcard}.NC_not, %s)' % (repr(ns),), **template_map)
        template_map['pc'] = wildcard.processContents()
        self.setLiteral(templates.replaceInText('%{Wildcard}(process_contents=%{Wildcard}.PC_%{pc}, namespace_constraint=%{nc})', **template_map))

class ReferenceSchemaComponent (ReferenceLiteral):
    __component = None

    __anonymousIndex = 0
    @classmethod
    def __NextAnonymousIndex (cls):
        cls.__anonymousIndex += 1
        return cls.__anonymousIndex

    __ComponentTagMap = {
        Namespace.XMLSchemaModule().structures.SimpleTypeDefinition: 'STD'
        , Namespace.XMLSchemaModule().structures.ComplexTypeDefinition: 'CTD'
        , Namespace.XMLSchemaModule().structures.ElementDeclaration: 'ED'
        , Namespace.XMLSchemaModule().structures.ModelGroup: 'MG'
        }

    def __init__ (self, component, **kw):
        self.__component = component
        btns = kw['binding_target_namespace']
        tns = None
        try:
            tns = self.__component.targetNamespace()
        except:
            tns = btns
        is_in_binding = (btns == tns) or (tns is None)
            
        name = self.__component.nameInBinding()
        if is_in_binding and (name is None):
            global UniqueInBinding

            # The only components that are allowed to be nameless at
            # this point are ones in the binding we're generating.
            # @todo should not have to special case XMLSchema
            if not (is_in_binding or (Namespace.XMLSchema == tns)):
                raise LogicError('Attempt to reference unnamed component not in binding: %s' % (component,))

            # The initial name is the name of the component, or if the
            # component can't be named the name of something else
            # relevant.
            name = self.__component.bestNCName()

            # Element declarations may be local, in which case we want
            # to incorporate the parentage in the name.
            parent = self.__component
            while isinstance(parent, xs.structures.ElementDeclaration):
                ac = parent.ancestorComponent()
                if ac is None:
                    ac = parent.owner()
                if ac is not None:
                    while (ac is not None) and (ac.bestNCName() is None):
                        ac = ac.owner()
                    ancestor_name = None
                    if ac is not None:
                        ancestor_name = ac.bestNCName()
                    if ancestor_name is None:
                        ancestor_name = 'unknown'
                    name = '%s_%s' % (ancestor_name, name)
                parent = ac
            protected = False
            if name is None:
                tag = self.__ComponentTagMap.get(type(self.__component), None)
                if tag is None:
                    raise LogicError('Not prepared for reference to component type %s' % (self.__component.__class__.__name__,))
                name = '_%s_ANON_%d' % (tag, self.__NextAnonymousIndex())
                protected = True
            name = utility.PrepareIdentifier(name, UniqueInBinding, protected=protected)
            self.__component.setNameInBinding(name)
        if not is_in_binding:
            mp = None
            if Namespace.XMLSchema == tns:
                mp = 'datatypes'
            elif tns is not None:
                mp = tns.modulePath()
                assert mp is not None
            if mp is not None:
                name = '%s.%s' % (mp, name)
        self.setLiteral(name)

class ReferenceFacet (ReferenceLiteral):
    __facet = None

    def __init__ (self, **kw):
        self.__facet = kw['facet']
        super(ReferenceFacet, self).__init__(**kw)
        self.setLiteral('%s._CF_%s' % (pythonLiteral(self.__facet.ownerTypeDefinition(), **kw), self.__facet.Name()))

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

        self.setLiteral(self._addTypePrefix(self.enumerationElement.tag(), **kw))

def pythonLiteral (value, **kw):
    # For dictionaries, apply translation to all values (not keys)
    if isinstance(value, types.DictionaryType):
        return ', '.join([ '%s=%s' % (k, pythonLiteral(v, **kw)) for (k, v) in value.items() ])

    # For lists, apply translation to all members
    if isinstance(value, types.ListType):
        return [ pythonLiteral(_v, **kw) for _v in value ]

    # For other collection types, do what you do for list
    if isinstance(value, (types.TupleType, set)):
        return type(value)(pythonLiteral(list(value), **kw))

    # Value is a binding value for which there should be an
    # enumeration constant.  Return that constant.
    if isinstance(value, xs.facets._Enumeration_mixin):
        return pythonLiteral(ReferenceEnumerationMember(enum_value=value, **kw))

    # Value is an instance of a Python binding, e.g. one of the
    # XMLSchema datatypes.  Use its value, applying the proper prefix
    # for the module.
    if isinstance(value, pywxsb.binding.basis.simpleTypeDefinition):
        return PrefixModule(value, value.pythonLiteral())

    if isinstance(value, type):
        if issubclass(value, pywxsb.binding.basis.simpleTypeDefinition):
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

    # Particles expand to a pywxsb.binding.content.Particle instance
    if isinstance(value, xs.structures.Particle):
        return pythonLiteral(ReferenceParticle(value, **kw))

    # Wildcards expand to a pywxsb.binding.content.Wildcard instance
    if isinstance(value, xs.structures.Wildcard):
        return pythonLiteral(ReferenceWildcard(value, **kw))

    # Schema components have a single name through their lifespan
    if isinstance(value, xs.structures._SchemaComponent_mixin):
        return pythonLiteral(ReferenceSchemaComponent(value, **kw))

    # Other special cases
    if isinstance(value, ReferenceLiteral):
        return value.asLiteral()

    # Standard Python types
    if isinstance(value, (types.NoneType, types.BooleanType, types.FloatType, types.IntType, types.LongType)):
        return repr(value)

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
        parent_classes.append('pywxsb.binding.basis.enumeration_mixin')
        
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
# List SimpleTypeDefinition
class %{std} (pywxsb.binding.basis.STD_list):
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
# Union SimpleTypeDefinition
class %{std} (pywxsb.binding.basis.STD_union):
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

    need_content = False
    if (ctd.CT_EMPTY == ctd.contentType()):
        ctd_parent_class = pywxsb.binding.basis.CTD_empty
        prolog_template = '''
# Complex type %{ctd} with empty content
class %{ctd} (pywxsb.binding.basis.CTD_empty):
'''
        pass
    elif (ctd.CT_SIMPLE == ctd.contentType()[0]):
        ctd_parent_class = pywxsb.binding.basis.CTD_simple
        content_type = ctd.contentType()[1]
        prolog_template = '''
# Complex type %{ctd} with simple content type %{basetype}
class %{ctd} (pywxsb.binding.basis.CTD_simple):
    _TypeDefinition = %{basetype}
'''
        template_map['basetype'] = pythonLiteral(content_type, **kw)
    elif (ctd.CT_MIXED == ctd.contentType()[0]):
        ctd_parent_class = pywxsb.binding.basis.CTD_mixed
        content_type = ctd.contentType()[1]
        template_map['particle'] = pythonLiteral(content_type, **kw)
        need_content = True
        prolog_template = '''
# Complex type %{ctd} with mixed content
class %{ctd} (pywxsb.binding.basis.CTD_mixed):
'''
    elif (ctd.CT_ELEMENT_ONLY == ctd.contentType()[0]):
        ctd_parent_class = pywxsb.binding.basis.CTD_element
        content_type = ctd.contentType()[1]
        template_map['particle'] = pythonLiteral(content_type, **kw)
        need_content = True
        prolog_template = '''
# Complex type %{ctd} with element-only content
class %{ctd} (pywxsb.binding.basis.CTD_element):
'''
    if need_content:
        global PostscriptItems
        PostscriptItems.append(templates.replaceInText('''
%{ctd}._Content = %{particle}
''', **template_map))
        


    # Support for deconflicting attributes, elements, and reserved symbols
    class_keywords = frozenset(ctd_parent_class._ReservedSymbols)
    class_unique = set()

    definitions = []

    # Deconflict elements first, attributes are lower priority.
    # Expectation is that all elements that have the same tag in the
    # XML are combined into the same instance member, even if they
    # have different types.  Determine what name that should be, and
    # whether there might be multiple instances of elements of that
    # name.
    element_name_map = { }
    element_uses = []
    datatype_map = { }
    datatype_items = []
    if isinstance(content_type, xs.structures.Particle):
        plurality_data = content_type.pluralityData().nameBasedPlurality()
        for (name, (is_plural, types)) in plurality_data.items():
            ef_map = { }
            aux_init = []
            used_field_name = utility.PrepareIdentifier(name, class_unique, class_keywords)
            element_name_map[name] = used_field_name

            ef_map['python_field_name'] = used_field_name
            ef_map['field_inspector'] = used_field_name
            ef_map['field_mutator'] = utility.PrepareIdentifier('set' + used_field_name[0].upper() + used_field_name[1:], class_unique, class_keywords)
            ef_map['field_name'] = utility.PrepareIdentifier(name, class_unique, class_keywords, private=True)
            ef_map['value_field_name'] = utility.PrepareIdentifier('%s_%s' % (template_map['ctd'], name), class_unique, class_keywords, private=True)
            ef_map['is_plural'] = repr(is_plural)
            ef_map['field_tag'] = pythonLiteral(name, **kw)
            element_uses.append(templates.replaceInText('%{field_tag} : %{field_name}', **ef_map))
            datatype_items.append("%s : [ %s ]" % (ef_map['field_tag'], ','.join(pythonLiteral(types, **kw))))
            if 0 == len(aux_init):
                ef_map['aux_init'] = ''
            else:
                ef_map['aux_init'] = ', ' + ', '.join(aux_init)
            definitions.append(templates.replaceInText('''
    # Element %{field_tag} uses Python identifier %{python_field_name}
    %{field_name} = pywxsb.binding.content.ElementUse(%{field_tag}, '%{python_field_name}', '%{value_field_name}', %{is_plural}%{aux_init})
    def %{field_inspector} (self):
        """Get the value of the %{field_tag} element."""
        return self.%{field_name}.value(self)
    def %{field_mutator} (self, new_value):
        """Set the value of the %{field_tag} element.  Raises BadValueTypeException
        if the new value is not consistent with the element's type."""
        return self.%{field_name}.setValue(self, new_value)''', **ef_map))

    PostscriptItems.append('''
%s._UpdateElementDatatypes({
    %s
})''' % (template_map['ctd'], ",\n    ".join(datatype_items)))


    # Create definitions for all attributes.
    attribute_name_map = { }
    attribute_uses = []
    for au in ctd.attributeUses():
        ad = au.attributeDeclaration()
        au_map = { }
        attr_name = ad.ncName()
        used_attr_name = utility.PrepareIdentifier(attr_name, class_unique, class_keywords)
        attribute_name_map[attr_name] = used_attr_name
        au_map['python_attr_name'] = used_attr_name
        au_map['attr_inspector'] = used_attr_name
        au_map['attr_mutator'] = utility.PrepareIdentifier('set' + used_attr_name[0].upper() + used_attr_name[1:], class_unique, class_keywords)
        au_map['attr_name'] = utility.PrepareIdentifier(attr_name, class_unique, class_keywords, private=True)
        au_map['value_attr_name'] = utility.PrepareIdentifier('%s_%s' % (template_map['ctd'], attr_name), class_unique, class_keywords, private=True)
        au_map['attr_tag'] = pythonLiteral(attr_name, **kw)
        au_map['attr_type'] = pythonLiteral(ad.typeDefinition(), **kw)
        au_map['constraint_value'] = pythonLiteral(None, **kw)
        vc = au.valueConstraint()
        if vc is None:
            vc = ad.valueConstraint()
        aux_init = []
        if vc is not None:
            if au.VC_fixed == vc[0]:
                aux_init.append('fixed=True')
            aux_init.append('unicode_default=%s' % (pythonLiteral(ad.valueConstraint()[0], **kw),))
        if au.required():
            aux_init.append('required=True')
        if au.prohibited():
            aux_init.append('prohibited=True')
        if 0 == len(aux_init):
            au_map['aux_init'] = ''
        else:
            aux_init.insert(0, '')
            au_map['aux_init'] = ', '.join(aux_init)
        attribute_uses.append(templates.replaceInText('%{attr_tag} : %{attr_name}', **au_map))
        definitions.append(templates.replaceInText('''
    # Attribute %{attr_tag} uses Python identifier %{python_attr_name}
    %{attr_name} = pywxsb.binding.content.AttributeUse(%{attr_tag}, '%{python_attr_name}', '%{value_attr_name}', %{attr_type}%{aux_init})
    def %{attr_inspector} (self):
        """Get the value of the %{attr_tag} attribute."""
        return self.%{attr_name}.value(self)
    def %{attr_mutator} (self, new_value):
        """Set the value of the %{attr_tag} attribute.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.%{attr_name}.setValue(self, new_value)''', **au_map))

    if ctd.attributeWildcard() is not None:
        definitions.append('_AttributeWildcard = %s' % (pythonLiteral(ctd.attributeWildcard(), **kw),))
    if ctd.hasWildcardElement():
        definitions.append('_HasWildcardElement = True')

    template = ''.join([prolog_template,
                "    ", "\n    ".join(definitions), "\n",
                "    _AttributeMap = {\n        ", ",\n        ".join(attribute_uses), "\n    }\n",
                "    _ElementMap = {\n        ", ",\n        ".join(element_uses), "\n    }\n\n" ])
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
class %{class} (pywxsb.binding.basis.element):
    _XsdName = %{element_name}
    _ElementScope = %{element_scope}
    _TypeDefinition = %{base_datatype}
''', **template_map))
    return outf.getvalue()

def GenerateMG (mg, **kw):
    outf = StringIO.StringIO()
    template_map = { }
    template_map['model_group'] = pythonLiteral(mg, **kw)

    # My this gets ugly.  What we're doing here is looking at all
    # elements that can appear immediately in the XML at this group;
    # i.e., the top level elements in this model group and any
    # contained model groups.  We're figuring out what unique element
    # tags might appear.  For each tag, we're looking at the occurence
    # ranges and types of the elements it might represent.  We're
    # gonna spit all that out as a comment near the model group
    # declaration.
    #
    # @todo Handle the obscure case where the same tag is used for two
    # distinct elements both of which can appear.  This might happen
    # with a sequence of sequences, for example, and results in the
    # wrong occurence counts.  NB: This can't be handled at this
    # level; needs to be done within the element.
    #
    # @todo Gotta handle wildcards in here too.

    field_names = { }
    for e in mg.elementDeclarations():
        field_names.setdefault(e.ncName(), []).append(e)
    field_decls = []
    for fn in field_names.keys():
        decl = []
        may_be_plural = False
        field_type = None
        min_occurs = None
        max_occurs = -1
        for f in field_names.get(fn):
            if field_type is None:
                field_type = f.typeDefinition()
            if field_type == f.typeDefinition():
                # Nothing technically wrong with this, though it might
                # confuse the user.
                pass
            if isinstance(f.owner(), xs.structures.Particle):
                p = f.owner()
                may_be_plural = may_be_plural or p.isPlural()
                if min_occurs is None:
                    min_occurs = p.minOccurs()
                elif p.minOccurs() < min_occurs:
                    min_occurs = p.minOccurs()
                if p.maxOccurs() is None:
                    max_occurs = None
                elif (max_occurs is not None) and (p.maxOccurs() > max_occurs):
                    max_occurs = p.maxOccurs()
            if f.ancestorComponent() is not None:
                assert isinstance(f.ancestorComponent(), xs.structures.ModelGroup)
                mgd = f.ancestorComponent().modelGroupDefinition()
                if mgd is not None:
                    decl.append("%s:%s from group %s" % (fn, pythonLiteral(f.typeDefinition(), **kw), mgd.ncName()))
                else:
                    decl.append("%s:%s from unnamed group" % (fn, pythonLiteral(f.typeDefinition(), **kw)))
            else:
                decl.append("%s:%s from orphan %s" % (fn, pythonLiteral(f.typeDefinition(), **kw), f))
        if min_occurs is None:
            min_occurs = 1
        min_occurs = int(min_occurs)
        if max_occurs is None:
            max_occurs = '*'
        elif -1 == max_occurs:
            max_occurs = 1
        else:
            max_occurs = int(max_occurs)
        field_decls.append("# + %s %s [%d..%s]" % (fn, pythonLiteral(f.typeDefinition(), **kw), min_occurs, max_occurs))
        if decl:
            field_decls.append("#  - " + "\n#  - ".join(decl))
    template_map['field_descr'] = "\n".join(field_decls)

    outf.write(templates.replaceInText('''
# %{model_group} top level elements:
%{field_descr}
%{model_group} = pywxsb.binding.content.ModelGroup()
''', **template_map))
    template_map['compositor'] = 'pywxsb.binding.content.ModelGroup.C_%s' % (mg.compositorToString().upper(),)
    template_map['particles'] = ','.join( [ pythonLiteral(_p, **kw) for _p in mg.particles() ])
    PostscriptItems.append(templates.replaceInText('''
%{model_group}._setContent(%{compositor}, [ %{particles} ])
''', **template_map))
    return outf.getvalue()

GeneratorMap = {
    xs.structures.SimpleTypeDefinition : GenerateSTD
  , xs.structures.ElementDeclaration : GenerateED
  , xs.structures.ComplexTypeDefinition : GenerateCTD
  , xs.structures.ModelGroup : GenerateMG
}

def GeneratePython (**kw):
    global UniqueInBinding
    global PostscriptItems
    UniqueInBinding.clear()
    PostscriptItems = []
    try:
        schema = kw.get('schema', None)
        schema_file = kw.get('schema_file', None)
        if schema is None:
            if schema_file is None:
                raise Exception('No input provided')
            schema = xs.schema().CreateFromDOM(minidom.parse(schema_file))
        if schema_file is None:
            schema_file = '<not provided>'

        generator_kw = kw.copy()
        generator_kw['binding_target_namespace'] = schema.getTargetNamespace()

        emit_order = schema.orderedComponents()
        outf = StringIO.StringIO()
    
        import_prefix = 'pywxsb.xmlschema.'
        if schema.getTargetNamespace() == Namespace.XMLSchema:
            import_prefix = ''

        template_map = { }
        template_map['input'] = schema_file
        template_map['date'] = str(datetime.datetime.now())
        template_map['version'] = 'UNSPECIFIED'
        tns = schema.getTargetNamespace()
        if tns is not None:
            tns = tns.uri()
        template_map['targetNamespace'] = repr(tns)
        template_map['namespaces'] = ', '.join( [ repr(_ns.uri()) for _ns in schema.namespaces() ] )
        template_map['import_prefix'] = import_prefix

        import_namespaces = [ ]
        for ns in schema.namespaces():
            if ns == schema.getTargetNamespace():
                continue
            if ns.modulePath() is None:
                if not ns.isBuiltinNamespace():
                    print 'WARNING: Dependency on %s with no module path' % (ns.uri(),)
                continue
            import_namespaces.append(ns)
        template_map['aux_imports'] = "\n".join( [ 'import %s' % (_ns.modulePath(),) for _ns in import_namespaces ])

        outf.write(templates.replaceInText('''# PyWXSB bindings for %{input}
# Generated %{date} by PyWXSB version %{version}
import %{import_prefix}facets as facets
import %{import_prefix}datatypes as datatypes
import pywxsb.binding
from xml.dom import minidom
from xml.dom import Node
# Import bindings for namespaces listed in schema xmlns
%{aux_imports}

Namespace = %{targetNamespace}
NamespaceDependencies = [ %{namespaces} ]

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
    if not issubclass(cls, pywxsb.binding.basis.element):
        raise NotAnElementError('Tag %s does not exist as element in module' % (ncname,))
    return cls.CreateFromDOM(node)

''', **template_map))
    
        # Give priority for identifiers to element declarations
        for td in emit_order:
            if isinstance(td, xs.structures.ElementDeclaration):
                ReferenceSchemaComponent(td, **generator_kw).asLiteral()

        for td in emit_order:
            generator = GeneratorMap.get(type(td), None)
            if generator is None:
                continue
            outf.write(generator(td, **generator_kw))
    
        outf.write(''.join(PostscriptItems))
        return outf.getvalue()
    
    except Exception, e:
        sys.stderr.write("%s processing %s:\n" % (e.__class__, file))
        traceback.print_exception(*sys.exc_info())
        return None
    
