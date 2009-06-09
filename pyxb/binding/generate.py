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

# Initialize UniqueInBinding with the public identifiers we generate,
# import, or otherwise can't have mucked about with.
UniqueInBinding = set([ 'pyxb', 'xml', 'sys', 'Namespace', 'CreateFromDOM', 'ElementToBindingMap' ])
PostscriptItems = []

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

    __anonymousIndex = 0
    @classmethod
    def __NextAnonymousIndex (cls):
        cls.__anonymousIndex += 1
        return cls.__anonymousIndex

    __ComponentTagMap = {
        xs.structures.SimpleTypeDefinition: 'STD'
        , xs.structures.ComplexTypeDefinition: 'CTD'
        , xs.structures.ElementDeclaration: 'ED'
        , xs.structures.Wildcard: 'WC'
        }

    def __init__ (self, component, **kw):
        self.__component = component
        btns = kw['binding_target_namespace']
        tns = self.__component.targetNamespace()
        is_in_binding = (btns == tns) or (tns is None)
            
        if not ((not isinstance(self.__component, pyxb.namespace._Resolvable_mixin)) or self.__component.isResolved()):
            print '%s not resolved' % (self.__component,)
        assert (not isinstance(self.__component, pyxb.namespace._Resolvable_mixin)) or self.__component.isResolved()

        name = self.__component.nameInBinding()
        if is_in_binding and (name is None):
            global UniqueInBinding

            # The only components that are allowed to be nameless at
            # this point are ones in the binding we're generating.
            # @todo should not have to special case XMLSchema
            if not (is_in_binding or (pyxb.namespace.XMLSchema == tns)):
                raise pyxb.LogicError('Attempt to reference unnamed component not in binding: %s' % (component,))

            # The initial name is the name of the component, or if the
            # component can't be named the name of something else
            # relevant.
            name = self.__component.bestNCName()
            protected = False
            if name is None:
                tag = self.__ComponentTagMap.get(type(self.__component), None)
                if tag is None:
                    raise pyxb.LogicError('Not prepared for reference to component type %s' % (self.__component.__class__.__name__,))
                name = '_%s_ANON_%d' % (tag, self.__NextAnonymousIndex())
                protected = True

            # Element declarations may be local, in which case we want
            # to incorporate the parentage in the name.
            if isinstance(self.__component, xs.structures._ScopedDeclaration_mixin):
                scope = self.__component.scope()
                if scope is None:
                    print 'NO SCOPE for %s' % (self.__component,)
                assert scope is not None
                if isinstance(scope, xs.structures.ComplexTypeDefinition):
                    name_prefix = scope.name()
                    if name_prefix is None:
                        assert scope.owner() is not None
                        name_prefix = scope.owner().name()
                    assert name_prefix is not None
                    name = '%s_%s' % (name_prefix, name)

            name = utility.PrepareIdentifier(name, UniqueInBinding, protected=protected)
            self.__component.setNameInBinding(name)
        if not is_in_binding:
            assert name is not None, 'name %s component %s' % (name, self.__component)
            mp = None
            if pyxb.namespace.XMLSchema == tns:
                mp = 'pyxb.binding.datatypes'
            elif tns is not None:
                mp = tns.modulePath()
                assert mp is not None
            if mp is not None:
                name = '%s.%s' % (mp, name)
        self.setLiteral(name)

class ReferenceNamespace (ReferenceLiteral):
    __namespace = None

    def __init__ (self, **kw):
        self.__namespace = kw['namespace']
        btns = kw['binding_target_namespace']
        super(ReferenceNamespace, self).__init__(**kw)
        assert self.__namespace is not None
        ns = None
        if pyxb.namespace.XMLSchema == self.__namespace:
            ns = 'pyxb.namespace.XMLSchema'
        elif btns == self.__namespace:
            ns = 'Namespace'
        else:
            mp = self.__namespace.modulePath()
            assert mp is not None
            ns = '%s.Namespace' % (mp,)
        self.setLiteral(ns)

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


def GenerateModelGroupAll (ctd, mga, template_map, **kw):
    mga_tag = '__AModelGroup'
    template_map['mga_tag'] = mga_tag
    lines = []
    lines2 = []
    for ( dfa, is_required ) in mga.particles():
        ( dfa_tag, dfa_lines ) = GenerateContentModel(ctd, dfa, **kw)
        lines.extend(dfa_lines)
        template_map['dfa_tag'] = dfa_tag
        template_map['is_required'] = pythonLiteral(is_required, **kw)
        lines2.append(templates.replaceInText('    %{content}.ModelGroupAllAlternative(%{ctd}.%{dfa_tag}, %{is_required}),', **template_map))
    lines.append(templates.replaceInText('%{mga_tag} = %{content}.ModelGroupAll(alternatives=[', **template_map))
    lines.extend(lines2)
    lines.append('])')
    return (mga_tag, lines)

def GenerateContentModel (ctd, automaton, **kw):
    cmi = None
    template_map = { }
    template_map['ctd'] = pythonLiteral(ctd, **kw)
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
        template_map['state'] = pythonLiteral(state)
        template_map['is_final'] = pythonLiteral(None in transitions)

        lines2.append(templates.replaceInText('%{state_comma} %{state} : %{content}.ContentModelState(state=%{state}, is_final=%{is_final}, transitions=[', **template_map))
        template_map['state_comma'] = ','
        lines3 = []
        for (key, destinations) in transitions.items():
            if key is None:
                continue
            assert 1 == len(destinations)
            template_map['next_state'] = pythonLiteral(list(destinations)[0], **kw)
            if isinstance(key, xs.structures.Wildcard):
                template_map['eu_field'] = pythonLiteral(None, **kw)
                template_map['term'] = pythonLiteral(key, **kw)
            elif isinstance(key, nfa.AllWalker):
                (mga_tag, mga_defns) = GenerateModelGroupAll(ctd, key, template_map.copy(), **kw)
                template_map['term'] = mga_tag
                lines.extend(mga_defns)
                template_map['eu_field'] = pythonLiteral(None, **kw)
            else:
                assert isinstance(key, xs.structures.ElementDeclaration)
                template_map['term'] = pythonLiteral(key, **kw)
                template_map['eu_field'] = templates.replaceInText('%{ctd}._UseForTag(%{field_tag})', field_tag=pythonLiteral(key.expandedName(), **kw), **template_map)
            lines3.append(templates.replaceInText('%{content}.ContentModelTransition(term=%{term}, next_state=%{next_state}, element_use=%{eu_field}),',
                          **template_map))
        lines2.extend([ '    '+_l for _l in lines3 ])
        lines2.append("])")

    lines.append(templates.replaceInText('%{ctd}.%{cm_tag} = %{content}.ContentModel(state_map = {', **template_map))
    lines.extend(['    '+_l for _l in lines2 ])
    lines.append("})")
    return (cmi, lines)

def GenerateFacets (outf, td, **kw):
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
        outf.write("%s = %s(%s)\n" % pythonLiteral( (facet_var, fc, argset ), **kw))
        facet_instances.append(pythonLiteral(facet_var, **kw))
        if (fi is not None) and is_collection:
            for i in fi.items():
                if isinstance(i, facets._EnumerationElement):
                    enum_member = ReferenceEnumerationMember(type_definition=td, facet_instance=fi, enumeration_element=i, **kw)
                    outf.write("%s = %s.addEnumeration(unicode_value=%s)\n" % pythonLiteral( (enum_member, facet_var, i.unicodeValue() ), **kw))
                    if fi.enumPrefix() is not None:
                        outf.write("%s_%s = %s\n" % (fi.enumPrefix(), i.tag(), pythonLiteral(enum_member, **kw)))
                if isinstance(i, facets._PatternElement):
                    outf.write("%s.addPattern(pattern=%s)\n" % pythonLiteral( (facet_var, i.pattern ), **kw))
    if 2 <= len(facet_instances):
        map_args = ",\n   ".join(facet_instances)
    else:
        map_args = ','.join(facet_instances)
    outf.write("%s._InitializeFacetMap(%s)\n" % (pythonLiteral(td, **kw), map_args))

def GenerateSTD (std, **kw):
    generate_facets = kw.get('generate_facets', False)
    outf = StringIO.StringIO()

    class_keywords = frozenset(basis.simpleTypeDefinition._ReservedSymbols)
    class_unique = set()
    kw['class_keywords'] = class_keywords
    kw['class_unique'] = class_unique

    parent_classes = [ pythonLiteral(std.baseTypeDefinition(), **kw) ]
    enum_facet = std.facets().get(facets.CF_enumeration, None)
    if (enum_facet is not None) and (enum_facet.ownerTypeDefinition() == std):
        parent_classes.append('pyxb.binding.basis.enumeration_mixin')
        
    template_map = { }
    template_map['std'] = pythonLiteral(std, **kw)
    template_map['superclasses'] = ''
    if 0 < len(parent_classes):
        template_map['superclasses'] = ', '.join(parent_classes)
    template_map['expanded_name'] = pythonLiteral(std.expandedName(), **kw)

    # @todo: Extensions of LIST will be wrong in below

    if xs.structures.SimpleTypeDefinition.VARIETY_absent == std.variety():
        assert False
        return None
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
        template_map['itemtype'] = pythonLiteral(std.itemTypeDefinition(), **kw)
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

    if std.name() is not None:
        outf.write(templates.replaceInText("Namespace.addCategoryObject('typeBinding', %{localName}, %{std})\n",
                                           localName=pythonLiteral(std.name(), **kw), **template_map))
    return outf.getvalue()

def TypeSetCompatible (s1, s2):
    for ctd1 in s1:
        match = False
        for ctd2 in s2:
            if ctd1.name() == ctd2.name():
                match = True
                break
        if not match:
            return False
    return True

def expandedNameToUseMap (expanded_name, container_name, class_unique, class_keywords, kw):
    use_map = { }
    unique_name = utility.PrepareIdentifier(expanded_name.localName(), class_unique, class_keywords)
    use_map['id'] = unique_name
    use_map['inspector'] = unique_name
    use_map['mutator'] = utility.PrepareIdentifier('set' + unique_name[0].upper() + unique_name[1:], class_unique, class_keywords)
    use_map['use'] = utility.MakeUnique('__' + unique_name.strip('_'), class_unique)
    use_map['key'] = utility.PrepareIdentifier('%s_%s' % (container_name, expanded_name), class_unique, class_keywords, private=True)
    use_map['name'] = str(expanded_name)
    use_map['name_expr'] = pythonLiteral(expanded_name, **kw)
    return use_map

def GenerateCTD (ctd, **kw):
    content_type = None
    prolog_template = None
    template_map = { }
    template_map['ctd'] = pythonLiteral(ctd, **kw)
    base_type = ctd.baseTypeDefinition()
    content_type_tag = ctd._contentTypeTag()

    template_map['base_type'] = pythonLiteral(base_type, **kw)
    template_map['expanded_name'] = pythonLiteral(ctd.expandedName(), **kw)
    template_map['simple_base_type'] = pythonLiteral(None, **kw)
    template_map['contentTypeTag'] = content_type_tag
    template_map['is_abstract'] = repr(not not ctd.abstract())

    need_content = False
    content_basis = None
    if (ctd.CT_SIMPLE == content_type_tag):
        content_basis = ctd.contentType()[1]
        template_map['simple_base_type'] = pythonLiteral(content_basis, **kw)
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
    template_map['superclass'] = pythonLiteral(base_type, **kw)
    if isinstance(base_type, xs.structures.SimpleTypeDefinition) or base_type.isUrTypeDefinition():
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
    datatype_items = []

    definitions = []

    definitions.append('# Base type is %{base_type}')

    # Retain in the ctd the information about the element
    # infrastructure, so it can be inherited where appropriate in
    # subclasses.

    if isinstance(content_basis, xs.structures.Particle):
        plurality_data = content_basis.pluralityData().nameBasedPlurality()

        # name - String value of expanded name of the attribute (attr_tag, attr_ns)
        # name_expr - Python expression for an expanded name identifying the attribute (attr_tag)
        # use - Binding variable name holding AttributeUse instance (attr_name)
        # id - Python identifier for attribute (python_attr_name)
        # key - String used as dictionary key holding instance value of attribute (value_attr_name)
        # inspector - Name of the method used for inspection (attr_inspector)
        # mutator - Name of the method use for mutation (attr_mutator)

        PostscriptItems.append("\n\n")
        for (expanded_name, (is_plural, ed)) in plurality_data.items():
            # @todo Detect and account for plurality change between this and base
            if ed.scope() == ctd:
                ef_map = expandedNameToUseMap(ed.expandedName(), template_map['ctd'], class_unique, class_keywords, kw)
                aux_init = []
                ef_map['is_plural'] = repr(is_plural)
                element_uses.append(templates.replaceInText('%{name_expr} : %{use}', **ef_map))
                datatype_items.append("%s : %s" % (ef_map['name_expr'], pythonLiteral(ed, **kw)))
                if 0 == len(aux_init):
                    ef_map['aux_init'] = ''
                else:
                    ef_map['aux_init'] = ', ' + ', '.join(aux_init)
                ed.__elementFields = ef_map
            ef_map = ed.__elementFields

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
        return self.%{use}.setValue(self, new_value)''', **ef_map))

        fa = nfa.Thompson(content_basis).nfa()
        fa = fa.buildDFA()
        (cmi, cmi_defn) = GenerateContentModel(ctd=ctd, automaton=fa, **kw)
        PostscriptItems.append("\n".join(cmi_defn))
        PostscriptItems.append("\n")

    if need_content:
        PostscriptItems.append(templates.replaceInText('''
%{ctd}._Content = %{particle}
''', **template_map))
        

    PostscriptItems.append('''
%s._UpdateElementDatatypes({
    %s
})
''' % (template_map['ctd'], ",\n    ".join(datatype_items)))


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
        if ad.scope() == ctd:
            au_map = expandedNameToUseMap(ad.expandedName(), template_map['ctd'], class_unique, class_keywords, kw)

            assert ad.typeDefinition() is not None
            au_map['attr_type'] = pythonLiteral(ad.typeDefinition(), **kw)
                            
            vc_source = ad
            if au.valueConstraint() is not None:
                vc_source = au
            aux_init = []
            if vc_source.fixed() is not None:
                aux_init.append('fixed=True')
                aux_init.append('unicode_default=%s' % (pythonLiteral(vc_source.fixed(), **kw),))
            elif vc_source.default() is not None:
                aux_init.append('unicode_default=%s' % (pythonLiteral(vc_source.default(), **kw),))
            if au.required():
                aux_init.append('required=True')
            if au.prohibited():
                aux_init.append('prohibited=True')
            if 0 == len(aux_init):
                au_map['aux_init'] = ''
            else:
                aux_init.insert(0, '')
                au_map['aux_init'] = ', '.join(aux_init)
            ad.__attributeFields = au_map
        au_map = ad.__attributeFields
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

        attribute_uses.append(templates.replaceInText('%{name_expr} : %{use}', **au_map))
        definitions.append(templates.replaceInText('''
    # Attribute %{name} uses Python identifier %{id}
    %{use} = pyxb.binding.content.AttributeUse(%{name_expr}, '%{id}', '%{key}', %{attr_type}%{aux_init})
    def %{inspector} (self):
        """Get the attribute value for %{name}."""
        return self.%{use}.value(self)
    def %{mutator} (self, new_value):
        """Set the attribute value for %{name}.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.%{use}.setValue(self, new_value)''', **au_map))

    if ctd.attributeWildcard() is not None:
        definitions.append('_AttributeWildcard = %s' % (pythonLiteral(ctd.attributeWildcard(), **kw),))
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
        template_map['registration'] = templates.replaceInText("Namespace.addCategoryObject('typeBinding', %{localName}, %{ctd})",
                                                               localName=pythonLiteral(ctd.name(), **kw), **template_map)
    
    template = ''.join([prolog_template,
               "    ", "\n    ".join(definitions), "\n",
               map_decl, '''
%{registration}

'''])

    return templates.replaceInText(template, **template_map)

def elementDeclarationMap (ed, **kw):
    template_map = { }
    template_map['class'] = pythonLiteral(ed, **kw)
    template_map['localName'] = pythonLiteral(ed.name(), **kw)
    template_map['name'] = str(ed.expandedName())
    template_map['name_expr'] = pythonLiteral(ed.expandedName(), **kw)
    if (ed.SCOPE_global == ed.scope()):
        template_map['map_update'] = templates.replaceInText("Namespace.addCategoryObject('elementBinding', %{localName}, %{class})", **template_map)
    else:
        template_map['scope'] = pythonLiteral(ed.scope(), **kw)
    if ed.abstract():
        template_map['abstract'] = pythonLiteral(ed.abstract(), **kw)
    if ed.nillable():
        template_map['nillable'] = pythonLiteral(ed.nillable(), **kw)
    if ed.default():
        template_map['defaultValue'] = pythonLiteral(ed.default(), **kw)
    template_map['typeDefinition'] = pythonLiteral(ed.typeDefinition(), **kw)
    if ed.substitutionGroupAffiliation() is not None:
        template_map['substitutionGroupAffiliation'] = pythonLiteral(ed.substitutionGroupAffiliation(), **kw)
    return template_map

def GenerateED (ed, **kw):
    # Unscoped declarations should never be referenced in the binding.
    if ed._scopeIsIndeterminate():
        return ''

    outf = StringIO.StringIO()
    template_map = elementDeclarationMap(ed, **kw)
    template_map.setdefault('scope', pythonLiteral(None, **kw))
    template_map.setdefault('map_update', '')

    aux_init = { }
    for (k, p) in [ ('nillable', 'nillable'), ('abstract', 'abstract'), ('substitutionGroupAffiliation', 'substitution_group_affiliation'), ('scope', 'scope')]:
        v = template_map.get(k)
        if v is not None:
            aux_init[p] = v
    template_map['aux_init'] = ''
    if 0 < len(aux_init):
        template_map['aux_init'] = ',' + ','.join([ '%s=%s' % _i for _i in aux_init.items() ])

    outf.write(templates.replaceInText('''

__ignore = pyxb.binding.basis.element2(%{name_expr}, %{typeDefinition}%{aux_init})

# ElementDeclaration
class %{class} (pyxb.binding.basis.element):
    _ExpandedName = %{name_expr}
    _ElementScope = %{scope}
    _TypeDefinition = %{typeDefinition}
    #_SubstitutionGroupAffiliation = %{substitutionGroupAffiliation}
%{map_update}
''', **template_map))

    return outf.getvalue()

GeneratorMap = {
    xs.structures.SimpleTypeDefinition : GenerateSTD
  , xs.structures.ElementDeclaration : GenerateED
  , xs.structures.ComplexTypeDefinition : GenerateCTD
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
            schema = xs.schema.CreateFromDOM(domutils.StringToDOM(file(schema_file).read()))
        if schema_file is None:
            schema_file = '<not provided>'

        generator_kw = kw.copy()
        generator_kw['binding_target_namespace'] = schema.targetNamespace()
        outf = StringIO.StringIO()

        generate_facets = kw.get('generate_facets', False)
        if generate_facets:
            ns = schema.targetNamespace()
            generator_kw['class_unique'] = set()
            generator_kw['class_keywords'] = set()
            stds = [ ]
            num_unresolved = 0
            for td in ns.typeDefinitions().values():
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

        emit_order = schema.orderedComponents()
    
        import_prefix = 'pyxb.xmlschema.'
        if schema.targetNamespace() == pyxb.namespace.XMLSchema:
            import_prefix = ''

        template_map = { }
        template_map['input'] = schema_file
        template_map['date'] = str(datetime.datetime.now())
        template_map['version'] = 'UNSPECIFIED'
        tns = schema.targetNamespace()
        if tns is not None:
            tns = tns.uri()
        template_map['targetNamespace'] = repr(tns)
        template_map['import_prefix'] = import_prefix

        # "import" in import_namespaces means Python import, not XSD import
        import_namespaces = set()
        for ins in schema.importedNamespaces():
            ns = ins.namespace()
            if ns == schema.targetNamespace():
                continue
            if ns.modulePath() is None:
                if not ns.isBuiltinNamespace():
                    print 'WARNING: Dependency on %s with no module path' % (ns.uri(),)
                continue
            import_namespaces.add(ns)
        for ns in schema.referencedNamespaces():
            if ns == schema.targetNamespace():
                continue
            if ns.modulePath() is None:
                if not ns.isBuiltinNamespace():
                    print 'WARNING: Dependency on %s with no module path' % (ns.uri(),)
                continue
            print 'Adding due to dependency %s' % (ns,)
            import_namespaces.add(ns)
            
        template_map['aux_imports'] = "\n".join( [ 'import %s' % (_ns.modulePath(),) for _ns in import_namespaces ])

        if schema.targetNamespace().isAbsentNamespace():
            template_map['NamespaceDefinition'] = 'pyxb.namespace.CreateAbsentNamespace()'
        else:
            template_map['NamespaceDefinition'] = templates.replaceInText('pyxb.namespace.NamespaceForURI(%{targetNamespace}, create_if_missing=True)', **template_map)

        outf.write(templates.replaceInText('''# PyWXSB bindings for %{input}
# Generated %{date} by PyWXSB version %{version}
import pyxb.binding
import pyxb.exceptions_
import pyxb.utils.domutils
import sys

# Import bindings for namespaces imported into schema
%{aux_imports}

# Make sure there's a registered Namespace instance, and that it knows
# about this module.
Namespace = %{NamespaceDefinition}
Namespace._setModule(sys.modules[__name__])
Namespace.configureCategories(['typeBinding', 'elementBinding'])

def CreateFromDocument (xml_text):
    """Parse the given XML and use the document element to create a Python instance."""
    dom = pyxb.utils.domutils.StringToDOM(xml_text)
    return CreateFromDOM(dom.documentElement)

def CreateFromDOM (node):
    """Create a Python instance from the given DOM node.
    The node tag must correspond to an element declaration in this module."""
    return pyxb.binding.basis.element.AnyCreateFromDOM(node, Namespace)
''', **template_map))
    
        # Give priority for identifiers to scoped element declarations
        for td in emit_order:
            if (isinstance(td, xs.structures.ElementDeclaration)) and (td.scope() is not None):
                _ignored = ReferenceSchemaComponent(td, **generator_kw).asLiteral()

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
    
