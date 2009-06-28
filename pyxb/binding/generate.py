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
        bsm = kw.get('binding_schema')
        tns = self.__component.targetNamespace()
        is_in_binding = self.__component._picklesInNamespace(btns)
        is_in_module = is_in_binding and ((not btns.__dict__.get('__schemaHaveModules')) or ((bsm is None) or (bsm == self.__component._schema())))

        assert (not isinstance(self.__component, pyxb.namespace._Resolvable_mixin)) or self.__component.isResolved(), '%s not resolved' % (self.__component,)

        name = self.__component.nameInBinding()
        assert not(is_in_binding and (name is None)), 'Component %s is in binding but has no name' % (self.__component.expandedName(),)
        if not is_in_module:
            assert name is not None, 'name %s component %s' % (name, self.__component)
            mp = None
            if pyxb.namespace.XMLSchema == tns:
                mp = 'pyxb.binding.datatypes'
            elif not is_in_binding:
                mp = tns.modulePath()
                assert mp is not None
            else:
                mp = self.__component._schema().__dict__.get('__modulePath')
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
                template_map['kw_key'] = 'term'
                template_map['kw_val'] = pythonLiteral(key, **kw)
            elif isinstance(key, nfa.AllWalker):
                (mga_tag, mga_defns) = GenerateModelGroupAll(ctd, key, template_map.copy(), **kw)
                template_map['kw_key'] = 'term'
                template_map['kw_val'] = mga_tag
                lines.extend(mga_defns)
            else:
                assert isinstance(key, xs.structures.ElementDeclaration)
                template_map['kw_key'] = 'element_use'
                template_map['kw_val'] = templates.replaceInText('%{ctd}._UseForTag(%{field_tag})', field_tag=pythonLiteral(key.expandedName(), **kw), **template_map)
            lines3.append(templates.replaceInText('%{content}.ContentModelTransition(next_state=%{next_state}, %{kw_key}=%{kw_val}),',
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
    if ed.substitutionGroupAffiliation():
        template_map['substitution_group'] = pythonLiteral(ed.substitutionGroupAffiliation(), **kw)
    aux_init = []
    for k in ( 'nillable', 'abstract', 'scope' ):
        if k in template_map:
            aux_init.append('%s=%s' % (k, template_map[k]))
    template_map['element_aux_init'] = ''
    if 0 < len(aux_init):
        template_map['element_aux_init'] = ', ' + ', '.join(aux_init)
        
    return template_map

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

        PostscriptItems.append("\n\n")
        for (expanded_name, (is_plural, ed)) in plurality_data.items():
            # @todo Detect and account for plurality change between this and base
            if ed.scope() == ctd:
                ef_map = ed.__useMap
                ef_map.update(elementDeclarationMap(ed, **kw))
                aux_init = []
                ef_map['is_plural'] = repr(is_plural)
                element_uses.append(templates.replaceInText('%{use}.name() : %{use}', **ef_map))
                if 0 == len(aux_init):
                    ef_map['aux_init'] = ''
                else:
                    ef_map['aux_init'] = ', ' + ', '.join(aux_init)
                ed.__elementFields = ef_map
                ef_map['element_binding'] = utility.PrepareIdentifier('%s_elt' % (ef_map['id'],), class_unique, class_keywords, private=True)
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
        return self.%{use}.set(self, new_value)''', **ef_map))
            if is_plural:
                definitions.append(templates.replaceInText('''
    def %{appender} (self, new_value):
        """Add the value as another occurrence of the %{name} element.  Raises
        BadValueTypeException if the new value is not consistent with the
        element's type."""
        return self.%{use}.append(self, new_value)''', **ef_map))

            PostscriptItems.append(templates.replaceInText('''
%{ctd}._AddElement(pyxb.binding.basis.element(%{name_expr}, %{typeDefinition}%{element_aux_init}))
''', ctd=template_map['ctd'], **ef_map))

        fa = nfa.Thompson(content_basis).nfa()
        fa = fa.buildDFA()
        (cmi, cmi_defn) = GenerateContentModel(ctd=ctd, automaton=fa, **kw)
        PostscriptItems.append("\n".join(cmi_defn))
        PostscriptItems.append("\n")

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
        if ad.scope() == ctd:
            au_map = ad.__useMap
            assert isinstance(au_map, dict)

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

def GenerateED (ed, **kw):
    # Unscoped declarations should never be referenced in the binding.
    if not ed._scopeIsGlobal():
        return ''

    outf = StringIO.StringIO()
    template_map = elementDeclarationMap(ed, **kw)
    template_map.setdefault('scope', pythonLiteral(None, **kw))
    template_map.setdefault('map_update', '')

    outf.write(templates.replaceInText('''
%{class} = pyxb.binding.basis.element(%{name_expr}, %{typeDefinition}%{element_aux_init})
Namespace.addCategoryObject('elementBinding', %{class}.name().localName(), %{class})
''', **template_map))

    if ed.substitutionGroupAffiliation() is not None:
        PostscriptItems.append(templates.replaceInText('''
%{class}._setSubstitutionGroup(%{substitution_group})
''', **template_map))

    return outf.getvalue()

GeneratorMap = {
    xs.structures.SimpleTypeDefinition : GenerateSTD
  , xs.structures.ElementDeclaration : GenerateED
  , xs.structures.ComplexTypeDefinition : GenerateCTD
}

# Tuple of component classes in order in which they must be generated in
# order to satisfy the Python references between bindings.
# 
__ComponentOrder = (
    xs.structures.Annotation                   # no dependencies
  , xs.structures.IdentityConstraintDefinition # no dependencies
  , xs.structures.NotationDeclaration          # no dependencies
  , xs.structures.Wildcard                     # no dependencies
  , xs.structures.SimpleTypeDefinition         # no dependencies
  , xs.structures.AttributeDeclaration         # SimpleTypeDefinition
  , xs.structures.AttributeUse                 # AttributeDeclaration
  , xs.structures.AttributeGroupDefinition     # AttributeUse
  , xs.structures.ComplexTypeDefinition        # SimpleTypeDefinition, AttributeUse
  , xs.structures.ElementDeclaration           # *TypeDefinition
  , xs.structures.ModelGroup                   # ComplexTypeDefinition, ElementDeclaration, Wildcard
  , xs.structures.ModelGroupDefinition         # ModelGroup
  , xs.structures.Particle                     # ModelGroup, WildCard, ElementDeclaration
    )


def _ResolveReferencedNamespaces (namespace):
    ns_graph = utility.Graph(root=namespace)

    # Make sure all referenced namespaces have valid components
    need_check = set(namespace.referencedNamespaces())
    need_check.add(namespace)
    done_check = set()
    while 0 < len(need_check):
        ns = need_check.pop()
        ns.__schemaHaveModules = False
        for rns in ns.referencedNamespaces():
            ns_graph.addEdge(ns, rns)
            if not rns in done_check:
                need_check.add(rns)
        ns.validateComponentModel()
        if not ns.hasSchemaComponents():
            print 'WARNING: Referenced %s has no schema components' % (ns.uri(),)
        done_check.add(ns)

    scc_list = ns_graph.scc()
    if 0 < len(scc_list):
        print 'There are %d dependency cycles in the namespaces' % (len(scc_list),)
        for scc in scc_list:
            print " ".join([ str(_ns.prefix()) for _ns in scc])

    # Resolve all named objects in the referenced namespaces.  Iterate
    # where there are dependencies.
    need_resolved = set(done_check)
    while need_resolved:
        new_nr = set()
        for ns in need_resolved:
            if not ns.needsResolution():
                continue
            print 'Attempting resolution %s' % (ns.uri(),)
            if not ns.resolveDefinitions(allow_unresolved=True):
                print 'Holding incomplete resolution %s' % (ns.uri(),)
                new_nr.add(ns)
        if need_resolved == new_nr:
            raise pyxb.SchemaValidationError('Loop in namespace resolution')
        need_resolved = new_nr

def _PrepareNamespaceForGeneration (sns, module_path_prefix, all_std, all_ctd, all_ed):
    std = set()
    ctd = set()
    ed = set()
    for c in sns.components():
        if isinstance(c, xs.structures.SimpleTypeDefinition):
            std.add(c)
        elif isinstance(c, xs.structures.ComplexTypeDefinition):
            ctd.add(c)
        elif isinstance(c, xs.structures.ElementDeclaration) and c._scopeIsGlobal():
            ed.add(c)
        else:
            continue
        # Cache the namespace into which the component will be bound.
        # It certainly might not be reached by c.targetNamespace()
        # when c is an anonymous declaration.
        c.__bindingNamespace = sns
        assert c._schema().targetNamespace() == c.__bindingNamespace
    all_std.update(std)
    all_ctd.update(ctd)
    all_ed.update(ed)

    sns.__simpleTypeDefinitions = []
    sns.__complexTypeDefinitions = []
    sns.__elementDeclarations = []
    sns.__anonSTDIndex = 1
    sns.__anonCTDIndex = 1

def _PrepareSimpleTypeDefinition (std, module_context):
    std.__bindingNamespace.__simpleTypeDefinitions.append(std)
    std.__uniqueInBindingClass = basis.simpleTypeDefinition._ReservedSymbols.copy()
    ptd = std.primitiveTypeDefinition(throw_if_absent=False)
    if (ptd is not None) and ptd.hasPythonSupport():
        # Only generate enumeration constants for named simple
        # type definitions that are fundamentally xsd:string
        # values.
        if issubclass(ptd.pythonSupport(), pyxb.binding.datatypes.string):
            enum_facet = std.facets().get(pyxb.binding.facets.CF_enumeration, None)
            if (enum_facet is not None) and (std.expandedName() is not None):
                for ei in enum_facet.items():
                    assert ei.tag() is None
                    ei._setTag(utility.PrepareIdentifier(ei.unicodeValue(), std.__uniqueInBindingClass))
                    #print ' Enum %s represents %s' % (ei.tag(), ei.unicodeValue())
            #print '%s unique: %s' % (std.expandedName(), std.__uniqueInBindingClass)

def _PrepareComplexTypeDefinition (ctd, module_context):
    ctd.__bindingNamespace.__complexTypeDefinitions.append(ctd)
    #print '%s represents %s in %s' % (ctd.nameInBinding(), ctd.expandedName(), ctd.__bindingNamespace)
    if ctd._isHierarchyRoot():
        ctd.__uniqueInBindingClass = basis.complexTypeDefinition._ReservedSymbols.copy()
    else:
        ctd.__uniqueInBindingClass = ctd.baseTypeDefinition().__uniqueInBindingClass.copy()
    content_basis = None
    content_type_tag = ctd._contentTypeTag()
    if (ctd.CT_SIMPLE == content_type_tag):
        content_basis = ctd.contentType()[1]
        #template_map['simple_base_type'] = pythonLiteral(content_basis, **kw)
    elif (ctd.CT_MIXED == content_type_tag):
        content_basis = ctd.contentType()[1]
    elif (ctd.CT_ELEMENT_ONLY == content_type_tag):
        content_basis = ctd.contentType()[1]
    kw = { 'binding_target_namespace' : ctd.__bindingNamespace
         , 'binding_schema' : ctd._schema() }
    if isinstance(content_basis, xs.structures.Particle):
        plurality_map = content_basis.pluralityData().nameBasedPlurality()
    else:
        plurality_map = {}
    for cd in ctd.localScopedDeclarations():
        use_map = _SetNameWithAccessors(cd, ctd, plurality_map.get(cd.expandedName(), (False, None))[0], kw)
        cd.__useMap = use_map
        #print '  %s %s uses %s stored in %s' % (cd.__class__.__name__, cd.expandedName(), use_map['id'], use_map['key'])


def _SetNameWithAccessors (component, container, is_plural, kw):
    use_map = { }
    class_unique = container.__uniqueInBindingClass
    assert isinstance(component, xs.structures._ScopedDeclaration_mixin)
    unique_name = utility.PrepareIdentifier(component.expandedName().localName(), class_unique)
    use_map['id'] = unique_name
    use_map['inspector'] = unique_name
    use_map['mutator'] = utility.PrepareIdentifier('set' + unique_name[0].upper() + unique_name[1:], class_unique)
    use_map['use'] = utility.MakeUnique('__' + unique_name.strip('_'), class_unique)
    assert component._scope() == container
    assert component.nameInBinding() is None, 'Use %s but binding name %s for %s' % (use_map['use'], component.nameInBinding(), component.expandedName())
    component.setNameInBinding(use_map['use'])
    key_name = '%s_%s_%s' % (str(container.__bindingNamespace), container.nameInBinding(), component.expandedName())
    use_map['key'] = utility.PrepareIdentifier(key_name, class_unique, private=True)
    use_map['name'] = str(component.expandedName())
    use_map['name_expr'] = pythonLiteral(component.expandedName(), **kw)
    if isinstance(component, xs.structures.ElementDeclaration) and is_plural:
        use_map['appender'] = utility.PrepareIdentifier('add' + unique_name[0].upper() + unique_name[1:], class_unique)
    return use_map

def CheckDependencies (namespace):
    ns_graph = utility.Graph()
    ns_set = set([namespace])
    while ns_set:
        ns = ns_set.pop()
        for rns in ns.referencedNamespaces():
            if not (rns in ns_graph.nodes()):
                ns_set.add(rns)
                ns_graph.addNode(rns)
            ns_graph.addEdge(ns, rns)

    ns_graph.setRoot(namespace)
    scc_order = ns_graph.sccOrder()
    namespace.__namespaceOrder = scc_order
    namespace.__namespaceSet = ns_graph.nodes()
    print "Namespace ordering:"
    for scc in scc_order:
        elts = []
        nsg_head = scc[0]
        for ns in scc:
            ns.__namespaceGroupHead = scc[0]
            ns.__namespaceGroupMulti = (1 < len(scc))
            ns.__schemasForEmit = None
            elts.append(str(ns))
        nsg_head.__schemasForEmit = set()
        print 'SCC: %s' % ("\n  ".join(elts))

    schema_ii_graph = utility.Graph()
    schemas = set()
    for sch in namespace.schemas():
        if sch.schemaLocation() is not None:
            schemas.add(sch)
    while schemas:
        schema = schemas.pop()
        assert schema is not None
        assert schema.schemaLocation() is not None
        for sch in schema.includedSchema().union(schema.importedSchema()):
            assert sch is not None, '%s imports none?' % (schema.schemaLocation(),)
            if not ((sch.schemaLocation() is None) or (sch in schema_ii_graph.nodes())):
                schemas.add(sch)
                schema_ii_graph.addNode(sch)
            if sch in schema.includedSchema():
                schema_ii_graph.addEdge(schema, sch)

    schema = iter(namespace.schemas()).next()
    schema_ii_graph.setRoot(schema)
    scc_order = schema_ii_graph.sccOrder()
    namespace.__schemaOrder = scc_order
    namespace.__schemaSet = schema_ii_graph.nodes()
    print "Schema ordering:"
    for scc in scc_order:
        elts = []
        for s in scc:
            if s.schemaLocation() is None:
                print 'No schema location in %s' % (s.targetNamespace(),)
            elts.append(str(s.schemaLocation()))
            s.__schemaGroupHead = scc[0]
            s.__schemaGroupMulti = (1 < len(scc))
            s.__modulePath = None
            s.__requiredSchema = set()
            s.__requiredNamespaces = set()
        print 'SCC: %s' % ("\n  ".join(elts))


class BindingModuleIO (StringIO.StringIO):
    __prolog = None
    __postscript = None
    __namespace = None
    __schema = None

    def __init__ (self, namespace, schema=None, module_path=None):
        super(BindingModuleIO, self).__init__(self)
        self.__namespace = namespace
        self.__schema = schema
        self.__prolog = []
        self.__postscript = []

    def prolog (self):
        return self.__prolog
    def postscript (self):
        return self.__postscript
    def namespace (self):
        return self.__namespace
    def schema (self):
        return self.__schema

class _ModuleNaming_mixin (object):
    __anonSTDIndex = None
    __anonCTDIndex = None
    __uniqueInModule = None

    def __init__ (self, *args, **kw):
        super(_ModuleNaming_mixin, self).__init__(*args, **kw)
        self.__anonSTDIndex = 1
        self.__anonCTDIndex = 1
        self.__components = []
        self.__componentNameMap = {}
        self.__uniqueInModule = set()

    def modulePath (self):
        return self.__modulePath
    def _setModulePath (self, module_path):
        self.__modulePath = module_path
    __modulePath = None

    def _initializeUniqueInModule (self, unique_in_module):
        self.__uniqueInModule = set(unique_in_module)

    def uniqueInModule (self):
        return self.__uniqueInModule

    def _bindComponentInModule (self, component):
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
        self.__components.append(component)
        self.__componentNameMap[component] = rv
        return rv

    def nameInModule (self, component):
        return self.__componentNameMap.get(component)

class NamespaceModule (_ModuleNaming_mixin):
    """This class represents a Python module that holds all the
    declarations belonging to a specific namespace."""

    def namespace (self):
        return self.__namespace
    __namespace = None

    __modulePrefix = None

    def namespaceGroupModule (self):
        return self.__namespaceGroupModule
    def setNamespaceGroupModule (self, namespace_group_module):
        self.__namespaceGroupModule = namespace_group_module
    __namespaceGroupModule = None

    _UniqueInModule = set([ 'pyxb', 'sys', 'Namespace', 'CreateFromDOM' ])

    def __init__ (self, namespace, module_prefix):
        super(NamespaceModule, self).__init__(self)
        self.__namespace = namespace
        self.__modulePrefix = module_prefix[:]
        self.__namespaceBindingNames = {}
        self.__components = []
        self.__componentBindingName = {}
        self._initializeUniqueInModule(self._UniqueInModule)

    def setBaseModule (self, base_module):
        assert base_module is not None
        self._setModulePath('.'.join(self.__modulePrefix + [ base_module ]))
        self.__namespace.setModulePath(self.modulePath())

    def setSchemaGroupPrefix (self, schema_group_prefix):
        self.__schemaGroupPrefix = schema_group_prefix[:]
        self.__uniqueInSchemaGroup = set()
    __schemaGroupPrefix = None
    __uniqueInSchemaGroup = None
    
    def schemaGroupModulePath (self, schema_group_module):
        module_base = utility.MakeUnique('_'.join([ _s.schemaLocationTag() for _s in schema_group_module.schemaGroup() ]), self.__uniqueInSchemaGroup)
        return '.'.join(self.__schemaGroupPrefix + [ module_base ])

    __components = None
    __componentBindingName = None

    def bindComponentInModule (self, component, schema_group_module):
        ns_name = self._bindComponentInModule(component)
        print '%s NS %s' % (component.expandedName(), ns_name)

        binding_context = self
        if schema_group_module is not None:
            binding_context = schema_group_module.bindComponentInModule(component)
        if self.__namespaceGroupModule:
            self.__namespaceGroupModule.bindComponentInModule(component)

        component.setNameInBinding(binding_context.nameInModule(component))
        return binding_context

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

    def __init__ (self, namespace_modules, module_prefix):
        super(NamespaceGroupModule, self).__init__(self)
        assert 1 < len(namespace_modules)
        self.__namespaceModules = namespace_modules

        module_prefix = module_prefix[:]
        module_prefix.append(self._GroupPrefix)
        self._setModulePath('.'.join(module_prefix + [ utility.MakeUnique('_'.join([ _nsm.namespace().prefix() for _nsm in namespace_modules]), self.__UniqueInGroups) ]))
        for nsm in namespace_modules:
            nsm.setSchemaGroupPrefix(module_prefix + [ utility.MakeUnique('_%s' % (nsm.namespace().prefix(),), self.__UniqueInGroups) ])
        self._initializeUniqueInModule(self._UniqueInModule)

    def bindComponentInModule (self, component):
        ngm_name = self._bindComponentInModule(component)
        print '%s NGM %s' % (component.expandedName(), ngm_name)
        return self
            
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

    _UniqueInModule = set([ 'pyxb', 'sys', 'Namespace' ])
    
    def __init__ (self, namespace_module, schema_group):
        super(SchemaGroupModule, self).__init__(self)
        self.__namespaceModule = namespace_module
        self.__schemaGroup = schema_group
        assert isinstance(self.__schemaGroup, list)
        self._setModulePath(self.__namespaceModule.schemaGroupModulePath(self))
        self._initializeUniqueInModule(self._UniqueInModule)

    def bindComponentInModule (self, component):
        sgm_name = self._bindComponentInModule(component)
        print '%s SGM %s' % (component.expandedName(), sgm_name)
        return self

def AltGenerate(schema_location=None,
                namespace=None,
                module_path_prefix=''):
    global UniqueInBinding
    global PostscriptItems
    UniqueInBinding.clear()
    PostscriptItems = []

    if namespace is None:
        if schema_location is None:
            raise Exception('No input provided')
        schema = xs.schema.CreateFromLocation(schema_location)
        namespace = schema.targetNamespace()

    _ResolveReferencedNamespaces(namespace)

    CheckDependencies(namespace)

    used_modules = {}
    all_std = set()
    all_ctd = set()
    all_ed = set()
    for sns in namespace.siblingNamespaces():
        _PrepareNamespaceForGeneration(sns, module_path_prefix, all_std, all_ctd, all_ed)
    all_components = all_std.union(all_ctd).union(all_ed)

    component_graph = utility.Graph()
    for c in all_components:
        component_graph.addNode(c)
        deps = c.dependentComponents()
        for target in deps:
            if target in all_components:
                component_graph.addEdge(c, target)

    component_schemas = set()
    for c in component_graph.nodes():
        assert c._schema() is not None
        component_schemas.add(c._schema().__schemaGroupHead)
        c.__bindingNamespace.__namespaceGroupHead.__schemasForEmit.add(c._schema())

    component_order = [ _scc[0] for _scc in component_graph.sccOrder() ]
    assert len(component_order) == len(component_graph.nodes())

    binding_module_prefix = ['binding']
    namespace_module_map = {}
    unique_in_bindings = set([NamespaceGroupModule._GroupPrefix])
    for ns_scc in namespace.__namespaceOrder:
        namespace_modules = []
        for ns in ns_scc:
            nsm = NamespaceModule(ns, binding_module_prefix)
            namespace_module_map[ns] = nsm
            ns.__namespaceModule = nsm
            assert ns == nsm.namespace()
            if not ns.isBuiltinNamespace():
                assert nsm.namespace().prefix() is not None, 'No prefix for %s' % (ns,)
                nsm.setBaseModule(utility.MakeUnique(nsm.namespace().prefix(), unique_in_bindings))
                print '%s stores in %s' % (ns, nsm.modulePath())
            namespace_modules.append(nsm)

        nsg_head = ns_scc[0].__namespaceGroupHead
        if nsg_head.__namespaceGroupMulti:
            ngm = NamespaceGroupModule(namespace_modules, binding_module_prefix)
            [ _nsm.setNamespaceGroupModule(ngm) for _nsm in namespace_modules ]
            assert namespace_module_map[nsg_head].namespaceGroupModule() == ngm
            print 'Group headed by %s stores in %s' % (nsg_head, ngm.modulePath())
    for sc_scc in namespace.__schemaOrder:
        scg_head = sc_scc[0].__schemaGroupHead
        nsm = scg_head.targetNamespace().__namespaceModule
        sgm = None
        if nsm.namespaceGroupModule() is not None:
            sgm = SchemaGroupModule(nsm, sc_scc)
            print 'Schema group stores in %s: %s' % (sgm.modulePath(), ' '.join([ _s.schemaLocationTag() for _s in sc_scc]))
        for sc in sc_scc:
            sc.__schemaGroupModule = sgm

    type_defs = []
    for c in component_order:
        if isinstance(c, xs.structures.ElementDeclaration) and c._scopeIsGlobal():
            nsm = namespace_module_map[c.__bindingNamespace]
            nsm.bindComponentInModule(c, c._schema().__schemaGroupModule)
            c.__bindingNamespace.__elementDeclarations.append(c)
        else:
            type_defs.append(c)

    for td in type_defs:
        nsm = namespace_module_map.get(td.__bindingNamespace, None)
        assert nsm is not None, 'No namespace module for %s type %s scope %s namespace %s' % (td.expandedName(), type(td), td._scope(), td.__bindingNamespace)
        module_context = nsm.bindComponentInModule(td, td._schema().__schemaGroupModule)
        if isinstance(td, xs.structures.SimpleTypeDefinition):
            _PrepareSimpleTypeDefinition(td, module_context)
        elif isinstance(td, xs.structures.ComplexTypeDefinition):
            _PrepareComplexTypeDefinition(td, module_context)
        else:
            assert False, 'Unexpected component type %s' % (type(td),)

    assert False

    # If the namespace is not a multi, it gets a binding, and all schemas in it get the same binding.
    # If the namespace is a multi, it gets a binding, and all schema groups in it get their own bindings

    for sns in namespace.siblingNamespaces():
        generator_kw = { }
        generator_kw['binding_target_namespace'] = sns
        assert sns.__schemaHaveModules is not None
        ns_outf = StringIO.StringIO()

        import_prefix = 'pyxb.xmlschema.'
        if sns == pyxb.namespace.XMLSchema:
            import_prefix = ''

        template_map = { }
        template_map['input'] = sns.schemaLocation()
        template_map['date'] = str(datetime.datetime.now())
        template_map['version'] = pyxb.__version__
        template_map['targetNamespace'] = repr(sns.uri(),)
        template_map['import_prefix'] = import_prefix
        if sns.isAbsentNamespace():
            template_map['NamespaceDefinition'] = 'pyxb.namespace.CreateAbsentNamespace()'
        else:
            template_map['NamespaceDefinition'] = templates.replaceInText('pyxb.namespace.NamespaceForURI(%{targetNamespace}, create_if_missing=True)', **template_map)

        import_namespaces = []
        for ins in sns.referencedNamespaces():
            if ins == sns:
                continue
            if ins.modulePath() is None:
                if not ins.isBuiltinNamespace():
                    print 'WARNING: Dependency on %s with no module path' % (ins.uri(),)
                continue
            if not (sns.__schemaHaveModules and (ins in sns.siblingNamespaces()) and ins.__schemaHaveModules):
                import_namespaces.append('import %s # ref namespace' % (ins.modulePath(),))

        if sns.__schemaHaveModules:
            assert not sns.isAbsentNamespace()
            print 'WARNING: Using multiple schema for output for %s' % (sns,)
            
            module_imports = []
            ns_module_imports = []
            for schema in sns.__schemaOrder:
                module_imports.append('from %s import * # schema module' % (schema.__modulePath,))
                schema.__outputFile = StringIO.StringIO()
                imports = []
                for dep_schema in schema_graph.edgeMap().get(schema, []):
                    if dep_schema == schema:
                        continue
                    imports.append('import %s # schema' % (dep_schema.__modulePath,))
                imports.extend(import_namespaces)
                template_map['aux_imports'] = "\n".join(imports)
                schema.__outputFile.write(templates.replaceInText('''# PyWXSB bindings for schema %{schema_location}

# Generated %{date} by PyWXSB version %{version}
import pyxb.binding
import pyxb.exceptions_
import sys

# Import bindings for namespaces imported into schema
%{aux_imports}

# Make sure there's a registered Namespace instance, and that it knows
# about this module.
Namespace = %{NamespaceDefinition}
Namespace._setModule(sys.modules[__name__])
Namespace.configureCategories(['typeBinding', 'elementBinding'])
''', schema_location=schema.schemaLocation(), **template_map))
            import_namespaces.extend(module_imports)
        # "import" in import_namespaces means Python import, not XSD import
        template_map['aux_imports'] = "\n".join(import_namespaces)

        ns_outf.write(templates.replaceInText('''# PyWXSB bindings for %{input}
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
        #print 'Generating %d STDs' % (len(sns.__simpleTypeDefinitions),)
        for std in sns.__simpleTypeDefinitions:
            if sns.__schemaHaveModules:
                outf = std._schema().__outputFile
            else:
                outf = ns_outf
            outf.write(GenerateSTD(std, binding_schema=std._schema(), **generator_kw))
        #print 'Generating %d CTDs' % (len(sns.__complexTypeDefinitions),)
        for ctd in sns.__complexTypeDefinitions:
            if sns.__schemaHaveModules:
                outf = ctd._schema().__outputFile
            else:
                outf = ns_outf
            outf.write(GenerateCTD(ctd, binding_schema=ctd._schema(), **generator_kw))
        #print 'Generating %d ED' % (len(sns.__elementDeclarations),)
        for ed in sns.__elementDeclarations:
            if sns.__schemaHaveModules:
                outf = ed._schema().__outputFile
            else:
                outf = ns_outf
            outf.write(GenerateED(ed, binding_schema=ed._schema(), **generator_kw))

        ns_outf.write(''.join(PostscriptItems))
        sns.__bindingSource = ns_outf.getvalue()

    return namespace

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


def GeneratePython (**kw):
    """
    @keyword namespace: The namespace for which bindings should be generated
    @keyword schema_location: If namespace is C{None}, the location where a schema defining the namespace can be found
    @keyword generate_facets: Utility generating only the facet definitions for the XMLSchema namespace
    """

    ns = AltGenerate(**kw)
    return ns.__bindingSource
