# Copyright 2009, Peter A. Bigot
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain a
# copy of the License at:
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""The really ugly code that generates the Python bindings.  This
whole thing is going to be refactored once customized generation makes
it to the top of the task queue."""

import pyxb
import pyxb.xmlschema as xs
import StringIO
import datetime
import urlparse

from pyxb.utils import utility
from pyxb.utils import templates
from pyxb.utils import domutils
import basis
import content
import datatypes
import facets

import nfa

import types
import sys
import traceback
import xml.dom
import os.path

# Initialize UniqueInBinding with the public identifiers we generate,
# import, or otherwise can't have mucked about with.
UniqueInBinding = set([ 'pyxb', 'sys', 'Namespace', 'CreateFromDocument', 'CreateFromDOM' ])

def PrefixModule (value, text=None):
    if text is None:
        text = value.__name__
    if value.__module__ == datatypes.__name__:
        return 'pyxb.binding.datatypes.%s' % (text,)
    if value.__module__ == facets.__name__:
        return 'pyxb.binding.facets.%s' % (text,)
    raise pyxb.IncompleteImplementationError('PrefixModule needs support for non-builtin instances')

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
        assert (variable is None) or isinstance(variable, facets.Facet)

        if variable is not None:
            kw.setdefault('type_definition', variable.ownerTypeDefinition())
            self.__facetClass = type(variable)
        self.__facetClass = kw.get('facet_class', self.__facetClass)

        super(ReferenceFacetMember, self).__init__(**kw)

        self.setLiteral(self._addTypePrefix('_CF_%s' % (self.__facetClass.Name(),), **kw))

class ReferenceWildcard (ReferenceLiteral):
    __wildcard = None

    def __init__ (self, wildcard, **kw):
        self.__wildcard = wildcard
        super(ReferenceWildcard, self).__init__(**kw)
        
        template_map = { }
        template_map['Wildcard'] = 'pyxb.binding.content.Wildcard'
        if (xs.structures.Wildcard.NC_any == wildcard.namespaceConstraint()):
            template_map['nc'] = templates.replaceInText('%{Wildcard}.NC_any', **template_map)
        elif isinstance(wildcard.namespaceConstraint(), (set, frozenset)):
            namespaces = []
            for ns in wildcard.namespaceConstraint():
                if ns is None:
                    namespaces.append(None)
                else:
                    namespaces.append(ns.uri())
            template_map['nc'] = 'set(%s)' % (",".join( [ repr(_ns) for _ns in namespaces ]))
        else:
            assert isinstance(wildcard.namespaceConstraint(), tuple)
            ns = wildcard.namespaceConstraint()[1]
            if ns is not None:
                ns = ns.uri()
            template_map['nc'] = templates.replaceInText('(%{Wildcard}.NC_not, %{namespace})', namespace=repr(ns), **template_map)
        template_map['pc'] = wildcard.processContents()
        self.setLiteral(templates.replaceInText('%{Wildcard}(process_contents=%{Wildcard}.PC_%{pc}, namespace_constraint=%{nc})', **template_map))

class ReferenceSchemaComponent (ReferenceLiteral):
    __component = None

    def __init__ (self, component, **kw):
        self.__component = component
        binding_module = kw['binding_module']
        rv = binding_module.referenceSchemaComponent(component)
        #print '%s in %s is %s' % (component.expandedName(), binding_module, rv)
        self.setLiteral(rv)

class ReferenceNamespace (ReferenceLiteral):
    __namespace = None

    def __init__ (self, **kw):
        self.__namespace = kw['namespace']
        binding_module = kw['binding_module']
        rv = binding_module.referenceNamespace(self.__namespace)
        #print '%s in %s is %s' % (self.__namespace, binding_module, rv)
        self.setLiteral(rv)

class ReferenceExpandedName (ReferenceLiteral):
    __expandedName = None

    def __init__ (self, **kw):
        self.__expandedName = kw['expanded_name']
        self.setLiteral('pyxb.namespace.ExpandedName(%s, %s)' % (pythonLiteral(self.__expandedName.namespace(), **kw), pythonLiteral(self.__expandedName.localName(), **kw)))

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
        assert (value is None) or isinstance(value, facets._Enumeration_mixin)

        # Must provide facet_instance, or a value from which it can be
        # obtained.
        facet_instance = kw.get('facet_instance', None)
        if facet_instance is None:
            assert isinstance(value, facets._Enumeration_mixin)
            facet_instance = value._CF_enumeration
        assert isinstance(facet_instance, facets.CF_enumeration)

        # Must provide the enumeration_element, or a facet_instance
        # and value from which it can be identified.
        self.enumerationElement = kw.get('enumeration_element', None)
        if self.enumerationElement is None:
            assert value is not None
            self.enumerationElement = facet_instance.elementForValue(value)
        assert isinstance(self.enumerationElement, facets._EnumerationElement)
        if self.enumerationElement.tag() is None:
            self.enumerationElement._setTag(utility.MakeIdentifier(self.enumerationElement.unicodeValue()))

        # If no type definition was provided, use the value datatype
        # for the facet.
        kw.setdefault('type_definition', facet_instance.valueDatatype())

        super(ReferenceEnumerationMember, self).__init__(**kw)

        self.setLiteral(self._addTypePrefix(utility.PrepareIdentifier(self.enumerationElement.tag(), kw['class_unique'], kw['class_keywords']), **kw))

def pythonLiteral (value, **kw):
    # For dictionaries, apply translation to all values (not keys)
    if isinstance(value, types.DictionaryType):
        return ', '.join([ '%s=%s' % (k, pythonLiteral(v, **kw)) for (k, v) in value.items() ])

    # For lists, apply translation to all members
    if isinstance(value, types.ListType):
        return [ pythonLiteral(_v, **kw) for _v in value ]

    # ExpandedName is a tuple, but not here
    if isinstance(value, pyxb.namespace.ExpandedName):
        return pythonLiteral(ReferenceExpandedName(expanded_name=value, **kw))

    # For other collection types, do what you do for list
    if isinstance(value, (types.TupleType, set)):
        return type(value)(pythonLiteral(list(value), **kw))

    # Value is a binding value for which there should be an
    # enumeration constant.  Return that constant.
    if isinstance(value, facets._Enumeration_mixin):
        return pythonLiteral(ReferenceEnumerationMember(enum_value=value, **kw))

    # Value is an instance of a Python binding, e.g. one of the
    # XMLSchema datatypes.  Use its value, applying the proper prefix
    # for the module.
    if isinstance(value, basis.simpleTypeDefinition):
        return PrefixModule(value, value.pythonLiteral())

    if isinstance(value, pyxb.namespace.Namespace):
        return pythonLiteral(ReferenceNamespace(namespace=value, **kw))

    if isinstance(value, type):
        if issubclass(value, basis.simpleTypeDefinition):
            return PrefixModule(value)
        if issubclass(value, facets.Facet):
            return PrefixModule(value)

    # String instances go out as their representation
    if isinstance(value, types.StringTypes):
        return utility.QuotedEscaped(value,)

    if isinstance(value, facets.Facet):
        return pythonLiteral(ReferenceFacet(facet=value, **kw))

    # Treat pattern elements as their value
    if isinstance(value, facets._PatternElement):
        return pythonLiteral(value.pattern)

    # Treat enumeration elements as their value
    if isinstance(value, facets._EnumerationElement):
        return pythonLiteral(value.value())

    # Particles expand to a pyxb.binding.content.Particle instance
    if isinstance(value, xs.structures.Particle):
        return pythonLiteral(ReferenceParticle(value, **kw))

    # Wildcards expand to a pyxb.binding.content.Wildcard instance
    if isinstance(value, xs.structures.Wildcard):
        return pythonLiteral(ReferenceWildcard(value, **kw))

    # Schema components have a single name through their lifespan
    if isinstance(value, xs.structures._SchemaComponent_mixin):
        return pythonLiteral(ReferenceSchemaComponent(value, **kw))

    # Other special cases
    if isinstance(value, ReferenceLiteral):
        return value.asLiteral()

    # Represent namespaces by their URI
    if isinstance(value, pyxb.namespace.Namespace):
        return repr(value.uri())

    # Standard Python types
    if isinstance(value, (types.NoneType, types.BooleanType, types.FloatType, types.IntType, types.LongType)):
        return repr(value)

    raise Exception('Unexpected literal type %s' % (type(value),))
    print 'Unexpected literal type %s' % (type(value),)
    return str(value)


def GenerateModelGroupAll (ctd, mga, binding_module, template_map, **kw):
    mga_tag = '__AModelGroup'
    template_map['mga_tag'] = mga_tag
    lines = []
    lines2 = []
    for ( dfa, is_required ) in mga.particles():
        ( dfa_tag, dfa_lines ) = GenerateContentModel(ctd, dfa, binding_module, **kw)
        lines.extend(dfa_lines)
        template_map['dfa_tag'] = dfa_tag
        template_map['is_required'] = binding_module.literal(is_required, **kw)
        lines2.append(templates.replaceInText('    %{content}.ModelGroupAllAlternative(%{ctd}.%{dfa_tag}, %{is_required}),', **template_map))
    lines.append(templates.replaceInText('%{mga_tag} = %{content}.ModelGroupAll(alternatives=[', **template_map))
    lines.extend(lines2)
    lines.append('])')
    return (mga_tag, lines)

def GenerateContentModel (ctd, automaton, binding_module, **kw):
    cmi = None
    template_map = { }
    template_map['ctd'] = binding_module.literal(ctd, **kw)
    try:
        cmi = '_ContentModel_%d' % (ctd.__contentModelIndex,)
        ctd.__contentModelIndex += 1
    except AttributeError:
        cmi = '_ContentModel'
        ctd.__contentModelIndex = 1
    template_map['cm_tag'] = cmi
    template_map['content'] = 'pyxb.binding.content'
    template_map['state_comma'] = ' '
    lines = []
    lines2 = []
    for (state, transitions) in automaton.items():
        if automaton.end() == state:
            continue
        template_map['state'] = binding_module.literal(state)
        template_map['is_final'] = binding_module.literal(None in transitions)

        lines2.append(templates.replaceInText('%{state_comma} %{state} : %{content}.ContentModelState(state=%{state}, is_final=%{is_final}, transitions=[', **template_map))
        template_map['state_comma'] = ','
        lines3 = []
        for (key, destinations) in transitions.items():
            if key is None:
                continue
            assert 1 == len(destinations)
            template_map['next_state'] = binding_module.literal(list(destinations)[0], **kw)
            if isinstance(key, xs.structures.Wildcard):
                template_map['kw_key'] = 'term'
                template_map['kw_val'] = binding_module.literal(key, **kw)
            elif isinstance(key, nfa.AllWalker):
                (mga_tag, mga_defns) = GenerateModelGroupAll(ctd, key, binding_module, template_map.copy(), **kw)
                template_map['kw_key'] = 'term'
                template_map['kw_val'] = mga_tag
                lines.extend(mga_defns)
            else:
                assert isinstance(key, xs.structures.ElementDeclaration)
                template_map['kw_key'] = 'element_use'
                template_map['kw_val'] = templates.replaceInText('%{ctd}._UseForTag(%{field_tag})', field_tag=binding_module.literal(key.expandedName(), **kw), **template_map)
            lines3.append(templates.replaceInText('%{content}.ContentModelTransition(next_state=%{next_state}, %{kw_key}=%{kw_val}),',
                          **template_map))
        lines2.extend([ '    '+_l for _l in lines3 ])
        lines2.append("])")

    lines.append(templates.replaceInText('%{ctd}.%{cm_tag} = %{content}.ContentModel(state_map = {', **template_map))
    lines.extend(['    '+_l for _l in lines2 ])
    lines.append("})")
    return (cmi, lines)

def GenerateFacets (td, **kw):
    binding_module = kw['binding_module']
    outf = binding_module.bindingIO()
    facet_instances = []
    for (fc, fi) in td.facets().items():
        #if (fi is None) or (fi.ownerTypeDefinition() != td):
        #    continue
        if (fi is None) and (fc in td.baseTypeDefinition().facets()):
            # Nothing new here
            #print 'Skipping %s in %s: already registered' % (fc, td)
            continue
        if (fi is not None) and (fi.ownerTypeDefinition() != td):
            # Did this one in an ancestor
            #print 'Skipping %s in %s: found in ancestor' % (fc, td)
            continue
        argset = { }
        is_collection = issubclass(fc, facets._CollectionFacet_mixin)
        if issubclass(fc, facets._LateDatatype_mixin):
            vdt = td
            if fc.LateDatatypeBindsSuperclass():
                vdt = vdt.baseTypeDefinition()
            argset['value_datatype'] = vdt
        if fi is not None:
            if not is_collection:
                argset['value'] = fi.value()
            if isinstance(fi, facets.CF_enumeration):
                argset['enum_prefix'] = fi.enumPrefix()
        facet_var = ReferenceFacetMember(type_definition=td, facet_class=fc, **kw)
        outf.write("%s = %s(%s)\n" % binding_module.literal( (facet_var, fc, argset ), **kw))
        facet_instances.append(binding_module.literal(facet_var, **kw))
        if (fi is not None) and is_collection:
            for i in fi.items():
                if isinstance(i, facets._EnumerationElement):
                    enum_member = ReferenceEnumerationMember(type_definition=td, facet_instance=fi, enumeration_element=i, **kw)
                    outf.write("%s = %s.addEnumeration(unicode_value=%s)\n" % binding_module.literal( (enum_member, facet_var, i.unicodeValue() ), **kw))
                    if fi.enumPrefix() is not None:
                        outf.write("%s_%s = %s\n" % (fi.enumPrefix(), i.tag(), binding_module.literal(enum_member, **kw)))
                if isinstance(i, facets._PatternElement):
                    outf.write("%s.addPattern(pattern=%s)\n" % binding_module.literal( (facet_var, i.pattern ), **kw))
    if 2 <= len(facet_instances):
        map_args = ",\n   ".join(facet_instances)
    else:
        map_args = ','.join(facet_instances)
    outf.write("%s._InitializeFacetMap(%s)\n" % (binding_module.literal(td, **kw), map_args))

def GenerateSTD (std):

    binding_module = _ModuleNaming_mixin.ComponentBindingModule(std)
    outf = binding_module.bindingIO()
    
    class_keywords = frozenset(basis.simpleTypeDefinition._ReservedSymbols)
    class_unique = set()

    kw = { }
    kw['binding_module'] = binding_module
    kw['class_keywords'] = class_keywords
    kw['class_unique'] = class_unique

    parent_classes = [ binding_module.literal(std.baseTypeDefinition(), **kw) ]
    enum_facet = std.facets().get(facets.CF_enumeration, None)
    if (enum_facet is not None) and (enum_facet.ownerTypeDefinition() == std):
        parent_classes.append('pyxb.binding.basis.enumeration_mixin')
        
    template_map = { }
    template_map['std'] = binding_module.literal(std, **kw)
    template_map['superclasses'] = ''
    if 0 < len(parent_classes):
        template_map['superclasses'] = ', '.join(parent_classes)
    template_map['expanded_name'] = binding_module.literal(std.expandedName(), **kw)
    template_map['namespaceReference'] = binding_module.literal(std.bindingNamespace(), **kw)

    # @todo: Extensions of LIST will be wrong in below

    if xs.structures.SimpleTypeDefinition.VARIETY_absent == std.variety():
        assert False
    elif xs.structures.SimpleTypeDefinition.VARIETY_atomic == std.variety():
        template = '''
# Atomic SimpleTypeDefinition
class %{std} (%{superclasses}):
    """%{description}"""

    _ExpandedName = %{expanded_name}
'''
        template_map['description'] = ''
    elif xs.structures.SimpleTypeDefinition.VARIETY_list == std.variety():
        template = '''
# List SimpleTypeDefinition
# superclasses %{superclasses}
class %{std} (pyxb.binding.basis.STD_list):
    """%{description}"""

    _ExpandedName = %{expanded_name}
    _ItemType = %{itemtype}
'''
        template_map['itemtype'] = binding_module.literal(std.itemTypeDefinition(), **kw)
        template_map['description'] = templates.replaceInText('Simple type that is a list of %{itemtype}', **template_map)
    elif xs.structures.SimpleTypeDefinition.VARIETY_union == std.variety():
        template = '''
# Union SimpleTypeDefinition
# superclasses %{superclasses}
class %{std} (pyxb.binding.basis.STD_union):
    """%{description}"""

    _ExpandedName = %{expanded_name}
    _MemberTypes = ( %{membertypes}, )
'''
        template_map['membertypes'] = ", ".join( [ binding_module.literal(_mt, **kw) for _mt in std.memberTypeDefinitions() ])
        template_map['description'] = templates.replaceInText('Simple type that is a union of %{membertypes}', **template_map)

    if 0 == len(template_map['description']):
        template_map['description'] = 'No information'
    outf.write(templates.replaceInText(template, **template_map))

    generate_facets = False
    if generate_facets:
        # If generating datatype_facets, throw away the class garbage
        outf = StringIO.StringIO()
        if std.isBuiltin():
            GenerateFacets(std, **kw)
    else:
        GenerateFacets(std, **kw)

    if std.name() is not None:
        outf.write(templates.replaceInText("%{namespaceReference}.addCategoryObject('typeBinding', %{localName}, %{std})\n",
                                           localName=binding_module.literal(std.name(), **kw), **template_map))
def elementDeclarationMap (ed, binding_module, **kw):
    template_map = { }
    template_map['name'] = str(ed.expandedName())
    template_map['name_expr'] = binding_module.literal(ed.expandedName(), **kw)
    template_map['namespaceReference'] = binding_module.literal(ed.bindingNamespace(), **kw)
    if (ed.SCOPE_global == ed.scope()):
        template_map['class'] = binding_module.literal(ed, **kw)
        template_map['localName'] = binding_module.literal(ed.name(), **kw)
        template_map['map_update'] = templates.replaceInText("%{namespaceReference}.addCategoryObject('elementBinding', %{localName}, %{class})", **template_map)
    else:
        template_map['scope'] = binding_module.literal(ed.scope(), **kw)
    if ed.abstract():
        template_map['abstract'] = binding_module.literal(ed.abstract(), **kw)
    if ed.nillable():
        template_map['nillable'] = binding_module.literal(ed.nillable(), **kw)
    if ed.default():
        template_map['defaultValue'] = binding_module.literal(ed.default(), **kw)
    template_map['typeDefinition'] = binding_module.literal(ed.typeDefinition(), **kw)
    if ed.substitutionGroupAffiliation():
        template_map['substitution_group'] = binding_module.literal(ed.substitutionGroupAffiliation(), **kw)
    aux_init = []
    for k in ( 'nillable', 'abstract', 'scope' ):
        if k in template_map:
            aux_init.append('%s=%s' % (k, template_map[k]))
    template_map['element_aux_init'] = ''
    if 0 < len(aux_init):
        template_map['element_aux_init'] = ', ' + ', '.join(aux_init)
        
    return template_map

def GenerateCTD (ctd, **kw):
    binding_module = _ModuleNaming_mixin.ComponentBindingModule(ctd)
    outf = binding_module.bindingIO()

    content_type = None
    prolog_template = None
    template_map = { }
    template_map['ctd'] = binding_module.literal(ctd, **kw)
    base_type = ctd.baseTypeDefinition()
    content_type_tag = ctd._contentTypeTag()

    template_map['base_type'] = binding_module.literal(base_type, **kw)
    template_map['namespaceReference'] = binding_module.literal(ctd.bindingNamespace(), **kw)
    template_map['expanded_name'] = binding_module.literal(ctd.expandedName(), **kw)
    template_map['simple_base_type'] = binding_module.literal(None, **kw)
    template_map['contentTypeTag'] = content_type_tag
    template_map['is_abstract'] = repr(not not ctd.abstract())

    need_content = False
    content_basis = None
    if (ctd.CT_SIMPLE == content_type_tag):
        content_basis = ctd.contentType()[1]
        template_map['simple_base_type'] = binding_module.literal(content_basis, **kw)
    elif (ctd.CT_MIXED == content_type_tag):
        content_basis = ctd.contentType()[1]
        need_content = True
    elif (ctd.CT_ELEMENT_ONLY == content_type_tag):
        content_basis = ctd.contentType()[1]
        need_content = True
    need_content = False

    prolog_template = '''
# Complex type %{ctd} with content type %{contentTypeTag}
class %{ctd} (%{superclass}):
    _TypeDefinition = %{simple_base_type}
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_%{contentTypeTag}
    _Abstract = %{is_abstract}
    _ExpandedName = %{expanded_name}
'''

    # Complex types that inherit from non-ur-type complex types should
    # have their base type as their Python superclass, so pre-existing
    # elements and attributes can be re-used.
    inherits_from_base = True
    template_map['superclass'] = binding_module.literal(base_type, **kw)
    if ctd._isHierarchyRoot():
        inherits_from_base = False
        template_map['superclass'] = 'pyxb.binding.basis.complexTypeDefinition'
        assert base_type.nameInBinding() is not None

    # Support for deconflicting attributes, elements, and reserved symbols
    class_keywords = frozenset(basis.complexTypeDefinition._ReservedSymbols)
    class_unique = set()

    # Deconflict elements first, attributes are lower priority.
    # Expectation is that all elements that have the same tag in the
    # XML are combined into the same instance member, even if they
    # have different types.  Determine what name that should be, and
    # whether there might be multiple instances of elements of that
    # name.
    element_name_map = { }
    element_uses = []

    definitions = []

    definitions.append('# Base type is %{base_type}')

    # Retain in the ctd the information about the element
    # infrastructure, so it can be inherited where appropriate in
    # subclasses.

    if isinstance(content_basis, xs.structures.Particle):
        plurality_data = content_basis.pluralityData().nameBasedPlurality()

        outf.postscript().append("\n\n")
        for (expanded_name, (is_plural, ed)) in plurality_data.items():
            # @todo Detect and account for plurality change between this and base
            ef_map = ed._templateMap()
            if ed.scope() == ctd:
                ef_map.update(elementDeclarationMap(ed, binding_module, **kw))
                aux_init = []
                ef_map['is_plural'] = repr(is_plural)
                element_uses.append(templates.replaceInText('%{use}.name() : %{use}', **ef_map))
                if 0 == len(aux_init):
                    ef_map['aux_init'] = ''
                else:
                    ef_map['aux_init'] = ', ' + ', '.join(aux_init)
                ef_map['element_binding'] = utility.PrepareIdentifier('%s_elt' % (ef_map['id'],), class_unique, class_keywords, private=True)
            if ed.scope() != ctd:
                definitions.append(templates.replaceInText('''
    # Element %{id} inherited from %{decl_type_en}''', decl_type_en=str(ed.scope().expandedName()), **ef_map))
                continue

            definitions.append(templates.replaceInText('''
    # Element %{name} uses Python identifier %{id}
    %{use} = pyxb.binding.content.ElementUse(%{name_expr}, '%{id}', '%{key}', %{is_plural}%{aux_init})
    def %{inspector} (self):
        """Get the value of the %{name} element."""
        return self.%{use}.value(self)
    def %{mutator} (self, new_value):
        """Set the value of the %{name} element.  Raises BadValueTypeException
        if the new value is not consistent with the element's type."""
        return self.%{use}.set(self, new_value)''', **ef_map))
            if is_plural:
                definitions.append(templates.replaceInText('''
    def %{appender} (self, new_value):
        """Add the value as another occurrence of the %{name} element.  Raises
        BadValueTypeException if the new value is not consistent with the
        element's type."""
        return self.%{use}.append(self, new_value)''', **ef_map))

            outf.postscript().append(templates.replaceInText('''
%{ctd}._AddElement(pyxb.binding.basis.element(%{name_expr}, %{typeDefinition}%{element_aux_init}))
''', ctd=template_map['ctd'], **ef_map))

        fa = nfa.Thompson(content_basis).nfa()
        fa = fa.buildDFA()
        (cmi, cmi_defn) = GenerateContentModel(ctd=ctd, automaton=fa, binding_module=binding_module, **kw)
        outf.postscript().append("\n".join(cmi_defn))
        outf.postscript().append("\n")

    if need_content:
        PostscriptItems.append(templates.replaceInText('''
%{ctd}._Content = %{particle}
''', **template_map))
        
    # Create definitions for all attributes.
    attribute_uses = []

    # name - String value of expanded name of the attribute (attr_tag, attr_ns)
    # name_expr - Python expression for an expanded name identifying the attribute (attr_tag)
    # use - Binding variable name holding AttributeUse instance (attr_name)
    # id - Python identifier for attribute (python_attr_name)
    # key - String used as dictionary key holding instance value of attribute (value_attr_name)
    # inspector - Name of the method used for inspection (attr_inspector)
    # mutator - Name of the method use for mutation (attr_mutator)
    for au in ctd.attributeUses():
        ad = au.attributeDeclaration()
        assert isinstance(ad.scope(), xs.structures.ComplexTypeDefinition)
        au_map = ad._templateMap()
        if ad.scope() == ctd:
            assert isinstance(au_map, dict)

            assert ad.typeDefinition() is not None
            au_map['attr_type'] = binding_module.literal(ad.typeDefinition(), **kw)
                            
            vc_source = ad
            if au.valueConstraint() is not None:
                vc_source = au
            aux_init = []
            if vc_source.fixed() is not None:
                aux_init.append('fixed=True')
                aux_init.append('unicode_default=%s' % (binding_module.literal(vc_source.fixed(), **kw),))
            elif vc_source.default() is not None:
                aux_init.append('unicode_default=%s' % (binding_module.literal(vc_source.default(), **kw),))
            if au.required():
                aux_init.append('required=True')
            if au.prohibited():
                aux_init.append('prohibited=True')
            if 0 == len(aux_init):
                au_map['aux_init'] = ''
            else:
                aux_init.insert(0, '')
                au_map['aux_init'] = ', '.join(aux_init)
        if au.prohibited():
            attribute_uses.append(templates.replaceInText('%{name_expr} : None', **au_map))
            definitions.append(templates.replaceInText('''
    # Attribute %{id} marked prohibited in this type
    def %{inspector} (self):
        raise pyxb.ProhibitedAttributeError("Attribute %{name} is prohibited in %{ctd}")
    def %{mutator} (self, new_value):
        raise pyxb.ProhibitedAttributeError("Attribute %{name} is prohibited in %{ctd}")
''', ctd=template_map['ctd'], **au_map))
            continue
        if ad.scope() != ctd:
            definitions.append(templates.replaceInText('''
    # Attribute %{id} inherited from %{decl_type_en}''', decl_type_en=str(ad.scope().expandedName()), **au_map))
            continue

        attribute_uses.append(templates.replaceInText('%{use}.name() : %{use}', **au_map))
        definitions.append(templates.replaceInText('''
    # Attribute %{name} uses Python identifier %{id}
    %{use} = pyxb.binding.content.AttributeUse(%{name_expr}, '%{id}', '%{key}', %{attr_type}%{aux_init})
    def %{inspector} (self):
        """Get the attribute value for %{name}."""
        return self.%{use}.value(self)
    def %{mutator} (self, new_value):
        """Set the attribute value for %{name}.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.%{use}.set(self, new_value)''', **au_map))
        


    if ctd.attributeWildcard() is not None:
        definitions.append('_AttributeWildcard = %s' % (binding_module.literal(ctd.attributeWildcard(), **kw),))
    if ctd.hasWildcardElement():
        definitions.append('_HasWildcardElement = True')
    template_map['attribute_uses'] = ",\n        ".join(attribute_uses)
    template_map['element_uses'] = ",\n        ".join(element_uses)
    if inherits_from_base:
        map_decl = '''
    _ElementMap = %{superclass}._ElementMap.copy()
    _ElementMap.update({
        %{element_uses}
    })
    _AttributeMap = %{superclass}._AttributeMap.copy()
    _AttributeMap.update({
        %{attribute_uses}
    })'''
    else:
        map_decl = '''
    _ElementMap = {
        %{element_uses}
    }
    _AttributeMap = {
        %{attribute_uses}
    }'''

    template_map['registration'] = ''
    if ctd.name() is not None:
        template_map['registration'] = templates.replaceInText("%{namespaceReference}.addCategoryObject('typeBinding', %{localName}, %{ctd})",
                                                               localName=binding_module.literal(ctd.name(), **kw), **template_map)
    
    template = ''.join([prolog_template,
               "    ", "\n    ".join(definitions), "\n",
               map_decl, '''
%{registration}

'''])

    outf.write(template, **template_map)

def GenerateED (ed, **kw):
    # Unscoped declarations should never be referenced in the binding.
    assert ed._scopeIsGlobal()

    binding_module = _ModuleNaming_mixin.ComponentBindingModule(ed)
    outf = binding_module.bindingIO()

    template_map = elementDeclarationMap(ed, binding_module, **kw)
    template_map.setdefault('scope', binding_module.literal(None, **kw))
    template_map.setdefault('map_update', '')

    outf.write(templates.replaceInText('''
%{class} = pyxb.binding.basis.element(%{name_expr}, %{typeDefinition}%{element_aux_init})
%{namespaceReference}.addCategoryObject('elementBinding', %{class}.name().localName(), %{class})
''', **template_map))

    if ed.substitutionGroupAffiliation() is not None:
        outf.postscript().append(templates.replaceInText('''
%{class}._setSubstitutionGroup(%{substitution_group})
''', **template_map))

GeneratorMap = {
    xs.structures.SimpleTypeDefinition : GenerateSTD
  , xs.structures.ElementDeclaration : GenerateED
  , xs.structures.ComplexTypeDefinition : GenerateCTD
}

def _PrepareSimpleTypeDefinition (std, nsm, module_context):
    ptd = std.primitiveTypeDefinition(throw_if_absent=False)
    std._templateMap()['_unique'] = nsm.uniqueInClass(std)
    if (ptd is not None) and ptd.hasPythonSupport():
        # Only generate enumeration constants for named simple
        # type definitions that are fundamentally xsd:string
        # values.
        if issubclass(ptd.pythonSupport(), pyxb.binding.datatypes.string):
            enum_facet = std.facets().get(pyxb.binding.facets.CF_enumeration, None)
            if (enum_facet is not None) and (std.expandedName() is not None):
                for ei in enum_facet.items():
                    assert ei.tag() is None, '%s already has a tag' % (ei,)
                    ei._setTag(utility.PrepareIdentifier(ei.unicodeValue(), nsm.uniqueInClass(std)))
                    #print ' Enum %s represents %s' % (ei.tag(), ei.unicodeValue())
            #print '%s unique: %s' % (std.expandedName(), nsm.uniqueInClass(std))

def _PrepareComplexTypeDefinition (ctd, nsm, module_context):
    #print '%s represents %s in %s' % (ctd.nameInBinding(), ctd.expandedName(), nsm.namespace())
    content_basis = None
    content_type_tag = ctd._contentTypeTag()
    if (ctd.CT_SIMPLE == content_type_tag):
        content_basis = ctd.contentType()[1]
        #template_map['simple_base_type'] = binding_module.literal(content_basis, **kw)
    elif (ctd.CT_MIXED == content_type_tag):
        content_basis = ctd.contentType()[1]
    elif (ctd.CT_ELEMENT_ONLY == content_type_tag):
        content_basis = ctd.contentType()[1]
    kw = { 'binding_module' : module_context
         , 'binding_schema' : ctd._schema() }
    if isinstance(content_basis, xs.structures.Particle):
        plurality_map = content_basis.pluralityData().nameBasedPlurality()
    else:
        plurality_map = {}
    ctd._templateMap()['_unique'] = nsm.uniqueInClass(ctd)
    #print 'Generating locals for %s' % (ctd.expandedName(),)
    for cd in ctd.localScopedDeclarations():
        _SetNameWithAccessors(cd, ctd, plurality_map.get(cd.expandedName(), (False, None))[0], module_context, nsm, kw)
        #use_map = cd._templateMap()
        #print '  %s %s uses %s stored in %s' % (cd.__class__.__name__, cd.expandedName(), use_map['id'], use_map['key'])


def _SetNameWithAccessors (component, container, is_plural, binding_module, nsm, kw):
    use_map = component._templateMap()
    class_unique = nsm.uniqueInClass(container)
    assert isinstance(component, xs.structures._ScopedDeclaration_mixin)
    unique_name = utility.PrepareIdentifier(component.expandedName().localName(), class_unique)
    use_map['id'] = unique_name
    use_map['inspector'] = unique_name
    use_map['mutator'] = utility.PrepareIdentifier('set' + unique_name[0].upper() + unique_name[1:], class_unique)
    use_map['use'] = utility.MakeUnique('__' + unique_name.strip('_'), class_unique)
    assert component._scope() == container
    assert component.nameInBinding() is None, 'Use %s but binding name %s for %s' % (use_map['use'], component.nameInBinding(), component.expandedName())
    component.setNameInBinding(use_map['use'])
    key_name = '%s_%s_%s' % (str(nsm.namespace()), container.nameInBinding(), component.expandedName())
    use_map['key'] = utility.PrepareIdentifier(key_name, class_unique, private=True)
    use_map['name'] = str(component.expandedName())
    use_map['name_expr'] = binding_module.literal(component.expandedName(), **kw)
    if isinstance(component, xs.structures.ElementDeclaration) and is_plural:
        use_map['appender'] = utility.PrepareIdentifier('add' + unique_name[0].upper() + unique_name[1:], class_unique)
    return use_map

class BindingIO (object):
    __prolog = None
    __postscript = None
    __templateMap = None
    __stringIO = None
    __filePath = None

    def __init__ (self, binding_module, **kw):
        super(BindingIO, self).__init__(self)
        self.__bindingModule = binding_module
        if binding_module.modulePath():
            self.__filePath = os.path.join(*binding_module.modulePath().split('.'))
        if self.__filePath:
            self.__filePath += '.py'
        self.__prolog = []
        self.__postscript = []
        self.__templateMap = kw.copy()
        self.__templateMap.update({ 'date' : str(datetime.datetime.now()),
                                    'filePath' : self.__filePath,
                                    'binding_module' : binding_module,
                                    'pyxbVersion' : pyxb.__version__ })
        self.__stringIO = StringIO.StringIO()

    def expand (self, template, **kw):
        tm = self.__templateMap.copy()
        tm.update(kw)
        return templates.replaceInText(template, **tm)

    def write (self, template, **kw):
        txt = self.expand(template, **kw)
        self.__stringIO.write(txt)

    def bindingModule (self):
        return self.__bindingModule
    __bindingModule = None

    def prolog (self):
        return self.__prolog
    def postscript (self):
        return self.__postscript

    def literal (self, *args, **kw):
        kw.update(self.__templateMap)
        return pythonLiteral(*args, **kw)

    def contents (self):
        rv = self.__prolog
        rv.append(self.__stringIO.getvalue())
        rv.extend(self.__postscript)
        return ''.join(rv)

class _ModuleNaming_mixin (object):
    __anonSTDIndex = None
    __anonCTDIndex = None
    __uniqueInModule = None
    __uniqueInClass = None

    __ComponentBindingModuleMap = {}

    def __init__ (self, *args, **kw):
        super(_ModuleNaming_mixin, self).__init__(*args, **kw)
        self.__anonSTDIndex = 1
        self.__anonCTDIndex = 1
        self.__components = []
        self.__componentNameMap = {}
        self.__uniqueInModule = set()
        self.__bindingIO = None
        self.__importedModules = []
        self.__namespaceDeclarations = []
        self.__referencedNamespaces = {}
        self.__uniqueInClass = {}

    def _importModule (self, module):
        assert isinstance(module, _ModuleNaming_mixin)
        if isinstance(module, NamespaceModule) and (pyxb.namespace.XMLSchema == module.namespace()):
            return
        if not (module in self.__importedModules):
            self.__importedModules.append(module)

    def uniqueInClass (self, component):
        rv = self.__uniqueInClass.get(component)
        if rv is None:
            rv = set()
            if isinstance(component, xs.structures.SimpleTypeDefinition):
                rv.update(basis.simpleTypeDefinition._ReservedSymbols)
            else:
                assert isinstance(component, xs.structures.ComplexTypeDefinition)
                if component._isHierarchyRoot():
                    rv.update(basis.complexTypeDefinition._ReservedSymbols)
                else:
                    base_td = component.baseTypeDefinition()
                    base_unique = base_td._templateMap().get('_unique')
                    assert base_unique is not None, 'Base %s of %s has no unique' % (base_td.expandedName(), component.expandedName())
                    rv.update(base_unique)
            self.__uniqueInClass[component] = rv
        return rv

    __referencedNamespaces = None

    def bindingIO (self):
        return self.__bindingIO

    def moduleContents (self):
        template_map = {}
        aux_imports = []
        for ns in self.__importedModules:
            aux_imports.append('import %s' % (ns.modulePath(),))
        template_map['aux_imports'] = "\n".join(aux_imports)
        template_map['namespace_decls'] = "\n".join(self.__namespaceDeclarations)
        self._finalizeModuleContents_vx(template_map)
        return self.__bindingIO.contents()

    def modulePath (self):
        return self.__modulePath
    def _setModulePath (self, module_path):
        if module_path is not None:
            self.__modulePath = module_path
        kw = self._initialBindingTemplateMap()
        self.__bindingIO = BindingIO(self, **kw)
    __modulePath = None

    def _initializeUniqueInModule (self, unique_in_module):
        self.__uniqueInModule = set(unique_in_module)

    def uniqueInModule (self):
        return self.__uniqueInModule

    @classmethod
    def BindComponentInModule (cls, component, module):
        cls.__ComponentBindingModuleMap[component] = module
        return module

    @classmethod
    def ComponentBindingModule (cls, component):
        rv = cls.__ComponentBindingModuleMap.get(component)
        return cls.__ComponentBindingModuleMap.get(component)

    @classmethod
    def _RecordNamespace (cls, module):
        cls.__NamespaceModuleMap[module.namespace()] = module
        return module
    @classmethod
    def ForNamespace (cls, namespace):
        return cls.__NamespaceModuleMap.get(namespace)
    __NamespaceModuleMap = { }

    __SchemaModuleMap = { }
    @classmethod
    def _RecordSchemaGroup (cls, module):
        cls.__SchemaModuleMap.update(dict.fromkeys(module.schemaGroup(), module))
        return module
    @classmethod
    def ForSchema (cls, schema, fallback_to_namespace=False):
        rv = cls.__SchemaModuleMap.get(schema, None)
        if (rv is None) and fallback_to_namespace:
            rv = cls.ForNamespace(schema.targetNamespace())
        return rv

    def _bindComponent (self, component):
        kw = {}
        rv = component.bestNCName()
        if rv is None:
            if isinstance(component, xs.structures.ComplexTypeDefinition):
                rv = '_CTD_ANON_%d' % (self.__anonCTDIndex,)
                self.__anonCTDIndex += 1
            elif isinstance(component, xs.structures.SimpleTypeDefinition):
                rv = '_STD_ANON_%d' % (self.__anonSTDIndex,)
                self.__anonSTDIndex += 1
            else:
                assert False
            kw['protected'] = True
        rv = utility.PrepareIdentifier(rv, self.__uniqueInModule, kw)
        assert not component in self.__componentNameMap
        self.__components.append(component)
        self.__componentNameMap[component] = rv
        return rv
    def nameInModule (self, component):
        return self.__componentNameMap.get(component)

    def __componentModule (self, component, module_type):
        assert module_type is None
        if NamespaceGroupModule == module_type:
            pass
        elif NamespaceModule == module_type:
            pass
        else:
            assert module_type is None
            component_module = _ModuleNaming_mixin.ComponentBindingModule(component)
        return component_module

    def referenceSchemaComponent (self, component, module_type=None):
        component_module = self.__componentModule(component, module_type)
        if component_module is None:
            namespace = component.bindingNamespace()
            if namespace is None:
                name = self.__componentNameMap.get(component)
                assert name is not None, 'Completely at a loss to identify %s in %s' % (component.expandedName(), self)
            assert not namespace.definedBySchema()
            namespace_module = self.ForNamespace(namespace)
            assert namespace_module is not None, 'No namespace module for %s' % (namespace,)
            self._importModule(namespace_module)
            return '%s.%s' % (namespace.modulePath(), component.nameInBinding())
        name = component_module.__componentNameMap.get(component)
        if name is None:
            assert isinstance(self, NamespaceModule) and (self.namespace() == component.bindingNamespace())
            name = component.nameInBinding()
        if self != component_module:
            self._importModule(component_module)
            name = '%s.%s' % (component_module.modulePath(), name)
        return name

    def _referencedNamespaces (self): return self.__referencedNamespaces

    def defineNamespace (self, namespace, name, require_unique=True, **kw):
        rv = self.__referencedNamespaces.get(namespace)
        print '%s define %s current %s has %s' % (self, namespace, self.__referencedNamespaces, rv)
        if rv is not None:
            print 'WARNING: Module already have reference to %s' % (namespace,)
            return rv
        if require_unique:
            name = utility.PrepareIdentifier(name, self.__uniqueInModule, **kw)
        if namespace.isAbsentNamespace():
            defn = 'pyxb.namespace.CreateAbsentNamespace()'
        else:
            defn = 'pyxb.namespace.NamespaceForURI(%s, create_if_missing=True)' % (repr(namespace.uri()),)
        self.__namespaceDeclarations.append('%s = %s' % (name, defn))
        self.__namespaceDeclarations.append("%s.configureCategories(['typeBinding', 'elementBinding'])" % (name,))
        self.__referencedNamespaces[namespace] = name
        return name

    def referenceNamespace (self, namespace, module_type=None):
        assert module_type is None
        rv = self.__referencedNamespaces.get(namespace)
        if rv is None:
            namespace_module = self.ForNamespace(namespace)
            if pyxb.namespace.XMLSchema == namespace:
                rv = 'pyxb.namespace.XMLSchema'
            elif isinstance(self, NamespaceModule):
                if (self.namespace() == namespace):
                    rv = 'Namespace'
                elif namespace_module is not None:
                    self._importModule(namespace_module)
                    rv = '%s.Namespace' % (namespace_module.modulePath(),)
                else:
                    assert False
                    #rv = 'pyxb.namespace.NamespaceForURI(%s)' % (repr(namespace.uri()),)
            else:
                for im in self.__importedModules:
                    if isinstance(im, NamespaceModule) and (im.namespace() == namespace):
                        rv = '%s.Namespace' % (im.modulePath(),)
                        break
                    if isinstance(im, SchemaGroupModule):
                        rv = im.__referencedNamespaces.get(namespace)
                        if rv is not None:
                            break
                if rv is None:
                    if namespace.prefix():
                        nsn = 'Namespace_%s' % (namespace.prefix(),)
                    else:
                        nsn = 'Namespace'
                    rv =  self.defineNamespace(namespace, nsn, protected=True)
            self.__referencedNamespaces[namespace] = rv
        return rv

    def literal (self, *args, **kw):
        return self.__bindingIO.literal(*args, **kw)

    def addImportsFrom (self, module):
        print 'Importing to %s from %s' % (self, module)
        self._importModule(module)
        for c in self.__components:
            local_name = self.nameInModule(c)
            assert local_name is not None
            rem_name = module.nameInModule(c)
            if rem_name is None:
                continue
            aux = ''
            if local_name != rem_name:
                aux = ' as %s' % (local_name,)
            self.__bindingIO.write("from %s import %s%s\n" % (module.modulePath(), rem_name, aux))

class NamespaceModule (_ModuleNaming_mixin):
    """This class represents a Python module that holds all the
    declarations belonging to a specific namespace."""

    def namespace (self):
        return self.__namespace
    __namespace = None

    __modulePrefixElts = None

    def namespaceGroupModule (self):
        return self.__namespaceGroupModule
    def setNamespaceGroupModule (self, namespace_group_module):
        self.__namespaceGroupModule = namespace_group_module
    __namespaceGroupModule = None

    _UniqueInModule = set([ 'pyxb', 'sys', 'Namespace', 'CreateFromDOM' ])

    def namespaceGroupHead (self):
        return self.__namespaceGroupHead
    __namespaceGroupHead = None
    __namespaceGroup = None

    def componentsInNamespace (self):
        return self.__components
    __components = None

    @classmethod
    def ForComponent (cls, component):
        return cls.__ComponentModuleMap.get(component)
    __ComponentModuleMap = { }

    def namespaceGroupMulti (self):
        return 1 < len(self.__namespaceGroup)

    def __init__ (self, namespace, ns_scc, module_prefix_elts=[], components=None):
        super(NamespaceModule, self).__init__(self)
        self._initializeUniqueInModule(self._UniqueInModule)
        self.__namespace = namespace
        self.defineNamespace(namespace, 'Namespace', require_unique=False)
        print 'NSM Namespace %s module path %s' % (namespace, namespace.modulePath())
        mp = self.__namespace.modulePath()
        if mp is not None:
            print 'Setting namespace module path to %s' % (mp,)
            self._setModulePath(mp)
        self.__namespaceGroup = ns_scc
        self._RecordNamespace(self)
        self.__namespaceGroupHead = self.ForNamespace(ns_scc[0])
        self.__modulePrefixElts = module_prefix_elts[:]
        self.__components = components
        # wow! fromkeys actually IS useful!
        if self.__components is not None:
            self.__ComponentModuleMap.update(dict.fromkeys(self.__components, self))
        self.__namespaceBindingNames = {}
        self.__componentBindingName = {}

    def _initialBindingTemplateMap (self):
        kw = { 'moduleType' : 'namespace'
             , 'targetNamespace' : repr(self.__namespace.uri())
             , 'namespaceURI' : self.__namespace.uri()
             , 'namespaceReference' : self.referenceNamespace(self.__namespace)
             }
        return kw

    def setBaseModule (self, base_module):
        if base_module is not None:
            base_module = '.'.join(self.__modulePrefixElts + [ base_module ])
        self._setModulePath(base_module)
        self.__namespace.setModulePath(self.modulePath())

    def setSchemaGroupPrefixElts (self, schema_group_prefix_elts):
        self.__schemaGroupPrefixElts = schema_group_prefix_elts[:]
        self.__uniqueInSchemaGroup = set()
    __schemaGroupPrefixElts = None
    __uniqueInSchemaGroup = None
    
    def schemaGroupModulePath (self, schema_group_module):
        if schema_group_module.schemaGroupMulti():
            module_base = utility.MakeUnique('multischema', self.__uniqueInSchemaGroup)
        else:
            module_base = utility.MakeUnique(schema_group_module.schemaGroupHead().schemaLocationTag(), self.__uniqueInSchemaGroup)
        return '.'.join(self.__schemaGroupPrefixElts + [ module_base ])

    def _finalizeModuleContents_vx (self, template_map):
        self.bindingIO().prolog().append(self.bindingIO().expand('''# %{filePath}
# PyXB bindings for NamespaceModule
# Generated %{date} by PyXB version %{pyxbVersion}
import pyxb.binding
import pyxb.exceptions_
import pyxb.utils.domutils
import sys

%{namespace_decls}
Namespace._setModule(sys.modules[__name__])

def CreateFromDocument (xml_text):
    """Parse the given XML and use the document element to create a Python instance."""
    dom = pyxb.utils.domutils.StringToDOM(xml_text)
    return CreateFromDOM(dom.documentElement)

def CreateFromDOM (node):
    """Create a Python instance from the given DOM node.
    The node tag must correspond to an element declaration in this module."""
    return pyxb.binding.basis.element.AnyCreateFromDOM(node, Namespace)

# Import bindings for namespaces imported into schema
%{aux_imports}

''', **template_map))

    __components = None
    __componentBindingName = None

    def bindComponent (self, component, schema_group_module):
        ns_name = self._bindComponent(component)
        component.setNameInBinding(ns_name)
        binding_module = self
        if schema_group_module is not None:
            schema_group_module._bindComponent(component)
            binding_module = schema_group_module
        if self.__namespaceGroupModule:
            self.__namespaceGroupModule._bindComponent(component)
        return _ModuleNaming_mixin.BindComponentInModule(component, binding_module)

    def __str__ (self):
        return 'NM:%s@%s' % (self.namespace(), self.modulePath())

class NamespaceGroupModule (_ModuleNaming_mixin):
    """This class represents a Python module that holds all the
    declarations belonging to a set of namespaces which have
    interdependencies."""

    def namespaceModules (self):
        return self.__namespaceModules
    __namespaceModules = None

    __components = None
    __componentBindingName = None
    __uniqueInModule = None

    _UniqueInModule = set()
    __UniqueInGroups = set()
    _GroupPrefix = '_group'

    def __init__ (self, namespace_modules, module_prefix_elts):
        super(NamespaceGroupModule, self).__init__(self)
        assert 1 < len(namespace_modules)
        self.__namespaceModules = namespace_modules

        print namespace_modules[0].namespace()
        self.__namespaceGroupHead = namespace_modules[0].namespaceGroupHead()

        module_prefix_elts = module_prefix_elts[:]
        module_prefix_elts.append(self._GroupPrefix)
        self._setModulePath('.'.join(module_prefix_elts + [ utility.MakeUnique('nsgroup', self.__UniqueInGroups) ]))
        for nsm in namespace_modules:
            nsm.setSchemaGroupPrefixElts(module_prefix_elts + [ utility.MakeUnique('_%s' % (nsm.namespace().prefix(),), self.__UniqueInGroups) ])
        self._initializeUniqueInModule(self._UniqueInModule)

    def _initialBindingTemplateMap (self):
        kw = { 'moduleType' : 'namespaceGroup'
             , 'namespaceHeadURI' : self.__namespaceGroupHead.namespace().uri() }
        return kw

    def _finalizeModuleContents_vx (self, template_map):
        text = []
        for nsm in self.namespaceModules():
            text.append('#  %s %s' % (nsm.namespace(), nsm.namespace().prefix()))
        template_map['namespace_comment'] = "\n".join(text)
        self.bindingIO().prolog().append(self.bindingIO().expand('''# %{filePath}
# PyXB bindings for NamespaceGroupModule
# Incorporated namespaces:
%{namespace_comment}

import pyxb
import pyxb.binding

%{namespace_decls}

# Import bindings for schemas in group
%{aux_imports}
''', **template_map))

    def __str__ (self):
        return 'NGM:%s' % (self.modulePath(),)

class SchemaGroupModule (_ModuleNaming_mixin):
    """This class represents a Python module that holds all bindings
    associated with components defined in a set of schema.

    Normally an instance represents a single schema, but when there is
    a cycle in the schema dependency graph all components in the cycle
    are aggregated into a single module."""

    __bindingOutput = None

    def namespaceModule (self):
        return self.__namespaceModule
    __namespaceModule = None

    def schemaGroup (self):
        return self.__schemaGroup
    __schemaGroup = None

    def schemaGroupHead (self):
        return self.__schemaGroupHead
    __schemaGroupHead = None
    def schemaGroupMulti (self):
        return (1 < len(self.__schemaGroup))

    _UniqueInModule = set([ 'pyxb', 'sys', 'Namespace' ])
    
    def __init__ (self, namespace_module, schema_group):
        super(SchemaGroupModule, self).__init__(self)
        self.__namespaceModule = namespace_module
        self.defineNamespace(namespace_module.namespace(), 'Namespace', require_unique=False)
        self.__schemaGroup = schema_group
        self.__schemaGroupHead = schema_group[0]
        self._RecordSchemaGroup(self)
        assert isinstance(self.__schemaGroup, list)
        self._setModulePath(self.__namespaceModule.schemaGroupModulePath(self))
        self._initializeUniqueInModule(self._UniqueInModule)

    def setImports (self, schema_graph):
        for sc in self.__schemaGroup:
            for isc in schema_graph.edgeMap().get(sc, set()):
                self._importModule(_ModuleNaming_mixin.ForSchema(isc, True))

    def _initialBindingTemplateMap (self):
        kw = { 'moduleType' : 'namespaceGroup'
             , 'schemaLocation' : self.__schemaGroupHead.schemaLocation()
             , 'schemaGroupMulti' : repr(self.schemaGroupMulti())
             }
        return kw

    def _finalizeModuleContents_vx (self, template_map):
        slocs = []
        for sc in self.schemaGroup():
            slocs.append('#  %s' % (sc.schemaLocation(),))
        template_map['schema_locs'] = "\n".join(slocs)
        self.bindingIO().prolog().append(self.bindingIO().expand('''# %{filePath}
# PyXB bindings for SchemaGroupModule
# Incorporated schemas:
%{schema_locs}

import pyxb
import pyxb.binding

%{namespace_decls}

# Import bindings from schema
%{aux_imports}
''', **template_map))

    def __str__ (self):
        return 'SGM:%s' % (self.modulePath(),)

def SchemaLocations (sc_set):
    rvs = []
    for sc in sc_set:
        if sc.schemaLocation() is not None:
            rvs.append(sc.schemaLocation())
        else:
            rvs.append("no location for %s" % (sc.targetNamespace(),))
    return "\n  ".join(rvs)

def GeneratePython (schema_location=None,
                    namespace=None,
                    module_prefix_elts=[]):

    modules = GenerateAllPython(schema_location, namespace, module_prefix_elts)


    assert 1 == len(modules), '%s produced %d modules: %s' % (namespace, len(modules), " ".join([ str(_m) for _m in modules]))
    return modules.pop().moduleContents()

def GenerateAllPython (schema_location=None,
                       namespace=None,
                       module_prefix_elts=[],
                       _process_builtins=False):
    modules = set()
    
    binding_module_prefix_elts = module_prefix_elts[:]

    pyxb.namespace.XMLSchema.setModulePath('pyxb.binding.datatypes')

    if namespace is None:
        if schema_location is None:
            raise Exception('No input provided')
        schema = xs.schema.CreateFromLocation(schema_location)
        namespace = schema.targetNamespace()

    nsdep = pyxb.namespace.NamespaceDependencies(namespace)
    siblings = nsdep.siblingNamespaces()
    print 'Configuring siblings'
    missing = nsdep.schemaDefinedNamespaces().difference(siblings)
    if 0 < len(missing):
        #raise pyxb.BindingGenerationError('Generation root %s depends on schema-defined %s' % (namespace, " ".join([ str(_ns) for _ns in missing ])))
        siblings.update(missing)
        nsdep.setSiblingNamespaces(siblings)

    for ns_set in nsdep.namespaceOrder():
        pyxb.namespace.ResolveSiblingNamespaces(ns_set)

    file('namespace.dot', 'w').write(nsdep.namespaceGraph()._generateDOT('Namespace'))
    file('schema.dot', 'w').write(nsdep.schemaGraph()._generateDOT('Schema', labeller=lambda _s: "/".join(_s.schemaLocation().split('/')[-2:])))
    file('component.dot', 'w').write(nsdep.componentGraph()._generateDOT('Component', lambda _c: _c.bestNCName()))

    assert nsdep.siblingNamespaces() == siblings

    #siblings = nsdep.schemaDefinedNamespaces()

    all_components = set()
    namespace_component_map = {}
    for sns in siblings:
        if (pyxb.namespace.XMLSchema == sns) and (not _process_builtins):
            continue
        for c in sns.components():
            if (isinstance(c, xs.structures.ElementDeclaration) and c._scopeIsGlobal()) or c.isTypeDefinition():
                assert c._schema() is not None, '%s has no schema' % (c._schema(),)
                assert c._schema().targetNamespace() == sns
                c._setBindingNamespace(sns)
                all_components.add(c)
                namespace_component_map.setdefault(sns, set()).add(c)
    
    usable_namespaces = set(namespace_component_map.keys())
    usable_namespaces.update([ _ns for _ns in nsdep.dependentNamespaces() if _ns.isLoadable])

    module_graph = pyxb.utils.utility.Graph()

    namespace_module_map = {}
    unique_in_bindings = set([NamespaceGroupModule._GroupPrefix])
    for ns_scc in nsdep.namespaceOrder():
        namespace_modules = []
        nsg_head = None
        for ns in ns_scc:
            if ns in siblings:
                nsm = NamespaceModule(ns, ns_scc, binding_module_prefix_elts, namespace_component_map.get(ns, ns.components()))
                modules.add(nsm)
            else:
                nsm = NamespaceModule(ns, ns_scc)
            module_graph.addNode(nsm)
            namespace_module_map[ns] = nsm
            assert ns == nsm.namespace()

            if nsg_head is None:
                nsg_head = nsm.namespaceGroupHead()

            if nsm.namespace().prefix() is not None:
                assert nsm.namespace().prefix() is not None, 'No prefix for %s' % (ns,)
                nsm.setBaseModule(utility.MakeUnique(nsm.namespace().prefix(), unique_in_bindings))
            else:
                nsm.setBaseModule(None)
            namespace_modules.append(nsm)

        if (nsg_head is not None) and nsg_head.namespaceGroupMulti():
            ngm = NamespaceGroupModule(namespace_modules, binding_module_prefix_elts)
            modules.add(ngm)
            module_graph.addNode(ngm)
            for nsm in namespace_modules:
                module_graph.addEdge(ngm, nsm)
                nsm.setNamespaceGroupModule(ngm)
            assert namespace_module_map[nsg_head.namespace()].namespaceGroupModule() == ngm

    schema_module_map = {}
    for sc_scc in nsdep.schemaOrder():
        scg_head = sc_scc[0]
        nsm = NamespaceModule.ForNamespace(scg_head.targetNamespace())
        sgm = None
        if 1 < len(sc_scc):
            print 'MULTI_ELT SCHEMA GROUP: %s' % ("\n  ".join([_sc.schemaLocation() for _sc in sc_scc]),)

        if (nsm is not None) and (nsm.namespaceGroupModule() is not None):
            sgm = SchemaGroupModule(nsm, sc_scc)
            modules.add(sgm)
            module_graph.addEdge(sgm, nsm)
        for sc in sc_scc:
            schema_module_map[sc] = sgm

    for m in modules:
        if isinstance(m, SchemaGroupModule):
            m.setImports(nsdep.schemaGraph())
        elif isinstance(m, NamespaceModule):
            #m.setImports(nsdep)
            pass

    file('modules.dot', 'w').write(module_graph._generateDOT('Modules'))

    component_csets = nsdep.componentOrder()
    bad_order = False
    component_order = []
    for cset in component_csets:
        if 1 < len(cset):
            print "COMPONENT DEPENDENCY LOOP of %d components" % (len(cset),)
            cg = pyxb.utils.utility.Graph(cset[0])
            for c in cset:
                print '  %s' % (c.expandedName(),)
                cg.addNode(c)
                for cd in c.bindingRequires(reset=True, include_lax=False):
                    #print '%s depends on %s' % (c, cd)
                    cg.addEdge(c, cd)
            file('deploop.dot', 'w').write(cg._generateDOT('CompDep', lambda _c: _c.bestNCName()))
            relaxed_order = cg.sccOrder()
            for rcs in relaxed_order:
                assert 1 == len(rcs)
                rcs = rcs[0]
                if rcs in cset:
                    component_order.append(rcs)
        else:
            component_order.append(cset[0])

    element_declarations = []
    type_definitions = []
    for c in component_order:
        if isinstance(c, xs.structures.ElementDeclaration) and c._scopeIsGlobal():
            nsm = namespace_module_map[c.bindingNamespace()]
            nsm.bindComponent(c, SchemaGroupModule.ForSchema(c._schema()))
            element_declarations.append(c)
        else:
            type_definitions.append(c)

    simple_type_definitions = []
    complex_type_definitions = []
    for td in type_definitions:
        nsm = namespace_module_map.get(td.bindingNamespace())
        assert nsm is not None, 'No namespace module for %s type %s scope %s namespace %s' % (td.expandedName(), type(td), td._scope(), td.bindingNamespace)
        module_context = nsm.bindComponent(td, _ModuleNaming_mixin.ForSchema(td._schema()))
        assert isinstance(module_context, _ModuleNaming_mixin), 'Unexpected type %s' % (type(module_context),)
        if isinstance(td, xs.structures.SimpleTypeDefinition):
            _PrepareSimpleTypeDefinition(td, nsm, module_context)
            simple_type_definitions.append(td)
        elif isinstance(td, xs.structures.ComplexTypeDefinition):
            _PrepareComplexTypeDefinition(td, nsm, module_context)
            complex_type_definitions.append(td)
        else:
            assert False, 'Unexpected component type %s' % (type(td),)


    for m in modules:
        if isinstance(m, NamespaceModule):
            ngm = m.namespaceGroupModule()
            if ngm is not None:
                m.addImportsFrom(ngm)
        elif isinstance(m, SchemaGroupModule):
            m.namespaceModule().namespaceGroupModule().addImportsFrom(m)

    for std in simple_type_definitions:
        GenerateSTD(std)
    for ctd in complex_type_definitions:
        GenerateCTD(ctd)
    for ed in element_declarations:
        GenerateED(ed)

    return modules

def _GenerateFacets ():
    return '''
    generator_kw['class_unique'] = set()
    generator_kw['class_keywords'] = set()
    stds = [ ]
    num_unresolved = 0
    for td in namespace.typeDefinitions().values():
        if isinstance(td, xs.structures.SimpleTypeDefinition):
            td._resolve()
            stds.append(td)
            if not td.isResolved():
                num_unresolved += 1
    while 0 < num_unresolved:
        num_unresolved = 0
        for td in stds:
            if not td.isResolved():
                td._resolve()
            if (not td.isResolved()) and td.isBuiltin():
                #print 'No resolution for %s' % (td,)
                num_unresolved += 1
    for td in stds:
        if td.isBuiltin():
            assert td.isResolved()
            GenerateFacets(outf, td, **generator_kw)
    return outf.getvalue()
'''
