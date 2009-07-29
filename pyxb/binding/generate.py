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
import errno

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
import StringIO

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

def GenerateFacets (td, generator, **kw):
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

def GenerateSTD (std, generator):

    binding_module = generator.moduleForComponent(std)
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
        template = '''
# The ur SimpleTypeDefinition
class %{std} (%{superclasses}):
    """%{description}"""

    _ExpandedName = %{expanded_name}
'''
        template_map['description'] = ''
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
        if std.isBuiltin():
            GenerateFacets(std, generator, **kw)
    else:
        GenerateFacets(std, generator, **kw)

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

def GenerateCTD (ctd, generator, **kw):
    binding_module = generator.moduleForComponent(ctd)
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
        plurality_data = content_basis.pluralityData().combinedPlurality()

        outf.postscript().append("\n\n")
        for (ed, is_plural) in plurality_data.items():
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
    # Element %{id} (%{name}) inherited from %{decl_type_en}''', decl_type_en=str(ed.scope().expandedName()), **ef_map))
                continue

            definitions.append(templates.replaceInText('''
    # Element %{name} uses Python identifier %{id}
    %{use} = pyxb.binding.content.ElementUse(%{name_expr}, '%{id}', '%{key}', %{is_plural}%{aux_init})
''', **ef_map))

            if basis.BINDING_STYLE_ACCESSOR == generator.bindingStyle():
                definitions.append(templates.replaceInText('''
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
            elif basis.BINDING_STYLE_PROPERTY == generator.bindingStyle():
                definitions.append(templates.replaceInText('''
    %{inspector} = property(%{use}.value, %{use}.set)
''', **ef_map))
            else:
                raise pyxb.LogicError('Unexpected binding style %s' % (generator.bindingStyle(),))
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
            if au.restrictionOf() is not None:
                #print 'Local %s restriction of %s' % (au_map, au.restrictionOf().attributeDeclaration()._templateMap())
                au_map = au.restrictionOf().attributeDeclaration()._templateMap().copy()
                definitions.append(templates.replaceInText('''
    # Attribute %{id} is restricted from parent''', **au_map))

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
        if ad.scope() != ctd:
            definitions.append(templates.replaceInText('''
    # Attribute %{id} inherited from %{decl_type_en}''', decl_type_en=str(ad.scope().expandedName()), **au_map))
            continue

        attribute_uses.append(templates.replaceInText('%{use}.name() : %{use}', **au_map))
        definitions.append(templates.replaceInText('''
    # Attribute %{name} uses Python identifier %{id}
    %{use} = pyxb.binding.content.AttributeUse(%{name_expr}, '%{id}', '%{key}', %{attr_type}%{aux_init})''', **au_map))
        if au.prohibited():
            if basis.BINDING_STYLE_ACCESSOR == generator.bindingStyle():
                definitions.append(templates.replaceInText('''
    # Attribute %{id} marked prohibited in this type
    def %{inspector} (self):
        raise pyxb.ProhibitedAttributeError("Attribute %{name} is prohibited in %{ctd}")
    def %{mutator} (self, new_value):
        raise pyxb.ProhibitedAttributeError("Attribute %{name} is prohibited in %{ctd}")
''', ctd=template_map['ctd'], **au_map))
            elif basis.BINDING_STYLE_PROPERTY == generator.bindingStyle():
                definitions.append(templates.replaceInText('''
    %{inspector} = property()
''', ctd=template_map['ctd'], **au_map))

            else:
                raise pyxb.LogicError('Unexpected binding style %s' % (generator.bindingStyle(),))
        else:
            if basis.BINDING_STYLE_ACCESSOR == generator.bindingStyle():
                definitions.append(templates.replaceInText('''
    def %{inspector} (self):
        """Get the attribute value for %{name}."""
        return self.%{use}.value(self)
    def %{mutator} (self, new_value):
        """Set the attribute value for %{name}.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.%{use}.set(self, new_value)''', **au_map))
            elif basis.BINDING_STYLE_PROPERTY == generator.bindingStyle():
                definitions.append(templates.replaceInText('''
    %{inspector} = property(%{use}.value, %{use}.set)
''', ctd=template_map['ctd'], **au_map))
            else:
                raise pyxb.LogicError('Unexpected binding style %s' % (generator.bindingStyle(),))

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

def GenerateED (ed, generator, **kw):
    # Unscoped declarations should never be referenced in the binding.
    assert ed._scopeIsGlobal()

    binding_module = generator.moduleForComponent(ed)
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

def _PrepareSimpleTypeDefinition (std, generator, nsm, module_context):
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

def _PrepareComplexTypeDefinition (ctd, generator, nsm, module_context):
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
    kw = { 'binding_module' : module_context }
    if isinstance(content_basis, xs.structures.Particle):
        plurality_map = content_basis.pluralityData().combinedPlurality()
    else:
        plurality_map = {}
    ctd._templateMap()['_unique'] = nsm.uniqueInClass(ctd)
    for cd in ctd.localScopedDeclarations():
        _SetNameWithAccessors(cd, ctd, plurality_map.get(cd, False), module_context, nsm, kw)

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
    __bindingFilePath = None
    __bindingFile = None

    def __init__ (self, binding_module, **kw):
        super(BindingIO, self).__init__()
        self.__bindingModule = binding_module
        self.__bindingFilePath = kw['binding_file_path']
        self.__bindingFile = kw['binding_file']
        self.__prolog = []
        self.__postscript = []
        self.__templateMap = kw.copy()
        self.__templateMap.update({ 'date' : str(datetime.datetime.now()),
                                    'filePath' : self.__bindingFilePath,
                                    'binding_module' : binding_module,
                                    'pyxbVersion' : pyxb.__version__ })
        self.__stringIO = StringIO.StringIO()

    def bindingFile (self):
        return self.__bindingFile

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

    # @todo: provide a way to reset this, for multiple generations in a single run
    _UniqueInModule = set([ 'pyxb', 'sys' ])
    
    __ComponentBindingModuleMap = {}

    def generator (self):
        return self.__generator
    __generator = None

    def __init__ (self, generator, *args, **kw):
        super(_ModuleNaming_mixin, self).__init__(*args, **kw)
        self.__generator = generator
        assert isinstance(self.__generator, Generator)
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
        assert isinstance(module, (_ModuleNaming_mixin, pyxb.namespace.Namespace))
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

    __moduleUID = None
    def moduleUID (self):
        if self.__moduleUID is None:
            self.__moduleUID = pyxb.utils.utility.HashForText(self._moduleUID_vx())
        return self.__moduleUID

    def _moduleUID_vx (self):
        return str(id(self))

    def moduleContents (self):
        template_map = {}
        aux_imports = []
        for ns in self.__importedModules:
            module_path = ns.modulePath()
            if module_path is None:
                if isinstance(ns, NamespaceModule):
                    ns = ns.namespace()
                if isinstance(ns, pyxb.namespace.Namespace):
                    ns.validateComponentModel()
                    module_path = ns.modulePath()
            assert module_path is not None, ns
            aux_imports.append('import %s' % (module_path,))
        template_map['aux_imports'] = "\n".join(aux_imports)
        template_map['namespace_decls'] = "\n".join(self.__namespaceDeclarations)
        template_map['module_uid'] = self.moduleUID()
        template_map['generation_uid_expr'] = repr(self.generator().generationUID())
        self._finalizeModuleContents_vx(template_map)
        return self.__bindingIO.contents()

    def modulePath (self):
        return self.__modulePath
    def _setModulePath (self, path_data):
        (binding_file_path, binding_file, module_path) = path_data
        self.__bindingFilePath = binding_file_path
        self.__bindingFile = binding_file
        if module_path is None:
            module_path = self.namespace().modulePath()
        if module_path is not None:
            self.__modulePath = module_path
        kw = self._initialBindingTemplateMap()
        self.__bindingIO = BindingIO(self, binding_file=binding_file, binding_file_path=binding_file_path, **kw)
    __modulePath = None

    def bindingFile (self):
        return self.__bindingFile
    __bindingFile = None
    __bindingFilePath = None

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
            if namespace_module is not None:
                self._importModule(namespace_module)
                module_path = namespace.modulePath()
            else:
                assert namespace.isBuiltinNamespace(), 'No module for non-builtin %s' % (namespace,)
                self._importModule(namespace)
                module_path = namespace.builtinModulePath()
            return '%s.%s' % (module_path, component.nameInBinding())
        name = component_module.__componentNameMap.get(component)
        if name is None:
            assert isinstance(self, NamespaceModule) and (self.namespace() == component.bindingNamespace())
            name = component.nameInBinding()
        if self != component_module:
            self._importModule(component_module)
            name = '%s.%s' % (component_module.modulePath(), name)
        return name

    def _referencedNamespaces (self): return self.__referencedNamespaces

    def defineNamespace (self, namespace, name, require_unique=True, definition=None, **kw):
        rv = self.__referencedNamespaces.get(namespace)
        assert rv is None, 'Module %s already has reference to %s' % (self, namespace)
        if require_unique:
            name = utility.PrepareIdentifier(name, self.__uniqueInModule, **kw)
        if definition is None:
            if namespace.isAbsentNamespace():
                definition = 'pyxb.namespace.CreateAbsentNamespace()'
            else:
                definition = 'pyxb.namespace.NamespaceForURI(%s, create_if_missing=True)' % (repr(namespace.uri()),)
        self.__namespaceDeclarations.append('%s = %s' % (name, definition))
        self.__namespaceDeclarations.append("%s.configureCategories(['typeBinding', 'elementBinding'])" % (name,))
        self.__referencedNamespaces[namespace] = name
        return name

    def referenceNamespace (self, namespace, module_type=None):
        assert module_type is None
        rv = self.__referencedNamespaces.get(namespace)
        if rv is None:
            namespace_module = self.ForNamespace(namespace)
            if namespace.isBuiltinNamespace():
                rv = namespace.builtinNamespaceRepresentation()
            elif namespace.isUndeclaredNamespace():
                rv = namespace.modulePath()
            elif isinstance(self, NamespaceModule):
                if (self.namespace() == namespace):
                    rv = 'Namespace'
                elif namespace_module is not None:
                    self._importModule(namespace_module)
                    rv = '%s.Namespace' % (namespace_module.modulePath(),)
                else:
                    assert False, 'Unexpected reference to %s' % (namespace,)
                    #rv = 'pyxb.namespace.NamespaceForURI(%s)' % (repr(namespace.uri()),)
            else:
                if namespace.prefix():
                    nsn = 'Namespace_%s' % (namespace.prefix(),)
                else:
                    nsn = 'Namespace'
                for im in self.__importedModules:
                    if isinstance(im, NamespaceModule) and (im.namespace() == namespace):
                        rv = '%s.Namespace' % (im.modulePath(),)
                        break
                    if isinstance(im, NamespaceGroupModule):
                        irv = im.__referencedNamespaces.get(namespace)
                        if irv is not None:
                            rv = self.defineNamespace(namespace, nsn, '%s.%s' % (im.modulePath(), irv), protected=True)
                            break
                if rv is None:
                    rv =  self.defineNamespace(namespace, nsn, protected=True)
                    assert 0 < len(self.__namespaceDeclarations)
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
            self.__bindingIO.write("from %s import %s%s # %s\n" % (module.modulePath(), rem_name, aux, c.expandedName()))

    def writeToModuleFile (self):
        if self.bindingFile():
            self.bindingFile().write(self.moduleContents())
            print 'Saved binding source to %s' % (self.__bindingFilePath,)
        else:
            print 'ERROR: No binding file for %s' % (self,)


class NamespaceModule (_ModuleNaming_mixin):
    """This class represents a Python module that holds all the
    declarations belonging to a specific namespace."""

    def namespace (self):
        return self.__namespace
    __namespace = None

    def namespaceGroupModule (self):
        return self.__namespaceGroupModule
    def setNamespaceGroupModule (self, namespace_group_module):
        self.__namespaceGroupModule = namespace_group_module
    __namespaceGroupModule = None

    _UniqueInModule = _ModuleNaming_mixin._UniqueInModule.copy()
    _UniqueInModule.update([ 'Namespace', 'CreateFromDOM', 'CreateFromDocument' ])

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

    def _moduleUID_vx (self):
        if self.namespace().isAbsentNamespace():
            return 'Absent'
        return str(self.namespace())

    def namespaceGroupMulti (self):
        return 1 < len(self.__namespaceGroup)

    def __init__ (self, generator, namespace, ns_scc, components=None, **kw):
        super(NamespaceModule, self).__init__(generator, **kw)
        self._initializeUniqueInModule(self._UniqueInModule)
        self.__namespace = namespace
        self.defineNamespace(namespace, 'Namespace', require_unique=False)
        #print 'NSM Namespace %s module path %s' % (namespace, namespace.modulePath())
        self.__namespaceGroup = ns_scc
        self._RecordNamespace(self)
        self.__namespaceGroupHead = self.ForNamespace(ns_scc[0])
        self.__components = components
        # wow! fromkeys actually IS useful!
        if self.__components is not None:
            self.__ComponentModuleMap.update(dict.fromkeys(self.__components, self))
        self.__namespaceBindingNames = {}
        self.__componentBindingName = {}
        self._setModulePath(generator.modulePathData(self))

    def _initialBindingTemplateMap (self):
        kw = { 'moduleType' : 'namespace'
             , 'targetNamespace' : repr(self.__namespace.uri())
             , 'namespaceURI' : self.__namespace.uri()
             , 'namespaceReference' : self.referenceNamespace(self.__namespace)
             }
        return kw

    def _finalizeModuleContents_vx (self, template_map):
        self.bindingIO().prolog().append(self.bindingIO().expand('''# %{filePath}
# PyXB bindings for NamespaceModule
# NSM:%{module_uid}
# Generated %{date} by PyXB version %{pyxbVersion}
import pyxb
import pyxb.binding
import pyxb.utils.utility
import pyxb.utils.domutils
import sys

# Unique identifier for bindings created at the same time
_GenerationUID = %{generation_uid_expr}

# Import bindings for namespaces imported into schema
%{aux_imports}

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

''', **template_map))

    __components = None
    __componentBindingName = None

    def bindComponent (self, component):
        ns_name = self._bindComponent(component)
        component.setNameInBinding(ns_name)
        binding_module = self
        if self.__namespaceGroupModule:
            self.__namespaceGroupModule._bindComponent(component)
            binding_module = self.__namespaceGroupModule
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

    _UniqueInModule = _ModuleNaming_mixin._UniqueInModule.copy()
    
    __UniqueInGroups = set()
    
    _GroupPrefix = '_group'

    def __init__ (self, generator, namespace_modules, **kw):
        super(NamespaceGroupModule, self).__init__(generator, **kw)
        assert 1 < len(namespace_modules)
        self.__namespaceModules = namespace_modules
        self.__namespaceGroupHead = namespace_modules[0].namespaceGroupHead()
        self._initializeUniqueInModule(self._UniqueInModule)
        self._setModulePath(generator.modulePathData(self))

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
# NGM:%{module_uid}
# Incorporated namespaces:
%{namespace_comment}

import pyxb
import pyxb.binding
import pyxb.utils.utility

# Unique identifier for bindings created at the same time
_GenerationUID = %{generation_uid_expr}

# Import bindings for schemas in group
%{aux_imports}

%{namespace_decls}
''', **template_map))

    def _moduleUID_vx (self):
        nss = []
        for nsm in self.namespaceModules():
            ns = nsm.namespace()
            if ns.isAbsentNamespace():
                nss.append('Absent')
            else:
                nss.append(str(ns))
        nss.sort()
        return ';'.join(nss)

    def __str__ (self):
        return 'NGM:%s' % (self.modulePath(),)


def GeneratePython (schema_location=None,
                    schema_text=None,
                    namespace=None,
                    module_prefix_elts=[],
                    **kw):

    generator = Generator(allow_absent_module=True, generate_to_files=False, **kw)
    if schema_location is not None:
        schema_text = pyxb.utils.utility.TextFromURI(schema_location)
    generator.addSchema(pyxb.xmlschema.schema.CreateFromStream(StringIO.StringIO(schema_text)))
    modules = generator.bindingModules()

    assert 1 == len(modules), '%s produced %d modules: %s' % (namespace, len(modules), " ".join([ str(_m) for _m in modules]))
    return modules.pop().moduleContents()

import optparse
import re

class Generator (object):
    """Configuration and data for a single binding-generation action."""

    _DEFAULT_bindingRoot = '.'
    def bindingRoot (self):
        """The directory path into which generated bindings will be written.
        @rtype: C{str}"""
        return self.__bindingRoot
    def setBindingRoot (self, binding_root):
        self.__bindingRoot = binding_root
        return self
    __bindingRoot = None
    
    def moduleFilePaths (self, module_path):
        assert False
        assert module_path
        read_path_elts = module_path.split('.')
        leaf = read_path_elts.pop()
        read_path = os.path.join(self.bindingRoot(), *read_path_elts)
        write_path = read_path
        write_module = None
        if self.writeForCustomization():
            write_path_elts = read_path_elts + ['raw']
            write_module = '.'.join(write_path_elts + [leaf])
            write_path = os.path.join(self.bindingRoot(), *write_path_elts)
        leaf_name = '%s.py' % (leaf,)
        return (os.path.join(read_path, leaf_name), os.path.join(write_path, leaf_name), write_module)

    def __directoryForModulePath (self, module_elts):
        if isinstance(module_elts, basestring):
            module_elts = module_elts.split('.')
        else:
            module_elts = module_elts[:]
        assert 0 < len(module_elts)
        assert not module_elts[-1].endswith('.py')
        module_elts[-1] = '%s.py' % (module_elts[-1],)
        return os.path.join(self.bindingRoot(), *module_elts)

    def generateToFiles (self):
        return self.__generateToFiles
    __generateToFiles = None

    def modulePathData (self, module):
        # file system path to where the bindings are written
        # module path from which the bindings are normally imported
        # file object into which bindings are written
        
        module_path = None
        if isinstance(module, NamespaceModule):
            ns = module.namespace()
            ns.validateComponentModel()
            module_path = ns.modulePath()
            if (module_path is None) or ns.isLoadedNamespace() or (ns.isBuiltinNamespace() and not self.allowBuiltinGeneration()) or (not self.generateToFiles()):
                return ('/dev/null', None, None)
            #if pyxb.namespace.XMLSchema != ns:
            #    return ('/dev/null', None, None)
            #module_path="bogus.xsd"
            module_elts = module_path.split('.')
            import_file_path = self.__directoryForModulePath(module_elts)
            if self.writeForCustomization():
                module_elts.insert(-1, 'raw')
            if self.writeForCustomization() and (not os.path.exists(import_file_path)):
                raw_module_path = '.'.join(module_elts)
                file(import_file_path, 'w').write("from %s import *\n" % (raw_module_path,))
            binding_file_path = self.__directoryForModulePath(module_elts)
            try:
                binding_file = pyxb.utils.utility.OpenOrCreate(binding_file_path, tag=module.moduleUID())
            except OSError, e:
                if errno.EEXIST == e.errno:
                    raise pyxb.BindingGenerationError('Target file %s for namespace %s bindings exists with other content' % (binding_file_path, ns))
                raise
        elif isinstance(module, NamespaceGroupModule):
            if not self.generateToFiles():
                raise pyxb.BindingGenerationError('Generation of namespace groups requires generate-to-files')
            module_elts = []
            if self.modulePrefix():
                module_elts.extend(self.modulePrefix().split('.'))
            in_use = set()
            while True:
                module_elts.append(pyxb.utils.utility.PrepareIdentifier('nsgroup', in_use, protected=True))
                try:
                    binding_file_path = self.__directoryForModulePath(module_elts)
                    print 'Attempting group at %s' % (binding_file_path,)
                    binding_file = pyxb.utils.utility.OpenOrCreate(binding_file_path, tag=module.moduleUID())
                    break
                except OSError, e:
                    if errno.EEXIST != e.errno:
                        raise
                module_elts.pop()
            module_path = '.'.join(module_elts)
        else:
            assert False
        if self.generateToFiles():
            for n in range(len(module_elts)-1):
                sub_path = os.path.join(*module_elts[:1+n])
                init_path = os.path.join(sub_path, '__init__.py')
                if not os.path.exists(init_path):
                    file(init_path, 'w')
        return (binding_file_path, binding_file, module_path)

    def schemaRoot (self):
        """The directory from which entrypoint schemas specified as
        relative file paths will be read.

        The value includes the final path separator character."""
        return self.__schemaRoot
    def setSchemaRoot (self, schema_root):
        if not schema_root.endswith(os.sep):
            schema_root = schema_root + os.sep
        self.__schemaRoot = schema_root
        return self
    __schemaRoot = None

    def schemaStrippedPrefix (self):
        """Optional string that is stripped from the beginning of
        schemaLocation values before loading from them.

        This applies only to the values of schemaLocation attributes
        in C{import} and C{include} elements.  Its purpose is to
        convert absolute schema locations into relative ones to allow
        offline processing when all schema are available in a local
        directory.  See C{schemaRoot}.
        """
        return self.__schemaStrippedPrefix
    def setSchemaStrippedPrefix (self, schema_stripped_prefix):
        self.__schemaStrippedPrefix = schema_stripped_prefix
        return self
    __schemaStrippedPrefix = None

    def schemaLocationList (self):
        """A list of locations from which entrypoint schemas are to be
        read.

        See also L{addSchemaLocation} and L{schemas}.
        """
        return self.__schemaLocationList
    def setSchemaLocationList (self, schema_location_list):
        self.__schemaLocationList[:] = []
        self.__schemaLocationList.extend(schema_location_list)
        return self
    def addSchemaLocation (self, schema_location):
        """Add the location of an entrypoint schema.

        The specified location should be a URL.  If the schema
        location does not have a URL scheme (e.g., C{http:}), it is
        assumed to be a file, and if it is not an absolute path is
        located relative to the C{schemaRoot}."""
        self.__schemaLocationList.append(schema_location)
        return self
    __schemaLocationList = None

    def schemas (self):
        """L{Schema<pyxb.xmlschema.structures.Schema>} for which
        bindings should be generated.

        This is the list of entrypoint schemas for binding generation.
        Values in L{schemaLocationList} are read and converted into
        schema, then appended to this list.  Values from L{_moduleList}
        are applied starting with the first schema in this list.
        """
        return self.__schemas[:]
    def setSchemas (self, schemas):
        self.__schemas[:] = []
        self.__schemas.extend(schemas)
        return self
    def addSchema (self, schema):
        self.__schemas.append(schema)
        return self
    __schemas = None

    def namespaces (self):
        """The set of L{namespaces<pyxb.namespace.Namespace>} for
        which bindings will be generated.

        This is the set of namespaces read from entrypoint schema,
        closed under reference to namespaces defined by schema import.

        @rtype: C{set}
        """
        return self.__namespaces.copy()
    def setNamespaces (self, namespace_set):
        self.__namespaces.clear()
        self.__namespaces.update(namespace_set)
        return self
    def addNamespace (self, namespace):
        self.__namespaces.add(namespace)
        return self
    __namespaces = None

    def moduleList (self):
        """A list of module names to be applied in order to the namespaces of entrypoint schemas"""
        return self.__moduleList[:]
    def _setModuleList (self, module_list):
        self.__moduleList[:] = []
        self.__moduleList.extend(module_list)
        return self
    
    def addModuleName (self, module_name):
        """Add a module name corresponding to an entrypoint schema.

        The namespace defined by the corresponding schema will be
        written to a binding using the given module name, adjusted by
        L{modulePrefix}."""
        self.__moduleList.append(module_name)
        return self
    __moduleList = None

    def modulePrefix (self):
        """The prefix for binding modules.

        The base name for the module holding a binding is taken from
        the moduleList, moduleMap, or an XMLNS prefix associated with
        the namespace in a containing schema.  This value, if present,
        is used as a prefix to allow a deeper module hierarchy."""
        return self.__modulePrefix
    def setModulePrefix (self, module_prefix):
        self.__modulePrefix = module_prefix
        return self
    __modulePrefix = None

    def namespaceModuleMap (self):
        """A map from namespace URIs to the module to be used for the
        corresponding generated binding.

        Module values are adjusted by L{modulePrefix} if that has been
        specified.

        An entry in this map for a namespace supersedes the module
        specified in moduleList if the namespace is defined by an
        entrypoint schema.

        @return: A reference to the namespace module map.
        """
        return self.__namespaceModuleMap
    __namespaceModuleMap = None

    def archivePath (self):
        """A colon-separated list of paths from which namespace
        archives can be read.

        The default path is the contents of the C{PYXB_ARCHIVE_PATH}
        environment variable, or the standard path configured at
        installation time.
        """
        return self.__archivePath
    def setArchivePath (self, archive_path):
        self.__archivePath = archive_path
        return self
    __archivePath = None
        
    def noLoadNamespaces (self):
        """A frozenset of namespaces that many not be loaded from an archive."""
        return frozenset(self.__noLoadNamespaces)
    def _setNoLoadNamespaces (self, namespace_set):
        """Record the set of namespaces that should not be loaded from an archive.

        The expectation is that any required entities in the namespace
        will be defined by loading schema."""
        self.__noLoadNamespaces.clear()
        self.__noLoadNamespaces.update([ pyxb.namespace.NamespaceInstance(_ns) for _ns in namespace_set ])
    def addNoLoadNamespace (self, namespace):
        """Mark that the specififed namespace should not be loaded from an archive.

        Be aware that this removes any knowledge of any archive in
        which this namespace is present as a non-private member."""
        self.__noLoadNamespaces.add(pyxb.namespace.NamespaceInstance(namespace))
    __noloadNamespaces = None

    def preLoadArchives (self):
        """A list of paths to archives that should be loaded, in order, prior to parsing schema."""
        return frozenset(self.__preLoadArchives)
    def addPreLoadArchive (self, archive_file):
        """Name of a file containing a stored archive from which
        namespaces should be read prior to processing schema.

        Files to be pre-loaded are not affected by
        C{noLoadNamespace}."""
        self.__preLoadArchives.append(archive_file)
    def _setPreLoadArchives (self, pre_load_archives):
        self.__preLoadArchives[:] = pre_load_archives
        return self
    __preLoadArchives = None

    def archiveToFile (self):
        """Optional file into which the archive of namespaces will be written.

        Subsequent generation actions can read pre-parsed namespaces
        from this file, and therefore reference the bindings that were
        built earlier rather than re-generating them.

        The file name should normally end with C{.wxs}."""
        return self.__archiveToFile
    def setArchiveToFile (self, archive_to_file):
        self.__archiveToFile = archive_to_file
        return self
    __archiveToFile = None

    def setNamespaceVisibility (self, namespace, visibility):
        namespace = pyxb.namespace.NamespaceInstance(namespace)
        self.__namespaceVisibilityMap[namespace] = visibility
        pass
    def _setNamespaceVisibilities (self, public, private):
        if public is None:
            public = set()
        if private is None:
            private = set()
        self.__namespaceVisibilityMap.clear()
        self.__namespaceVisibilityMap.update(dict.fromkeys(public, True))
        self.__namespaceVisibilityMap.update(dict.fromkeys(private, False))
    def namespaceVisibilityMap (self):
        """Indicates, for specific namespaces, whether their
        visibility in the archive should be public or private."""
        return self.__namespaceVisibilityMap.copy()
    __namespaceVisibilityMap = None

    def defaultNamespacePublic (self):
        """Indicates whether namespaces that do not have visibilities set will be public (default) or private."""
        return self.__defaultNamespacePublic
    def setDefaultNamespacePublic (self, default_namespace_public):
        self.__defaultNamespacePublic = default_namespace_public
    __defaultNamespacePublic = None

    def validateChanges (self):
        """Indicates whether the bindings should validate mutations
        against the content model."""
        return self.__validateChanges
    def setValidateChanges (self, validate_changes):
        #raise pyxb.IncompleteImplementationError('No support for disabling validation')
        self.__validateChanges = validate_changes
        return self
    __validateChanges = None

    _DEFAULT_bindingStyle = basis.CURRENT_BINDING_STYLE
    def bindingStyle (self):
        """The style of Python used in generated bindings.

        C{accessor} means values are private variables accessed
        through inspector and mutator methods.

        C{property} means values are private variables accessed
        through a Python property.
        """
        return self.__bindingStyle
    def setBindingStyle (self, binding_style):
        raise pyxb.IncompleteImplementationError('No support for binding style configuration')
        self.__bindingStyle = binding_style
        return self
    __bindingStyle = None

    def writeForCustomization (self):
        """Indicates whether the binding Python code should be written into a sub-module for customization.

        If enabled, a module C{path.to.namespace} will be written to
        the file C{path/to/raw/namespace.py}, so that the file
        C{path/to/namespace.py} can import it and override behavior."""
        return self.__writeForCustomization
    def setWriteForCustomization (self, write_for_customization):
        self.__writeForCustomization = write_for_customization
        return self
    __writeForCustomization = None

    def allowAbsentModule (self):
        """Indicates whether the code generator is permitted to
        process namespace for which no module path can be determined.

        Use this only when generating bindings that will not be
        referenced by other bindings."""
        return self.__allowAbsentModule
    def setAllowAbsentModule (self, allow_absent_module):
        self.__allowAbsentModule = allow_absent_module
        return self
    __allowAbsentModule = None

    def allowBuiltinGeneration (self):
        """Indicates whether bindings will be written for namespaces that are built-in to PyXB.

        This must be enabled when building bindings for the XML,
        XMLSchema instance, and other built-in namespaces.  Normally
        generation of these namespaces is inhibited lest it produce
        inconsistencies."""
        return self.__allowBuiltinGeneration
    def setAllowBuiltinGeneration (self, allow_builtin_generation):
        self.__allowBuiltinGeneration = allow_builtin_generation
        return self
    __allowBuiltinGeneration = None

    def __init__ (self, *args, **kw):
        """Create a configuration to be used for generating bindings.

        Arguments are treated as additions to the schema location list
        after all keywords have been processed.

        @keyword binding_root: Invokes L{setBindingRoot}
        @keyword schema_root: Invokes L{setSchemaRoot}
        @keyword schema_stripped_prefix: Invokes L{setSchemaStrippedPrefix}
        @keyword schema_location_list: Invokes L{setSchemaLocationList}
        @keyword module_list: Invokes L{_setModuleList}
        @keyword module_prefix: Invokes L{setModulePrefix}
        @keyword archive_path: Invokes L{setArchivePath}
        @keyword no_load_namespaces: Invokes L{_setNoLoadNamespaces}
        @keyword pre_load_archives: Invokes L{_setPreLoadArchives}
        @keyword archive_to_file: Invokes L{setArchiveToFile}
        @keyword public_namespace: Invokes L{_setNamespaceVisibility}
        @keyword private_namespace: Invokes L{_setNamespaceVisibility}
        @keyword default_namespace_public: Invokes L{setDefaultNamespacePublic}
        @keyword validate_changes: Invokes L{setValidateChanges}
        @keyword binding_style: Invokes L{setBindingStyle}
        @keyword namespace_module_map: Initializes L{namespaceModuleMap}
        @keyword schemas: Invokes L{setSchemas}
        @keyword namespaces: Invokes L{setNamespaces}
        @keyword write_for_customization: Invokes L{setWriteForCustomization}
        @keyword allow_builtin_generation: Invokes L{setAllowBuiltinGeneration}
        @keyword allow_absent_module: Invokes L{setAllowAbsentModule}
        @keyword generate_to_files: Sets L{generateToFiles}
        """
        argv = kw.get('argv', None)
        if argv is not None:
            kw = {}
        self.__bindingRoot = kw.get('binding_root', self._DEFAULT_bindingRoot)
        self.__schemaRoot = kw.get('schema_root', '.')
        self.__schemaStrippedPrefix = kw.get('schema_stripped_prefix')
        self.__schemas = []
        self.__schemaLocationList = kw.get('schema_location_list', [])[:]
        self.__moduleList = kw.get('module_list', [])[:]
        self.__modulePrefix = kw.get('module_prefix')
        self.__archivePath = kw.get('archive_path', pyxb.namespace.GetArchivePath())
        self.__noLoadNamespaces = kw.get('no_load_namespaces', set()).copy()
        self.__preLoadArchives = kw.get('pre_load_archives', [])[:]
        self.__archiveToFile = kw.get('archive_to_file')
        self.__namespaceVisibilityMap = {}
        self._setNamespaceVisibilities(kw.get('public_namespaces', set()), kw.get('private_namespaces', set()))
        self.__defaultNamespacePublic = kw.get('default_namespace_public', True)
        self.__validateChanges = kw.get('validate_changes', True)
        self.__bindingStyle = kw.get('binding_style', self._DEFAULT_bindingStyle)
        self.__namespaceModuleMap = kw.get('namespace_module_map', {}).copy()
        self.__schemas = kw.get('schemas', [])[:]
        self.__namespaces = set(kw.get('namespaces', []))
        self.__writeForCustomization = kw.get('write_for_customization', False)
        self.__writeForCustomization = kw.get('allow_builtin_generation', False)
        self.__allowAbsentModule = kw.get('allow_absent_module', False)
        self.__generateToFiles = kw.get('generate_to_files', True)
        
        if argv is not None:
            self.applyOptionValues(*self.optionParser().parse_args(argv))
        [ self.addSchemaLocation(_a) for _a in args ]
        
        pyxb.namespace.XML.validateComponentModel()

    __stripSpaces_re = re.compile('\s\s\s+')
    def __stripSpaces (self, string):
        return self.__stripSpaces_re.sub(' ', string)
    
    __OptionSetters = (
        ('binding_root', setBindingRoot),
        ('schema_root', setSchemaRoot),
        ('schema_stripped_prefix', setSchemaStrippedPrefix),
        ('schema_location', setSchemaLocationList),
        ('module', _setModuleList),
        ('module_prefix', setModulePrefix),
        ('archive_path', setArchivePath),
        ('no_load_namespace', _setNoLoadNamespaces),
        ('pre_load_archive', _setPreLoadArchives),
        ('archive_to_file', setArchiveToFile),
        ('default_namespace_public', setDefaultNamespacePublic),
        ('binding_style', setBindingStyle),
        ('validate_changes', setValidateChanges),
        ('write_for_customization', setWriteForCustomization),
        ('allow_builtin_generation', setAllowBuiltinGeneration),
        ('allow_absent_module', setAllowAbsentModule)
        )
    def applyOptionValues (self, options, args=None):
        for (tag, method) in self.__OptionSetters:
            v = getattr(options, tag)
            if v is not None:
                method(self, v)
        public_namespaces = getattr(options, 'public_namespace')
        private_namespaces = getattr(options, 'private_namespace')
        self._setNamespaceVisibilities(public_namespaces, private_namespaces)
        if args is not None:
            self.__schemaLocationList.extend(args)

    def setFromCommandLine (self, argv=None):
        if argv is None:
            argv = sys.argv[1:]
        (options, args) = self.optionParser().parse_args(argv)
        self.applyOptionValues(options, args)
        return self

    def generationUID (self):
        return self.__generationUID
    __generationUID = None

    def optionParser (self, reset=False):
        """Return an C{optparse.OptionParser} instance tied to this configuration.

        @param reset: If C{False} (default), a parser created in a
        previous invocation will be returned.  If C{True}, any
        previous option parser is discarded and a new one created.
        @type reset: C{bool}
        """
        if reset or (self.__optionParser is None):
            parser = optparse.OptionParser(usage="%prog [options] [more schema locations...]",
                                           version='%%prog from PyXB %s' % (pyxb.__version__,),
                                           description='Generate bindings from a set of XML schemas')
            parser.add_option('--schema-location', '-u', metavar="FILE_or_URL",
                              action='append',
                              help=self.__stripSpaces(self.addSchemaLocation.__doc__))
            parser.add_option('--module', '-m', metavar="MODULE",
                              action='append',
                              help=self.__stripSpaces(self.addModuleName.__doc__))
            parser.add_option('--schema-root', metavar="DIRECTORY",
                              help=self.__stripSpaces(self.schemaRoot.__doc__))
            parser.add_option('--schema-stripped-prefix', metavar="TEXT", type='string',
                              help=self.__stripSpaces(self.schemaStrippedPrefix.__doc__))
            parser.add_option('--module-prefix', metavar="MODULE",
                              help=self.__stripSpaces(self.modulePrefix.__doc__))
            parser.add_option('--binding-root', metavar="DIRECTORY",
                              help=self.__stripSpaces(self.bindingRoot.__doc__))
            parser.add_option('--archive-path', metavar="PATH",
                              help=self.__stripSpaces(self.archivePath.__doc__))
            parser.add_option('--no-load-namespace', metavar="URI",
                              action='append',
                              help=self.__stripSpaces(self.addNoLoadNamespace.__doc__))
            parser.add_option('--pre-load-archive', metavar="FILE",
                              action='append',
                              help=self.__stripSpaces(self.addPreLoadArchive.__doc__))
            parser.add_option('--archive-to-file', metavar="FILE",
                              help=self.__stripSpaces(self.archiveToFile.__doc__))
            parser.add_option('--public-namespace', metavar="URI",
                              action='append',
                              help=self.__stripSpaces(self.namespaceVisibilityMap.__doc__ + ' This option adds the namespace as a public archive member.'))
            parser.add_option('--private-namespace', metavar="URI",
                              action='append',
                              help=self.__stripSpaces(self.namespaceVisibilityMap.__doc__ + ' This option adds the namespace as a private archive member.'))
            parser.add_option('--default-namespace-public',
                              action="store_true", dest='default_namespace_public',
                              help=self.__stripSpaces(self.defaultNamespacePublic.__doc__ + ' This option makes the default "public" (default).'))
            parser.add_option('--default-namespace-private',
                              action="store_false", dest='default_namespace_public',
                              help=self.__stripSpaces(self.defaultNamespacePublic.__doc__ + ' This option makes the default "private".'))
            parser.add_option('--binding-style',
                              type='choice', choices=basis.BINDING_STYLES,
                              help=self.__stripSpaces(self.bindingStyle.__doc__))
            parser.add_option('--validate-changes',
                              action='store_true', dest='validate_changes',
                              help=self.__stripSpaces(self.validateChanges.__doc__ + ' This option turns on validation (default).'))
            parser.add_option('--no-validate-changes',
                              action='store_false', dest='validate_changes',
                              help=self.__stripSpaces(self.validateChanges.__doc__ + ' This option turns off validation.'))
            parser.add_option('-r', '--write-for-customization',
                              action='store_true', dest='write_for_customization',
                              help=self.__stripSpaces(self.writeForCustomization.__doc__ + ' This option turns on the feature.'))
            parser.add_option('--no-write-for-customization',
                              action='store_false', dest='write_for_customization',
                              help=self.__stripSpaces(self.writeForCustomization.__doc__ + ' This option turns off the feature (default).'))
            parser.add_option('--allow-absent-module',
                              action='store_true', dest='allow_absent_module',
                              help=self.__stripSpaces(self.allowAbsentModule.__doc__ + ' This option turns on the feature.'))
            parser.add_option('--no-allow-absent-module',
                              action='store_false', dest='allow_absent_module',
                              help=self.__stripSpaces(self.allowAbsentModule.__doc__ + ' This option turns off the feature (default).'))
            parser.add_option('--allow-builtin-generation',
                              action='store_true', dest='allow_builtin_generation',
                              help=self.__stripSpaces(self.allowBuiltinGeneration.__doc__ + ' This option turns on the feature.'))
            parser.add_option('--no-allow-builtin-generation',
                              action='store_false', dest='allow_builtin_generation',
                              help=self.__stripSpaces(self.allowBuiltinGeneration.__doc__ + ' This option turns off the feature (default).'))
            self.__optionParser = parser
        return self.__optionParser
    __optionParser = None

    def getCommandLineArgs (self):
        """Return a command line option sequence that could be used to
        construct an equivalent configuration.

        @note: If you extend the option parser, as is done by
        C{pyxbgen}, this may not be able to reconstruct the correct
        command line."""
        opts = []
        module_list = self.moduleList()
        schema_list = self.schemaLocationList()
        while module_list and schema_list:
            ml = module_list.pop(0)
            sl = schema_list.pop(0)
            opts.extend(['--schema-location=' + sl, '--module=' + ml])
        for sl in schema_list:
            opts.append('--schema-location=' + sl)
        if self.schemaRoot() is not None:
            opts.append('--schema-root=' + self.schemaRoot())
        if self.schemaStrippedPrefix() is not None:
            opts.append('--schema-stripped-prefix=%s' + self.schemaStrippedPrefix())
        if self.modulePrefix() is not None:
            opts.append('--module-prefix=' + self.modulePrefix())
        opts.append('--binding-root=' + self.bindingRoot())
        if self.archivePath() is not None:
            opts.append('--archive-path=' + self.archivePath())
        for ns in self.noLoadNamespaces():
            opts.append('--no-load-namespace=' + ns.uri())
        for fps in self.preLoadArchives():
            opts.append('--pre-load-archive=' + fp)
        if self.archiveToFile() is not None:
            opts.append('--archive-to-file=' + self.archiveToFile())
        for (ns, visibility) in self._namespaceVisibilityMap():
            if visibility:
                opts.append('--public-namespace=' + ns.uri())
            else:
                opts.append('--private-namespace=' + ns.uri())
        if self.defaultNamespacePublic():
            opts.append('--default-namespace-public')
        else:
            opts.append('--default-namespace-private')
        for (val, opt) in ( (self.validateChanges(), 'validate-changes'),
                            (self.writeForCustomization(), 'write-for-customization'),
                            (self.allowAbsentModule(), 'allow-absent-module'),
                            (self.allowBuiltinGeneration(), 'allow-builtin-generation') ):
            if val:
                opts.append('--' + opt)
            else:
                opts.append('--no-' + opt)
        return opts

    def normalizeSchemaLocation (self, sl):
        ssp = self.schemaStrippedPrefix()
        if ssp and sl.startswith(ssp):
            sl = sl[len(ssp):]
        return pyxb.utils.utility.NormalizeLocation(sl, self.schemaRoot())

    def __assignNamespaceModulePath (self, namespace, module_path=None):
        assert isinstance(namespace, pyxb.namespace.Namespace), 'unexpected type %s' % (type(namespace),)
        # Validate so we can pull any existing module path from the archive
        namespace.validateComponentModel()
        if namespace.modulePath() is not None:
            return namespace
        if namespace.isAbsentNamespace():
            namespace.setModulePath(module_path)
            return namespace
        if (module_path is None) and not (namespace.prefix() is None):
            module_path = namespace.prefix()
        module_path = self.namespaceModuleMap().get(namespace.uri(), module_path)
        if module_path is None:
            if self.allowAbsentModule() or (pyxb.namespace.XMLSchema_instance == namespace):
                return namespace
            raise pyxb.BindingGenerationError('No prefix or module name available for %s' % (namespace,))
        if self.modulePrefix(): # non-empty value
            module_path = '.'.join([self.modulePrefix(), module_path])
        namespace.setModulePath(module_path)
        return namespace

    __didResolveExternalSchema = False
    def resolveExternalSchema (self, reset=False):
        if self.__didResolveExternalSchema and (not reset):
            raise pyxb.PyXBException('Cannot resolve external schema multiple times')

        if self.__generationUID is not None:
            # This isn't safe until we have a way to reset everything.
            print 'WARNING: Unsafe to perform multiple generations in one run'
            assert False

        self.__generationUID = pyxb.utils.utility.UniqueIdentifier()

        required_archives = pyxb.namespace.NamespaceArchive.PreLoadArchives(self.archivePath(), self.preLoadArchives())
        for nsa in required_archives:
            nsa.readNamespaces()
        for ns in self.noLoadNamespaces():
            assert isinstance(ns, pyxb.namespace.Namespace)
            ns.markNotLoadable()
        while self.__schemaLocationList:
            sl = self.__schemaLocationList.pop(0)
            try:
                schema = xs.schema.CreateFromLocation(absolute_schema_location=self.normalizeSchemaLocation(sl), generation_uid=self.generationUID())
                self.addSchema(schema)
            except pyxb.SchemaUniquenessError, e:
                print 'WARNING: Skipped redundant translation of %s defining %s' % (e.schemaLocation(), e.namespace())
                self.addSchema(e.existingSchema())
        for schema in self.__schemas:
            ns = schema.targetNamespace()
            #print 'namespace %s' % (ns,)
            module_path = None
            if self.__moduleList:
                module_path = self.__moduleList.pop(0)
            self.__assignNamespaceModulePath(ns, module_path)
            self.addNamespace(ns)
        self.__didResolveExternalSchema = True
        self.__bindingModules = None

    def __buildBindingModules (self):
        modules = set()
    
        entry_namespaces = self.namespaces()
        nsdep = pyxb.namespace.NamespaceDependencies(namespace_set=self.namespaces())
        siblings = nsdep.siblingNamespaces()
        missing = nsdep.schemaDefinedNamespaces().difference(siblings)
        siblings.update(missing)
        nsdep.setSiblingNamespaces(siblings)
        self.__namespaces.update(siblings)
        #namespace_order = []
        #[ namespace_order.extend(_scc) for _scc in nsdep.namespaceOrder() ]
        #print "\n".join([ str(_ns) for _ns in namespace_order ])
        #print '%d one, %d dep, %d sib' % (len(self.namespaces()), len(namespace_order), len(siblings))
        for ns in self.namespaces(): # namespace_order:
            ns.validateComponentModel()
            self.__assignNamespaceModulePath(ns)
            if (ns.modulePath() is None) and not (ns.isAbsentNamespace() or self.allowAbsentModule() or (pyxb.namespace.XMLSchema_instance == ns)):
                raise pyxb.BindingGenerationError('No module path available for %s' % (ns,))
        if 0 < len(missing):
            text = []
            text.append('WARNING: Adding the following namespaces due to dependencies:')
            for ns in missing:
                self.__assignNamespaceModulePath(ns)
                text.append('  %s, prefix %s, module path %s' % (ns, ns.prefix(), ns.modulePath()))
                for sch in ns.schemas():
                    text.append('    schemaLocation=%s' % (sch.location(),))
            print "\n".join(text)

        for ns_set in nsdep.namespaceOrder():
            pyxb.namespace.ResolveSiblingNamespaces(ns_set, self.__generationUID)
    
        file('namespace.dot', 'w').write(nsdep.namespaceGraph()._generateDOT('Namespace'))
        file('component.dot', 'w').write(nsdep.componentGraph()._generateDOT('Component', lambda _c: _c.bestNCName()))
    
        all_components = set()
        namespace_component_map = {}
        _process_builtins = False # Set to True for XMLSchema
        for sns in siblings:
            if (pyxb.namespace.XMLSchema == sns) and (not _process_builtins):
                continue
            for c in sns.components():
                if (isinstance(c, xs.structures.ElementDeclaration) and c._scopeIsGlobal()) or c.isTypeDefinition():
                    assert (c._schema() is None) or (c._schema().targetNamespace() == sns)
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
                    nsm = NamespaceModule(self, ns, ns_scc, namespace_component_map.get(ns, ns.components()))
                    modules.add(nsm)
                else:
                    nsm = NamespaceModule(self, ns, ns_scc)
                module_graph.addNode(nsm)
                namespace_module_map[ns] = nsm
                assert ns == nsm.namespace()
    
                if nsg_head is None:
                    nsg_head = nsm.namespaceGroupHead()
                namespace_modules.append(nsm)
    
            if (nsg_head is not None) and (not nsg_head.namespace().isLoadedNamespace()) and nsg_head.namespaceGroupMulti():
                ngm = NamespaceGroupModule(self, namespace_modules)
                modules.add(ngm)
                module_graph.addNode(ngm)
                for nsm in namespace_modules:
                    module_graph.addEdge(ngm, nsm)
                    nsm.setNamespaceGroupModule(ngm)
                assert namespace_module_map[nsg_head.namespace()].namespaceGroupModule() == ngm
    
        file('modules.dot', 'w').write(module_graph._generateDOT('Modules'))
    
        component_csets = nsdep.componentOrder()
        bad_order = False
        component_order = []
        for cset in component_csets:
            if 1 < len(cset):
                print "COMPONENT DEPENDENCY LOOP of %d components" % (len(cset),)
                cg = pyxb.utils.utility.Graph()
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
                nsm.bindComponent(c)
                element_declarations.append(c)
            else:
                type_definitions.append(c)
    
        simple_type_definitions = []
        complex_type_definitions = []
        for td in type_definitions:
            nsm = namespace_module_map.get(td.bindingNamespace())
            assert nsm is not None, 'No namespace module for %s type %s scope %s namespace %s' % (td.expandedName(), type(td), td._scope(), td.bindingNamespace)
            module_context = nsm.bindComponent(td)
            assert isinstance(module_context, _ModuleNaming_mixin), 'Unexpected type %s' % (type(module_context),)
            if isinstance(td, xs.structures.SimpleTypeDefinition):
                _PrepareSimpleTypeDefinition(td, self, nsm, module_context)
                simple_type_definitions.append(td)
            elif isinstance(td, xs.structures.ComplexTypeDefinition):
                _PrepareComplexTypeDefinition(td, self, nsm, module_context)
                complex_type_definitions.append(td)
            else:
                assert False, 'Unexpected component type %s' % (type(td),)
    
    
        for ngm in modules:
            if isinstance(ngm, NamespaceGroupModule):
                for m in ngm.namespaceModules():
                    m.addImportsFrom(ngm)
    
        for std in simple_type_definitions:
            GenerateSTD(std, self)
        for ctd in complex_type_definitions:
            GenerateCTD(ctd, self)
        for ed in element_declarations:
            GenerateED(ed, self)
    
        return modules
    
    __bindingModules = None
    def bindingModules (self, reset=False):
        if reset or (not self.__didResolveExternalSchema):
            self.resolveExternalSchema(reset)
        if reset or (self.__bindingModules is None):
            self.__bindingModules = self.__buildBindingModules()
        return self.__bindingModules
    
    def writeNamespaceArchive (self):
        archive_file = self.archiveToFile()
        if archive_file is not None:
            ns_archive = pyxb.namespace.NamespaceArchive(namespaces=self.namespaces(), generation_uid=self.generationUID())
            try:
                ns_archive.writeNamespaces(pyxb.utils.utility.OpenOrCreate(archive_file))
                print 'Saved parsed schema to %s URI' % (archive_file,)
            except Exception, e:
                print 'Exception saving preprocessed schema to %s: %s' % (archive_file, e)
                traceback.print_exception(*sys.exc_info())
                try:
                    os.unlink(component_model_file)
                except (OSError, IOError), e:
                    pass
                if isinstance(e, (AssertionError, AttributeError, TypeError)):
                    raise

    def moduleForComponent (self, component):
        return _ModuleNaming_mixin.ComponentBindingModule(component)
