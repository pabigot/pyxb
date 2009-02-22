"""Classes corresponding to W3C XML Schema components.

Class names and behavior should conform to the schema components
described in http://www.w3.org/TR/xmlschema-1/.

Each class has a CreateFromDOM class method that creates an instance
and initializes it from a DOM node.

"""

from PyWXSB.exceptions_ import *
from xml.dom import Node
import types
import PyWXSB.Namespace as Namespace
import datatypes
import facets
import PyWXSB.templates as templates

def LocateUniqueChild (node, schema, tag, absent_ok=True):
    """Locate a unique child of the DOM node.

    The node should be a xml.dom.Node ELEMENT_NODE instance.  The
    schema from which the node derives is also provided.  tag is the
    NCName of an XMLSchema element.  This function returns the sole
    child of node which is an ELEMENT_NODE instance and has a tag
    consistent with the given tag.  If multiple nodes with a matching
    tag are found, or abesnt_ok is False and no matching tag is found,
    an exception is raised.

    @throw SchemaValidationError if multiple elements are identified
    @throw SchemaValidationError if absent_ok is False and no element is identified.
    """
    candidate = None
    # @todo identify QName children as well as NCName
    names = schema.xsQualifiedNames(tag)
    for cn in node.childNodes:
        if (Node.ELEMENT_NODE == cn.nodeType) and (cn.nodeName in names):
            if candidate:
                raise SchemaValidationError('Multiple %s elements nested in %s' % (name, node.nodeName))
            candidate = cn
    if (candidate is None) and not absent_ok:
        raise SchemaValidationError('Expected %s elements nested in %s' % (name, node.nodeName))
    return candidate

def NodeAttribute (node, schema, attribute_ncname, attribute_ns=Namespace.XMLSchema):
    """Look up an attribute in a node.

    NEVER EVER use node.hasAttribute or node.getAttribute directly.
    The attribute tag can often be in multiple forms.

    This gets tricky because the attribute tag may or may not be
    qualified with a namespace.  The qualifier may be elided if the
    containing element is in the attribute's namespace, even if that
    is not the default namespace for the schema.

    Return the requested attribute, or None if the attribute is not
    present in the node.

    An example of where this is necessary is the attribute declaration
    for "lang" in http://www.w3.org/XML/1998/namespace, The simpleType
    includes a union clause whose memberTypes attribute is
    unqualified, and XMLSchema is not the default namespace."""
    assert node.namespaceURI is not None
    container_ns = schema.namespaceForURI(node.namespaceURI)
    assert container_ns is not None
    assert attribute_ns is not None
    candidate_names = schema.qualifiedNames(attribute_ncname, attribute_ns)
    if (attribute_ns == container_ns) and not (attribute_ncname in candidate_names):
        candidate_names = candidate_names + (attribute_ncname,)
    attr_value = None
    match_name = None
    for attr_name in candidate_names:
        if node.hasAttribute(attr_name):
            if attr_value is not None:
                raise SchemaValidationError('Multiple instances of attribute %s from %s' % (attribute_ncname, attribute_ns.uri()))
            attr_value = node.getAttribute(attr_name)
    return attr_value

def LocateMatchingChildren (node, schema, tag):
    """Locate all children of the DOM node that have a particular tag.

    The node should be a xml.dom.Node ELEMENT_NODE instance.  The
    schema from which the node derives is also provided.  tag is the
    NCName of an XMLSchema element.  This function returns a list of
    children of node which are an ELEMENT_NODE instances and have a tag
    consistent with the given tag.
    """
    matches = []
    names = schema.xsQualifiedNames(tag)
    for cn in node.childNodes:
        if (Node.ELEMENT_NODE == cn.nodeType) and (cn.nodeName in names):
            matches.append(cn)
    return matches

def LocateFirstChildElement (node, absent_ok=True, require_unique=False):
    """Locate the first element child of the node.

    If absent_ok is True, and there are no ELEMENT_NODE children, None
    is returned.  If require_unique is True and there is more than one
    ELEMENT_NODE child, an exception is rasied.
    """
    
    candidate = None
    for cn in node.childNodes:
        if Node.ELEMENT_NODE == cn.nodeType:
            if require_unique:
                if candidate:
                    raise SchemaValidationError('Multiple elements nested in %s' % (node.nodeName,))
                candidate = cn
            else:
                return cn
    if (candidate is None) and not absent_ok:
        raise SchemaValidationError('No elements nested in %s' % (node.nodeName,))
    return candidate

def HasNonAnnotationChild (wxs, node):
    """Return True iff node has an ELEMENT_NODE child that is not an
    XMLSchema annotation node."""
    xs_annotation = wxs.xsQualifiedNames('annotation')
    for cn in node.childNodes:
        if Node.ELEMENT_NODE != cn.nodeType:
            continue
        if cn.nodeName not in xs_annotation:
            return True
    return False

class _Singleton_mixin (object):
    """This class is a mix-in which guarantees that only one instance
    of the class will be created.  It is used to ensure that the
    ur-type instances are pointer-equivalent even when unpickling.
    See ComplexTypeDefinition.UrTypeDefinition()."""
    def __new__ (cls, *args, **kw):
        singleton_property = '_%s__singleton' % (cls.__name__,)
        if not (singleton_property in cls.__dict__):
            setattr(cls, singleton_property, object.__new__(cls, *args, **kw))
        return cls.__dict__[singleton_property]

class _Annotated_mixin (object):
    """Mix-in that supports an optional single annotation that describes the component.

    Most schema components have annotations.  The ones that don't are
    AttributeUse, Particle, and Annotation.  ComplexTypeDefinition and
    Schema support multiple annotations, so do not mix-in this class."""

    # Optional Annotation instance
    __annotation = None

    def __init__ (self, *args, **kw):
        super(_Annotated_mixin, self).__init__(*args, **kw)
        self.__annotation = kw.get('annotation', None)

    def _annotationFromDOM (self, wxs, node):
        cn = LocateUniqueChild(node, wxs, 'annotation')
        if cn is not None:
            self.__annotation = Annotation.CreateFromDOM(wxs, cn)

    def _setFromInstance (self, other):
        try:
            super(_Annotated_mixin, self)._setFromInstance(other)
        except AttributeError, e:
            pass
        # @todo make this a copy?
        self.__annotation = other.__annotation

    def annotation (self):
        return self.__annotation

class _NamedComponent_mixin (object):
    """Mix-in to hold the name and target namespace of a component.

    The name may be None, indicating an anonymous component."""
    # Value of the component.  None if the component is anonymous.
    __name = None

    # None, or a reference to a Namespace in which the component may be found
    __targetNamespace = None
    
    # The schema in which qualified names for the namespace should be
    # determined.
    __schema = None

    def __init__ (self, *args, **kw):
        assert 0 == len(args)
        super(_NamedComponent_mixin, self).__init__(*args, **kw)
        name = kw.get('name', None)
        target_namespace = kw.get('target_namespace', None)
        assert (name is None) or (0 > name.find(':'))
        self.__name = name
        if target_namespace is not None:
            self.__targetNamespace = target_namespace
        self.__schema = None
            
    def targetNamespace (self):
        """Return the namespace in which the component is located."""
        return self.__targetNamespace

    def ncName (self):
        """Return the local name of the component."""
        return self.__name

    def name (self):
        """Return the QName of the component."""
        if self.__targetNamespace is not None:
            if self.__name is not None:
                return '%s[%s]' % (self.__name, self.__targetNamespace.uri())
            return '#??[%s]' % (self.__targetNamespace.uri(),)
        return self.__name

    def isNameEquivalent (self, other):
        """Return true iff this and the other component share the same name and target namespace.
        
        Anonymous components are inherently name inequivalent."""
        # Note that unpickled objects 
        return (self.__name is not None) and (self.__name == other.__name) and (self.__targetNamespace == other.__targetNamespace)

    __IGNORE = '''
    def __getstate__ (self):
        pickling_namespace = Namespace.Namespace.PicklingNamespace()
        assert pickling_namespace is not None
        if self.targetNamespace() is None:
            print '@@@ Pickling non-associated name %s type %s' % (self.name(), self)
            return self.__dict__
        if pickling_namespace != self.targetNamespace():
            if self.ncName() is None:
                raise LogicError('Unable to pickle reference to %s: %s' % (self.name(), self))
            print '@@@ Pickling reference to %s' % (self.name(),)
            return ( self.targetNamespace().uri(), self.ncName() )
        print '@@@ Pickling value of %s' % (self.name(),)
        return self.__dict__

    def __setstate__ (self, state):
        if isinstance(state, tuple):
            ( ns_uri, nc_name ) = state
            print '@@@ Need reference to %s[%s]' % (nc_name, ns_uri)
            return
        self.__dict__.update(state)
    '''

class _Resolvable_mixin (object):
    """Mix-in indicating that this component may have references to unseen named components."""
    def isResolved (self):
        """Determine whether this named component is resolved.

        Override this in the child class."""
        raise LogicError('Resolved check not implemented in %s' % (self.__class__,))
    
    def _resolve (self, wxs):
        """Perform whatever steps are required to resolve this component.

        Resolution is performed in the context of the provided schema.
        Invoking this method may fail to complete the resolution
        process if the component itself depends on unresolved
        components.  The sole caller of this should be
        schema._resolveDefinitions().
        
        Override this in the child class.  In the prefix, if
        isResolved() is true, return right away.  If something
        prevents you from completing resolution, invoke
        wxs._queueForResolution(self) so it is retried later, then
        immediately return self.  Prior to leaving after successful
        resolution discard any cached dom node by setting
        self.__domNode=None.

        The method should return self, whether or not resolution
        succeeds.
        """
        raise LogicError('Resolution not implemented in %s' % (self.__class__,))

class _ValueConstraint_mixin:
    """Mix-in indicating that the component contains a simple-type
    value that may be constrained."""
    
    VC_na = 0                   #<<< No value constraint applies
    VC_default = 1              #<<< Provided value constraint is default value
    VC_fixed = 2                #<<< Provided value constraint is fixed value

    # None, or a tuple containing a string followed by one of the VC_*
    # values above.
    __valueConstraint = None
    def valueConstraint (self):
        """A constraint on the value of the attribute or element.

        Either None, or a pair consisting of a string in the lexical
        space of the typeDefinition and one of VC_default and
        VC_fixed."""
        return self.__valueConstraint

    def _valueConstraintFromDOM (self, wxs, node):
        aval = NodeAttribute(node, wxs, 'default')
        if aval is not None:
            self.__valueConstraint = (aval, self.VC_default)
            return self
        aval = NodeAttribute(node, wxs, 'fixed')
        if aval is not None:
            self.__valueConstraint = (aval, self.VC_fixed)
            return self
        self.__valueConstraint = None
        return self
        

class AttributeDeclaration (_NamedComponent_mixin, _Resolvable_mixin, _Annotated_mixin, _ValueConstraint_mixin):
    """An XMLSchema Attribute Declaration component.

    See http://www.w3.org/TR/xmlschema-1/index.html#cAttribute_Declarations
    """
    # 
    __typeDefinition = None
    def typeDefinition (self):
        """The simple type definition to which an attribute value must
         conform."""
        return self.__typeDefinition

    SCOPE_global = 'global'     #<<< Marker to indicate global scope
    xSCOPE_unhandled = 'unhandled' #<<< Marker to indicate scope has not been defined

    __scope = None
    def scope (self):
        """The scope to which the declaration applies.
        
        None, the string "global", or a reference to a _ComplexTypeDefinition.
        """
        return self.__scope

    def __str__ (self):
        return '%s{%s}' % (self.name(), self.typeDefinition())

    @classmethod
    def CreateBaseInstance (cls, name, target_namespace=None):
        """Create an attribute declaration component for a specified namespace."""
        bi = cls(name=name, target_namespace=target_namespace)
        return bi

    @classmethod
    def CreateFromDOM (cls, wxs, node):
        # Node should be an XMLSchema attribute node
        assert node.nodeName in wxs.xsQualifiedNames('attribute')

        name = NodeAttribute(node, wxs, 'name')
        if name is not None:
            namespace = wxs.getTargetNamespace()
        #elif node.hasAttribute('ref'):
        #    pass
        elif NodeAttribute(node, wxs, 'ref') is None:
            namespace = wxs.getTargetNamespaceFromDOM(node, 'attributeFormDefault')

        rv = cls(name=name, namespace=namespace)
        rv._annotationFromDOM(wxs, node)
        rv._valueConstraintFromDOM(wxs, node)
        rv.__domNode = node
        wxs._queueForResolution(rv)
        return rv

    def isResolved (self):
        return self.__typeDefinition is not None

    def _resolve (self, wxs):
        if self.isResolved():
            return self
        #print 'Resolving AD %s' % (self.name(),)
        node = self.__domNode

        # Implement per section 3.2.2
        if node.parentNode.nodeName in wxs.xsQualifiedNames('schema'):
            self.__scope = self.SCOPE_global
        elif NodeAttribute(node, wxs, 'ref') is None:
            # The AttributeUse component is resolved elsewhere
            # @todo Set scope to enclosing complexType, if present
            self.__scope = self.xSCOPE_unhandled
        else:
            # I think this is really a schema validation error
            raise IncompleteImplementationError('Internal attribute declaration by reference')
        
        st_node = LocateUniqueChild(node, wxs, 'simpleType')
        type_attr = NodeAttribute(node, wxs, 'type')
        if st_node is not None:
            self.__typeDefinition = SimpleTypeDefinition.CreateFromDOM(wxs, st_node)
            print '!! Attr decl %s created type definition %s' % (self.name(), self.__typeDefinition)
        elif type_attr is not None:
            # Although the type definition may not be resolved, *this* component
            # is resolved, since we don't look into the type definition for anything.
            self.__typeDefinition = wxs.lookupSimpleType(type_attr)
        else:
            self.__typeDefinition = SimpleTypeDefinition.SimpleUrTypeDefinition()
                
        self.__domNode = None
        return self


class AttributeUse (_Resolvable_mixin, _ValueConstraint_mixin):
    """An XMLSchema Attribute Use component.

    See http://www.w3.org/TR/xmlschema-1/index.html#cAttribute_Use
    """

    # How this attribute can be used.  The component property
    # "required" is true iff the value is USE_required.
    USE_required = 0x01
    USE_optional = 0x02
    USE_prohibited = 0x04
    __use = False
    def required (self): return self.USE_required == self.__use
    def prohibited (self): return self.USE_prohibited == self.__use

    # A reference to an AttributeDeclaration
    __attributeDeclaration = None
    def attributeDeclaration (self): return self.__attributeDeclaration

    @classmethod
    def CreateFromDOM (cls, wxs, node):
        assert node.nodeName in wxs.xsQualifiedNames('attribute')
        rv = cls()
        rv.__use = cls.USE_optional
        use = NodeAttribute(node, wxs, 'use')
        if use is not None:
            if 'required' == use:
                rv.__use = cls.USE_required
            elif 'optional' == use:
                rv.__use = cls.USE_optional
            elif 'prohibited' == use:
                rv.__use = cls.USE_prohibited
            else:
                raise SchemaValidationError('Unexpected value %s for attribute use attribute' % (use,))

        rv._valueConstraintFromDOM(wxs, node)
        
        if NodeAttribute(node, wxs, 'ref') is None:
            # Create an anonymous declaration, which will be resolved
            # separately
            rv.__attributeDeclaration = AttributeDeclaration.CreateFromDOM(wxs, node)
        else:
            rv.__domNode = node
            wxs._queueForResolution(rv)
        return rv

    def isResolved (self):
        return self.__attributeDeclaration is not None

    def _resolve (self, wxs):
        if self.isResolved():
            return self
        assert self.__domNode
        node = self.__domNode
        ref_attr = NodeAttribute(node, wxs, 'ref')
        if ref_attr is None:
            raise SchemaValidationError('Attribute uses require reference to attribute declaration')
        # Although the attribute declaration definition may not be
        # resolved, *this* component is resolved, since we don't look
        # into the attribute declaration for anything.
        self.__attributeDeclaration = wxs.lookupAttribute(ref_attr)
        self.__domNode = None
        return self

class ElementDeclaration (_NamedComponent_mixin, _Resolvable_mixin, _Annotated_mixin, _ValueConstraint_mixin):
    """An XMLSchema Element Declaration component.

    See http://www.w3.org/TR/xmlschema-1/index.html#cElement_Declarations
    """

    # Simple or complex type definition
    __typeDefinition = None
    def typeDefinition (self):
        """The simple or complex type to which the element value conforms."""
        return self.__typeDefinition

    SCOPE_global = 0x01         #<<< Marker for global scope

    __scope = None
    def scope (self):
        """The scope for the element.
        Valid values are SCOPE_global, or a complex type definition.

        @todo For declarations in named model groups (viz., local
        elements that aren't references), the scope needs to be set by
        the owning complex type.
        """
        return self.__scope

    __nillable = False
    def nillable (self): return self.__nillable

    __identityConstraintDefinitions = None
    def identityConstraintDefinitions (self):
        """A list of IdentityConstraintDefinition instances."""
        return self.__identityConstraintDefinitions

    __substitutionGroupAffiliation = None
    def substitutionGroupAffiliation (self):
        """None, or a reference to an ElementDeclaration."""
        return self.__substitutionGroupAffiliation

    SGE_none = 0
    SGE_extension = 0x01
    SGE_restriction = 0x02
    SGE_substitution = 0x04

    # Subset of SGE marks formed by bitmask.  SGE_substitution is disallowed.
    __substitutionGroupExclusions = SGE_none

    # Subset of SGE marks formed by bitmask
    __disallowedSubstitutions = SGE_none

    __abstract = False
    def abstract (self): return self.__abstract

    __ancestorComponent = None
    def ancestorComponent (self):
        """The containing component which will ultimately provide the
        scope.

        None if at the top level, or a ComplexTypeDefinition or a
        ModelGroup.  """
        return self.__ancestorComponent

    def __init__ (self, *args, **kw):
        super(ElementDeclaration, self).__init__(*args, **kw)
        self.__ancestorComponent = kw.get('ancestor_component', None)

    def isPlural (self):
        return False

    @classmethod
    def CreateFromDOM (cls, wxs, node, ancestor_component=None):
        # Node should be an XMLSchema element node
        assert node.nodeName in wxs.xsQualifiedNames('element')

        # Might be top-level, might be local
        name = NodeAttribute(node, wxs, 'name')
        scope = None
        namespace = None
        if node.parentNode.nodeName in wxs.xsQualifiedNames('schema'):
            namespace = wxs.getTargetNamespace()
            scope = cls.SCOPE_global
        elif NodeAttribute(node, wxs, 'ref') is None:
            namespace = wxs.targetNamespaceFromDOM(node, 'elementFormDefault')
            if not ancestor_component:
                raise IncompleteImplementationError("Require ancestor information for local element:\n%s\n" % (node.toxml(),))
            if isinstance(ancestor_component, ComplexTypeDefinition):
                scope = ancestor_component
            else:
                # Presumably a declaration within a named model group;
                # scope is determined when it is used, but is
                # certainly not global.
                pass
        else:
            raise LogicError('Created reference as element declaration')
        
        rv = cls(name=name, namespace=namespace, ancestor_component=ancestor_component)
        rv.__scope = scope
        rv._annotationFromDOM(wxs, node)
        rv._valueConstraintFromDOM(wxs, node)

        # Creation does not attempt to do resolution.  Queue up the newly created
        # whatsis so we can resolve it after everything's been read in.
        rv.__domNode = node
        wxs._queueForResolution(rv)
        
        return rv

    def isResolved (self):
        return self.__typeDefinition is not None

    def _resolve (self, wxs):
        if self.isResolved():
            return self
        node = self.__domNode

        # NB: Scope already set

        sg_attr = NodeAttribute(node, wxs, 'substitutionGroup')
        if sg_attr is not None:
            sga = wxs.lookupElement(sg_attr)
            if not sga.isResolved():
                wxs._queueForResolution(self)
                return self
            self.__substitutionGroupAffiliation = sga
            
        id_tags = list(wxs.xsQualifiedNames('key'))
        id_tags.extend(wxs.xsQualifiedNames('unique'))
        id_tags.extend(wxs.xsQualifiedNames('keyref'))
        identity_constraints = []
        for cn in node.childNodes:
            if (Node.ELEMENT_NODE == cn.nodeType) and (cn.nodeName in id_tags):
                identity_constraints.append(IdentityConstraintDefinition.CreateFromDOM(wxs, cn))
        self.__identityConstraintDefinitions = identity_constraints

        type_def = None
        td_node = LocateUniqueChild(node, wxs, 'simpleType')
        if td_node is not None:
            type_def = SimpleTypeDefinition.CreateFromDOM(wxs, node)
        else:
            td_node = LocateUniqueChild(node, wxs, 'complexType')
            if td_node is not None:
                type_def = ComplexTypeDefinition.CreateFromDOM(wxs, td_node)
        if type_def is None:
            type_attr = NodeAttribute(node, wxs, 'type')
            if type_attr is not None:
                type_def = wxs.lookupType(type_attr)
            elif self.__substitutionGroupAffiliation is not None:
                type_def = self.__substitutionGroupAffiliation.typeDefinition()
            else:
                type_def = ComplexTypeDefinition.UrTypeDefinition()
        self.__typeDefinition = type_def

        attr_val = NodeAttribute(node, wxs, 'nillable')
        if attr_val is not None:
            self.__nillable = datatypes.boolean(attr_val)

        # @todo disallowed substitutions, substitution group exclusions

        attr_val = NodeAttribute(node, wxs, 'abstract')
        if attr_val is not None:
            self.__abstract = datatypes.boolean(attr_val)
                
        self.__domNode = None
        return self

    def __str__ (self):
        return '%s[%s]' % (self.name(), self.typeDefinition().name())


class ComplexTypeDefinition (_NamedComponent_mixin, _Resolvable_mixin):
    __baseTypeDefinition = None
    def baseTypeDefinition (self):
        "The type resolved from the base attribute."""
        return self.__baseTypeDefinition

    DM_empty = 0                #<<< No derivation method specified
    DM_extension = 0x01         #<<< Derivation by extension
    DM_restriction = 0x02       #<<< Derivation by restriction

    #  This field is used to identify unresolved definitions.
    __derivationMethod = None
    def derivationMethod (self):
        """How the type was derived."""
        return self.__derivationMethod

    # Derived from the final and finalDefault attributes
    __final = DM_empty

    # Derived from the abstract attribute
    __abstract = False
    
    __attributeUses = None
    def attributeUses (self):
        """A frozenset() of AttributeUse instances."""
        return self.__attributeUses

    # Optional wildcard that constrains attributes
    __attributeWildcard = None

    CT_EMPTY = 0                #<<< No content
    CT_SIMPLE = 1               #<<< Simple (character) content
    CT_MIXED = 2                #<<< Children may be elements or other (e.g., character) content
    CT_ELEMENT_ONLY = 3         #<<< Expect only element content.

    __contentType = None
    def contentType (self):
        """Identify the sort of content in this type.

        Valid values are:
         * CT_EMPTY
         * ( CT_SIMPLE, simple_type_definition )
         * ( CT_MIXED, particle )
         * ( CT_ELEMENT_ONLY, particle )
        """
        return self.__contentType

    def contentTypeToString (self):
        if self.CT_EMPTY == self.contentType():
            return 'EMPTY'
        ( tag, particle ) = self.contentType()
        if self.CT_SIMPLE == tag:
            return 'Simple [%s]' % (particle,)
        if self.CT_MIXED == tag:
            return 'Mixed [%s]' % (particle,)
        if self.CT_ELEMENT_ONLY == tag:
            return 'Element [%s]' % (particle,)
        raise LogicError('Unhandled content type')

    # Derived from the block and blockDefault attributes
    __prohibitedSubstitutions = DM_empty

    # @todo Extracted from children of various types
    __annotations = None
    
    def __init__ (self, *args, **kw):
        super(ComplexTypeDefinition, self).__init__(*args, **kw)
        self.__derivationMethod = kw.get('derivation_method', None)

    def _setFromInstance (self, other):
        """Override fields in this instance with those from the other.

        This method is invoked only by Schema._addNamedComponent, and
        then only when a built-in type collides with a schema-defined
        type.  Material like facets is not (currently) held in the
        built-in copy, so the DOM information is copied over to the
        built-in STD, which is subsequently re-resolved.

        Returns self.
        """
        assert self.isNameEquivalent(other)

        # The other STD should be an unresolved schema-defined type.
        assert other.__derivationMethod is None
        assert other.__domNode is not None
        self.__domNode = other.__domNode

        # Mark this instance as unresolved so it is re-examined
        self.__derivationMethod = None
        return self

    __UrTypeDefinition = None
    @classmethod
    def UrTypeDefinition (cls, in_builtin_definition=False):
        """Create the ComplexTypeDefinition instance that approximates
        the ur-type.

        See section 3.4.7.
        """

        # The first time, and only the first time, this is called, a
        # namespace should be provided which is the XMLSchema
        # namespace for this run of the system.  Please, do not try to
        # allow this by clearing the type definition.
        if in_builtin_definition and (cls.__UrTypeDefinition is not None):
            raise LogicError('Multiple definitions of UrType')
        if cls.__UrTypeDefinition is None:
            # NOTE: We use a singleton subclass of this class
            bi = _UrTypeDefinition(name='anyType', target_namespace=Namespace.XMLSchema, derivation_method=cls.DM_restriction)

            # The ur-type is its own baseTypeDefinition
            bi.__baseTypeDefinition = bi

            # No constraints on attributes
            bi.__attributeWildcard = Wildcard(namespace_constraint=Wildcard.NC_any, process_contents=Wildcard.PC_lax)

            # Content is mixed, with elements completely unconstrained.
            w = Wildcard(namespace_constraint=Wildcard.NC_any, process_contents=Wildcard.PC_lax)
            p = Particle(term=bi.__attributeWildcard, min_occurs=0, max_occurs=None)
            m = ModelGroup(compositor=ModelGroup.C_SEQUENCE, particles=[ p ])
            bi.__contentType = ( m, cls.CT_MIXED )

            # No attribute uses
            bi.__attributeUses = set()

            # No constraints on extension or substitution
            bi.__final = cls.DM_empty
            bi.__prohibitedSubstitutions = cls.DM_empty

            bi.__abstract = False

            # The ur-type is always resolved
            cls.__UrTypeDefinition = bi
        return cls.__UrTypeDefinition

    @classmethod
    def CreateFromDOM (cls, wxs, node):
        # Node should be an XMLSchema complexType node
        assert node.nodeName in wxs.xsQualifiedNames('complexType')

        name = NodeAttribute(node, wxs, 'name')

        rv = cls(name=name, target_namespace=wxs.getTargetNamespace(), derivation_method=None)

        # Creation does not attempt to do resolution.  Queue up the newly created
        # whatsis so we can resolve it after everything's been read in.
        rv.__domNode = node
        wxs._queueForResolution(rv)
        
        return rv

    # Handle attributeUses, attributeWildcard, contentType
    def __completeProcessing (self, wxs, definition_node_list, method, content_style):
        uses_c1 = set()
        uses_c2 = set()
        uses_c3 = set()
        xs_attribute = wxs.xsQualifiedNames('attribute')
        xs_attributeGroup = wxs.xsQualifiedNames('attributeGroup')
        # Handle clauses 1 and 2
        for node in definition_node_list:
            if Node.ELEMENT_NODE != node.nodeType:
                continue
            if node.nodeName in xs_attribute:
                # Note: This attribute use instance may have use=prohibited
                uses_c1.add(AttributeUse.CreateFromDOM(wxs, node))
            elif node.nodeName in xs_attributeGroup:
                # This must be an attributeGroupRef
                ref_attr =NodeAttribute(node, wxs, 'ref')
                if ref_attr is None:
                    raise SchemaValidationError('Require ref attribute on internal attributeGroup elements')
                agd = wxs.lookupAttributeGroup(ref_attr)
                if not agd.isResolved():
                    print 'Holding off resolution of attribute gruop %s due to dependence on unresolved %s' % (self.name(), agd.name())
                    wxs._queueForResolution(self)
                    return self
                uses_c2.update(agd.attributeUses())

        # Handle clause 3.  Note the slight difference in description
        # between smple and complex content is just that the complex
        # content assumes the base type definition is a complex type
        # definition.  So the same code should work for both, and we
        # don't bother to check content_style.
        if isinstance(self.__baseTypeDefinition, ComplexTypeDefinition):
            uses_c3 = uses_c3.union(self.__baseTypeDefinition.__attributeUses)
            if self.DM_restriction == self.__derivationMethod:
                # Exclude attributes per clause 3.  Note that this
                # process handles both 3.1 and 3.2, since we have
                # not yet filtered uses_c1 for prohibited attributes
                uses_c12 = uses_c1.union(uses_c2)
                for au in uses_c12:
                    uses_c3 = uses_c3.difference(au.matchingQNameMembers(uses_c3))
        uses = set([ _au for _au in uses_c1 if not _au.prohibited() ])
        self.__attributeUses = frozenset(uses.union(uses_c2).union(uses_c3))
        # @todo Handle attributeWildcard
        # Only now that we've succeeded do we set the method (mark this resolved)
        self.__derivationMethod = method
        return self

    def __completeSimpleResolution (self, wxs, definition_node_list, method, base_type):
        # deriviationMethod is assigned after resolution completes
        self.__baseTypeDefinition = base_type

        # Do content type
        if isinstance(self.__baseTypeDefinition, ComplexTypeDefinition):
            # Clauses 1, 2, and 3 might apply
            parent_content_type = self.__baseTypeDefinition.__contentType
            if (isinstance(parent_content_type, SimpleTypeDefinition) \
                    and (self.DM_restriction == method)):
                # Clause 1
                raise IncompleteImplementationError("contentType clause 1 of simple content in CTD")
            elif ((type(parent_content_type) == tuple) \
                    and (self.CT_mixed == parent_content_type[1]) \
                    and parent_content_type[0].isEmptiable()):
                # Clause 2
                raise IncompleteImplementationError("contentType clause 2 of simple content in CTD")
            else:
                # Clause 3
                raise IncompleteImplementationError("contentType clause 3 of simple content in CTD")
        else:
            # Clause 4
            self.__contentType = ( self.CT_SIMPLE, self.__baseTypeDefinition )
                
        return self.__completeProcessing(wxs, definition_node_list, method, 'simple')

    def __completeComplexResolution (self, wxs, type_node, content_node, definition_node_list, method, base_type):
        # deriviationMethod is assigned after resolution completes
        self.__baseTypeDefinition = base_type

        # Do content type

        # Definition 1: effective mixed
        mixed_attr = None
        if content_node is not None:
            mixed_attr = NodeAttribute(content_node, wxs, 'mixed')
        if mixed_attr is None:
            mixed_attr = NodeAttribute(type_node, wxs, 'mixed')
        if mixed_attr is not None:
            effective_mixed = datatypes.boolean(mixed_attr)
        else:
            effective_mixed = False

        # Definition 2: effective content
        case_2_1_predicate_count = 0
        test_2_1_1 = True
        test_2_1_2 = False
        test_2_1_3 = False
        typedef_particle_tags = Particle.TypedefTags(wxs)
        typedef_node = None
        allseq_particle_tags = []
        [ allseq_particle_tags.extend(wxs.xsQualifiedNames(_tag)) for _tag in [ 'all', 'sequence' ] ]
        xs_choice = wxs.xsQualifiedNames('choice')
        for cn in definition_node_list:
            if Node.ELEMENT_NODE != cn.nodeType:
                continue
            if cn.nodeName in typedef_particle_tags:
                typedef_node = cn
                test_2_1_1 = False
            if ((cn.nodeName in allseq_particle_tags) \
                    and (not HasNonAnnotationChild(wxs, cn))):
                test_2_1_2 = True
            if ((cn.nodeName in xs_choice) \
                    and (not HasNonAnnotationChild(wxs, cn))):
                mo_attr = NodeAttribute(cn, wxs, 'minOccurs')
                if ((mo_attr is not None) \
                        and (0 == datatypes.integer(mo_attr))):
                    test_2_1_3 = True
        satisfied_predicates = 0
        if test_2_1_1:
            satisfied_predicates += 1
        if test_2_1_2:
            satisfied_predicates += 1
        if test_2_1_3:
            satisfied_predicates += 1
        if 1 == satisfied_predicates:
            if effective_mixed:
                # Clause 2.1.4
                assert typedef_node is None
                m = ModelGroup(compositor=ModelGroup.C_SEQUENCE)
                effective_content = Particle(term=m)
            else:
                # Clause 2.1.5
                effective_content = self.CT_EMPTY
        else:
            # Clause 2.2
            assert typedef_node is not None
            effective_content = Particle.CreateFromDOM(wxs, typedef_node, self)

        # Shared from clause 3.1.2
        if effective_mixed:
            ct = self.CT_MIXED
        else:
            ct = self.CT_ELEMENT_ONLY
        # Clause 3
        if self.DM_restriction == method:
            # Clause 3.1
            if self.CT_EMPTY == effective_content:
                # Clause 3.1.1
                content_type = self.CT_EMPTY
            else:
                # Clause 3.1.2(.2)
                content_type = ( ct, effective_content )
        else:
            # Clause 3.2
            assert self.DM_extension == method
            assert self.__baseTypeDefinition.isResolved()
            parent_content_type = self.__baseTypeDefinition.contentType()
            if self.CT_EMPTY == effective_content:
                content_type = parent_content_type
            elif self.CT_EMPTY == parent_content_type:
                # Clause 3.2.2
                content_type = ( ct, effective_content )
            else:
                assert type(parent_content_type) == tuple
                m = ModelGroup(compositor=ModelGroup.C_SEQUENCE, particles=[ parent_content_type[1], effective_content ])
                content_type = ( ct, Particle(term=m) )

        assert (self.CT_EMPTY == content_type) or ((type(content_type) == tuple) and (content_type[1] is not None))
        self.__contentType = content_type
        return self.__completeProcessing(wxs, definition_node_list, method, 'complex')

    def isResolved (self):
        """Indicate whether this complex type is fully defined.
        
        All built-in type definitions are resolved upon creation.
        Schema-defined type definitionss are held unresolved until the
        schema has been completely read, so that references to later
        schema-defined types can be resolved.  Resolution is performed
        after the entire schema has been scanned and type-definition
        instances created for all topLevel{Simple,Complex}Types.

        If a built-in type definition is also defined in a schema
        (which it should be), the built-in definition is kept, with
        the schema-related information copied over from the matching
        schema-defined type definition.  The former then replaces the
        latter in the list of type definitions to be resolved.  See
        Schema._addNamedComponent.
        """
        # Only unresolved nodes have an unset derivationMethod
        return (self.__derivationMethod is not None)

    def _resolve (self, wxs):
        if self.isResolved():
            return self
        assert self.__domNode
        node = self.__domNode
        
        #print 'Resolving CTD %s' % (self.name(),)
        attr_val = NodeAttribute(node, wxs, 'abstract')
        if attr_val is not None:
            self.__abstract = datatypes.boolean(attr_val)

        # @todo implement prohibitedSubstitutions, final, annotations

        # Assume we're in the short-hand case: the entire content is
        # implicitly wrapped in a complex restriction of the ur-type.
        definition_node_list = node.childNodes
        is_complex_content = True
        base_type = ComplexTypeDefinition.UrTypeDefinition()
        method = self.DM_restriction

        # Determine whether above assumption is correct by looking for
        # element content and seeing if it's one of the wrapper
        # elements.
        first_elt = LocateFirstChildElement(node)
        content_node = None
        if first_elt:
            have_content = False
            if first_elt.nodeName in wxs.xsQualifiedNames('simpleContent'):
                have_content = True
                is_complex_content = False
            elif first_elt.nodeName in wxs.xsQualifiedNames('complexContent'):
                have_content = True
            if have_content:
                # Repeat the search to verify that only the one child is present.
                content_node = LocateFirstChildElement(node, require_unique=True)
                assert content_node == first_elt
                
                # Identify the contained restriction or extension
                # element, and extract the base type.
                ions = LocateFirstChildElement(content_node, absent_ok=False)
                if ions.nodeName in wxs.xsQualifiedNames('restriction'):
                    method = self.DM_restriction
                elif ions.nodeName in wxs.xsQualifiedNames('extension'):
                    method = self.DM_extension
                else:
                    raise SchemaValidationError('Expected restriction or extension as sole child of %s in %s' % (content_node.name(), self.name()))
                base_attr = NodeAttribute(ions, wxs, 'base')
                if base_attr is None:
                    raise SchemaValidationError('Element %s missing base attribute' % (ions.nodeName,))
                base_type = wxs.lookupType(base_attr)
                if not base_type.isResolved():
                    # Have to delay resolution until the type this
                    # depends on is available.
                    print 'Holding off resolution of %s due to dependence on unresolved %s' % (self.name(), base_type.name())
                    wxs._queueForResolution(self)
                    return self
                # The content is defined by the restriction/extension element
                definition_node_list = ions.childNodes
        if is_complex_content:
            self.__completeComplexResolution(wxs, node, content_node, definition_node_list, method, base_type)
        else:
            self.__completeSimpleResolution(wxs, definition_node_list, method, base_type)
        return self

class _UrTypeDefinition (ComplexTypeDefinition, _Singleton_mixin):
    """Subclass ensures there is only one ur-type."""
    pass

class AttributeGroupDefinition (_NamedComponent_mixin, _Resolvable_mixin, _Annotated_mixin):
    __attributeUses = None

    # Optional wildcard that constrains attributes
    __attributeWildcard = None

    @classmethod
    def CreateFromDOM (cls, wxs, node):
        assert node.nodeName in wxs.xsQualifiedNames('attributeGroup')
        name = NodeAttribute(node, wxs, 'name')

        rv = cls(name=name, target_namespace=wxs.getTargetNamespace())
        rv._annotationFromDOM(wxs, node)
        wxs._queueForResolution(rv)
        rv.__domNode = node
        return rv

    # Indicates whether we have resolved any references
    __isResolved = False
    def isResolved (self):
        return self.__isResolved

    def _resolve (self, wxs):
        if self.__isResolved:
            return self
        node = self.__domNode
        #print 'Resolving AG %s with %d children' % (self.name(), len(node.childNodes))
        uses = set()
        ref_attr = NodeAttribute(node, wxs, 'ref')
        if ref_attr is not None:
            agd = wxs.lookupAttributeGroup(ref_attr)
            if not agd.isResolved():
                print 'Holding off resolution of attribute group %s due to dependence on unresolved %s' % (self.name(), agd.name())
                wxs._queueForResolution(self)
                return self
            uses = uses.union(agd.attributeUses())
        xs_attribute = wxs.xsQualifiedNames('attribute')
        for cn in node.childNodes:
            if Node.ELEMENT_NODE != cn.nodeType:
                continue
            if cn.nodeName not in xs_attribute:
                continue
            uses.add(AttributeUse.CreateFromDOM(wxs, cn))

        self.__attributeUses = frozenset(uses)
        self.__isResolved = True
        self.__domNode = None
        return self
        
    def attributeUses (self):
        return self.__attributeUses

class ModelGroupDefinition (_NamedComponent_mixin, _Annotated_mixin):
    # Reference to a _ModelGroup
    __modelGroup = None

    def modelGroup (self):
        return self.__modelGroup

    @classmethod
    def CreateFromDOM (cls, wxs, node):
        assert node.nodeName in wxs.xsQualifiedNames('group')

        assert NodeAttribute(node, wxs, 'ref') is None

        name = NodeAttribute(node, wxs, 'name')
        rv = cls(name=name, target_namespace=wxs.getTargetNamespace())
        rv._annotationFromDOM(wxs, node)

        mg_tags = ModelGroup.GroupMemberTags(wxs)
        for cn in node.childNodes:
            if Node.ELEMENT_NODE != cn.nodeType:
                continue
            if cn.nodeName in mg_tags:
                assert not rv.__modelGroup
                rv.__modelGroup = ModelGroup.CreateFromDOM(wxs, cn)
        return rv

class ModelGroup (_Annotated_mixin):
    C_INVALID = 0
    C_ALL = 0x01
    C_CHOICE = 0x02
    C_SEQUENCE = 0x03

    # One of the C_* values above
    __compositor = C_INVALID
    def compositor (self): return self.__compositor

    # A list of _Particle instances
    __particles = None
    def particles (self): return self.__particles

    def __init__ (self, *args, **kw):
        super(ModelGroup, self).__init__(*args, **kw)
        compositor = kw.get('compositor', None)
        particles = kw.get('particles', [])
        self.__compositor = compositor
        self.__particles =[ _p._setAncestorComponent(self) for _p in particles ]

    def isPlural (self):
        for p in self.particles():
            if p.isPlural():
                return True
        return False

    @classmethod
    def CreateFromDOM (cls, wxs, node):
        if node.nodeName in wxs.xsQualifiedNames('all'):
            compositor = cls.C_ALL
        elif node.nodeName in wxs.xsQualifiedNames('choice'):
            compositor = cls.C_CHOICE
        elif node.nodeName in wxs.xsQualifiedNames('sequence'):
            compositor = cls.C_SEQUENCE
        else:
            raise IncompleteImplementationError('ModelGroup: Got unexpected %s' % (node.nodeName,))
        particles = []
        particle_tags = Particle.ParticleTags(wxs)
        for cn in node.childNodes:
            if Node.ELEMENT_NODE != cn.nodeType:
                continue
            if cn.nodeName in particle_tags:
                # NB: Ancestor of particle is set in the ModelGroup constructor
                particles.append(Particle.CreateFromDOM(wxs, cn, None))
        rv = cls(compositor=compositor, particles=particles)
        rv._annotationFromDOM(wxs, node)
        return rv

    @classmethod
    def GroupMemberTags (cls, wxs):
        return [ wxs.xsQualifiedName(_tag) for _tag in [ 'all', 'choice', 'sequence' ] ]

    def __str__ (self):
        comp = None
        if self.C_ALL == self.compositor():
            comp = 'ALL'
        elif self.C_CHOICE == self.compositor():
            comp = 'CHOICE'
        elif self.C_SEQUENCE == self.compositor():
            comp = 'SEQUENCE'
        return '%s:(%s)' % (comp, ",".join( [ str(_p) for _p in self.particles() ] ) )

class Particle (_Resolvable_mixin):
    """Some entity along with occurrence information."""
    # NB: Particles are not resolvable, but the term they include
    # probably has some resolvable component.

    __minOccurs = 1
    def minOccurs (self):
        """The minimum number of times the term may appear.

        Defaults to 1."""
        return self.__minOccurs

    __maxOccurs = 1
    def maxOccurs (self):
        """Upper limit on number of times the term may appear.

        If None, the term may appear any number of times; otherwise,
        this is an integral value indicating the maximum number of times
        the term may appear.  The default value is 1; the value, unless
        None, must always be at least minOccurs().
        """
        return self.__maxOccurs

    __term = None
    def term (self):
        """A reference to a ModelGroup, Wildcard, or ElementDeclaration."""
        return self.__term

    def isPlural (self):
        if (self.maxOccurs() is None) or 1 < self.maxOccurs():
            return True
        return self.term().isPlural()

    # If this particle is within a complexType or a group, we need the
    # corresponding ComplexTypeDefinition or ModelGroup in order to
    # handle non-reference local elements.
    __ancestorComponent = None

    def __init__ (self, term, *args, **kw):
        min_occurs = kw.get('min_occurs', 1)
        max_occurs = kw.get('max_occurs', 1)
        ancestor_component = kw.get('ancestor_component', None)
        super(Particle, self).__init__(*args, **kw)
        self.__term = term
        assert isinstance(min_occurs, (types.IntType, types.LongType))
        self.__minOccurs = min_occurs
        assert (max_occurs is None) or isinstance(max_occurs, (types.IntType, types.LongType))
        self.__maxOccurs = max_occurs
        if self.__maxOccurs is not None:
            if self.__minOccurs > self.__maxOccurs:
                raise LogicError('Particle minOccurs %s is greater than maxOccurs %s on creation' % (min_occurs, max_occurs))
        self.__ancestorComponent = ancestor_component
        assert (self.__ancestorComponent is None) or isinstance(self.__ancestorComponent, ( ComplexTypeDefinition, ModelGroup ))
    
    def _setAncestorComponent (self, ancestor_component):
        self.__ancestorComponent = ancestor_component
        return self

    @classmethod
    def CreateFromDOM (cls, wxs, node, ancestor_component):
        min_occurs = 1
        max_occurs = 1
        if not node.nodeName in cls.ParticleTags(wxs):
            raise LogicError('Attempted to create particle from illegal element %s' % (node.nodeName,))
        attr_val = NodeAttribute(node, wxs, 'minOccurs')
        if attr_val is not None:
            min_occurs = datatypes.nonNegativeInteger(attr_val)
        attr_val = NodeAttribute(node, wxs, 'maxOccurs')
        if attr_val is not None:
            if 'unbounded' == attr_val:
                max_occurs = None
            else:
                max_occurs = datatypes.nonNegativeInteger(attr_val)

        rv = cls(term=None, min_occurs=min_occurs, max_occurs=max_occurs, ancestor_component=ancestor_component)
        rv.__domNode = node
        wxs._queueForResolution(rv)

        return rv

    def isResolved (self):
        return self.__term is not None

    def _resolve (self, wxs):
        if self.isResolved():
            return self
        #print 'Resolving Particle'
        node = self.__domNode

        ref_attr = NodeAttribute(node, wxs, 'ref')
        if node.nodeName in wxs.xsQualifiedNames('group'):
            # 3.9.2 says use 3.8.2, which is ModelGroup.  The group
            # inside a particle is a groupRef.  If there is no group
            # with that name, this throws an exception as expected.
            if ref_attr is None:
                raise SchemaValidationError('group particle without reference')
            group_decl = wxs.lookupGroup(ref_attr)

            # Neither group definitions, nor model groups, require
            # resolution, so we can just extract the reference.
            term = group_decl.modelGroup()
            assert term is not None
        elif node.nodeName in wxs.xsQualifiedNames('element'):
            assert wxs.xsQualifiedName('schema') != node.parentNode.nodeName
            # 3.9.2 says use 3.3.2, which is Element.  The element
            # inside a particle is a localElement, so we either get
            # the one it refers to, or create an anonymous one here.
            if ref_attr is not None:
                term = wxs.lookupElement(ref_attr)
            else:
                term = ElementDeclaration.CreateFromDOM(wxs, node, self.__ancestorComponent)
            assert term is not None
        elif node.nodeName in wxs.xsQualifiedNames('any'):
            # 3.9.2 says use 3.10.2, which is Wildcard.
            term = Wildcard.CreateFromDOM(wxs, node)
            assert term is not None
        elif node.nodeName in ModelGroup.GroupMemberTags(wxs):
            # Choice, sequence, and all inside a particle are explicit
            # groups (or a restriction of explicit group, in the case
            # of all)
            term = ModelGroup.CreateFromDOM(wxs, node)
        else:
            raise LogicError('Unhandled node in Particle._resolve: %s' % (node.toxml(),))
        assert term is not None
        self.__term = term
        self.__domNode = None
        return self
        
    @classmethod
    def TypedefTags (cls, wxs):
        """Return the list of schema element tags for typedef particles."""
        return [ wxs.xsQualifiedName(_tag) for _tag in [ 'group', 'all', 'choice', 'sequence' ] ]

    @classmethod
    def ParticleTags (cls, wxs):
        """Return the list of schema element tags for any particle."""
        return [ wxs.xsQualifiedName(_tag) for _tag in [ 'group', 'all', 'choice', 'sequence', 'element', 'any' ] ]

    def __str__ (self):
        return '%s{%d:%s}' % (self.term(), self.minOccurs(), self.maxOccurs())


# 3.10.1
class Wildcard (_Annotated_mixin):
    NC_any = '##any'            #<<< The namespace constraint "##any"
    NC_not = '##other'          #<<< A flag indicating constraint "##other"
    NC_targetNamespace = '##targetNamespace'
    NC_local = '##local'

    __namespaceConstraint = None
    def namespaceConstraint (self):
        """A constraint on the namespace for the wildcard.

        Valid values are:
         * Wildcard.NC_any
         * A tuple ( Wildcard.NC_not, a_namespace )
         * set(of_namespaces)

        Note that namespace are represented by Namespace instances,
        not the URIs that actually define a namespace.  Absence is
        represented by None, both in the "not" pair and in the set.
        """
        return self.__namespaceConstraint

    PC_skip = 'skip'            #<<< No constraint is applied
    PC_lax = 'lax'              #<<< Validate against available uniquely determined declaration
    PC_strict = 'strict'        #<<< Validate against declaration or xsi:type which must be available

    # One of PC_*
    __processContents = None
    def processContents (self): return self.__processContents

    def isPlural (self): return False

    def __init__ (self, *args, **kw):
        assert 0 == len(args)
        super(Wildcard, self).__init__(*args, **kw)
        self.__namespaceConstraint = kw['namespace_constraint']
        self.__processContents = kw['process_contents']

    @classmethod
    def CreateFromDOM (cls, wxs, node):
        nc = NodeAttribute(node, wxs, 'namespace')
        if nc is None:
            namespace_constraint = cls.NC_any
        else:
            if cls.NC_any == nc:
                namespace_constraint = cls.NC_any
            elif cls.NC_not == nc:
                namespace_constraint = ( cls.NC_not, wxs.getTargetNamespace() )
            else:
                ncs = set()
                for ns_uri in nc.split():
                    if cls.NC_local == ns_uri:
                        ncs.add(None)
                    elif cls.NC_targetNamespace == ns_uri:
                        ncs.add(wxs.getTargetNamespace())
                    else:
                        namespace = Namespace.NamespaceForURI(ns_uri)
                        if namespace is None:
                            namespace = Namespace.Namespace(ns_uri)
                        ncs.add(namespace)
                namespace_constraint = frozenset(ncs)

        pc = NodeAttribute(node, wxs, 'processContents')
        if pc is None:
            process_contents = cls.PC_strict
        else:
            if pc in [ cls.PC_skip, cls.PC_lax, cls.PC_strict ]:
                process_contents = pc
            else:
                raise SchemaValidationError('illegal value "%s" for any processContents attribute' % (pc,))

        rv = cls(namespace_constraint=namespace_constraint, process_contents=process_contents)
        rv._annotationFromDOM(wxs, node)
        return rv

# 3.11.1
class IdentityConstraintDefinition (_NamedComponent_mixin, _Annotated_mixin):
    ICC_KEY = 0x01
    ICC_KEYREF = 0x02
    ICC_UNIQUE = 0x04

    __identityConstraintCategory = None
    def identityConstraintCategory (self): return self.__identityConstraintCategory

    __selector = None
    def selector (self): return self.__selector
    
    __fields = None
    def fields (self): return self.__fields
    
    __referencedKey = None
    
    __annotations = None
    def annotations (self): return self.__annotations

    @classmethod
    def CreateFromDOM (cls, wxs, node):
        name = NodeAttribute(node, wxs, 'name')
        rv = cls(name=name, target_namespace=wxs.getTargetNamespace())
        #rv._annotationFromDOM(wxs, node);
        if node.nodeName in wxs.xsQualifiedNames('key'):
            rv.__identityConstraintCategory = cls.ICC_KEY
        elif node.nodeName in wxs.xsQualifiedNames('keyref'):
            rv.__identityConstraintCategory = cls.ICC_KEYREF
            # Look up the constraint identified by the refer attribute.
            raise IncompleteImplementationError('Need to support keyref')
        elif node.nodeName in wxs.xsQualifiedNames('unique'):
            rv.__identityConstraintCategory = cls.ICC_UNIQUE
        else:
            raise LogicError('Unexpected identity constraint node %s' % (node.toxml(),))

        cn = LocateUniqueChild(node, wxs, 'selector')
        rv.__selector = NodeAttribute(cn, wxs, 'xpath')
        if rv.__selector is None:
            raise SchemaValidationError('selector element missing xpath attribute')

        rv.__fields = []
        for cn in LocateMatchingChildren(node, wxs, 'field'):
            xp_attr = NodeAttribute(cn, wxs, 'xpath')
            if xp_attr is None:
                raise SchemaValidationError('field element missing xpath attribute')
            rv.__fields.append(xp_attr)

        rv._annotationFromDOM(wxs, node)
        rv.__annotations = []
        if rv.annotation() is not None:
            rv.__annotations.append(rv)
        annotated_child_names = list(wxs.xsQualifiedNames('selector'))
        annotated_child_names.extend(wxs.xsQualifiedNames('field'))
        for cn in node.childNodes:
            if (Node.ELEMENT_NODE != cn.nodeType):
                continue
            an = None
            if (cn.nodeName in annotated_child_names):
                an = LocateUniqueChild(cn, wxs, 'annotation')
            elif cn.nodeName in wxs.xsQualifiedNames('annotation'):
                an = cn
            if an is not None:
                rv.__annotations.append(Annotation.CreateFromDOM(wxs, an))

        return rv
    
# 3.12.1
class NotationDeclaration (_NamedComponent_mixin, _Annotated_mixin):
    __systemIdentifier = None
    def systemIdentifier (self): return self.__systemIdentifier
    
    __publicIdentifier = None
    def publicIdentifier (self): return self.__publicIdentifier

    @classmethod
    def CreateFromDOM (cls, wxs, node):
        name = NodeAttribute(node, wxs, 'name')
        rv = cls(name=name, target_namespace=wxs.getTargetNamespace())

        rv.__systemIdentifier = NodeAttribute(node, wxs, 'system')
        rv.__publicIdentifier = NodeAttribute(node, wxs, 'public')

        rv._annotationFromDOM(wxs, node)
        return rv

# 3.13.1
class Annotation (object):
    __applicationInformation = None
    def applicationInformation (self):
        return self.__applicationInformation
    
    __userInformation = None
    def userInformation (self):
        return self.__userInformation

    # @todo what the hell is this?  From 3.13.2, I think it's a place
    # to stuff attributes from the annotation element, which makes
    # sense, as well as from the annotation's parent element, which
    # doesn't.  Apparently it's for attributes that don't belong to
    # the XMLSchema namespace; so maybe we're not supposed to add
    # those to the other components.  Note that these are attribute
    # information items, not attribute uses.
    __attributes = None

    @classmethod
    def CreateFromDOM (cls, wxs, node):
        rv = cls()

        # @todo: Scan for attributes in the node itself that do not
        # belong to the XMLSchema namespace.

        # Node should be an XMLSchema annotation node
        assert node.nodeName in wxs.xsQualifiedNames('annotation')
        app_info = []
        user_info = []
        for cn in node.childNodes:
            if cn.nodeName in wxs.xsQualifiedNames('appinfo'):
                app_info.append(cn)
            elif cn.nodeName in wxs.xsQualifiedNames('documentation'):
                user_info.append(cn)
            else:
                pass
        if 0 < len(app_info):
            rv.__applicationInformation = app_info
        if 0 < len(user_info):
            rv.__userInformation = user_info

        #n2 = rv.generateDOM(wxs, node.ownerDocument)
        #print "In: %s\n\nOut: %s\n" % (node.toxml(), n2.toxml())
        return rv

    def generateDOM (self, wxs, document):
        node = wxs.createDOMNodeInWXS(document, 'annotation')
        if self.__userInformation is not None:
            ui_node = wxs.createDOMNodeInWXS(document, 'documentation')
            for ui in self.__userInformation:
                for cn in ui.childNodes:
                    ui_node.appendChild(cn.cloneNode(True))
            node.appendChild(ui_node)
        if self.__applicationInformation is not None:
            ai_node = wxs.createDOMNodeInWXS(document, 'appinfo')
            for ai in self.__applicationInformation:
                for cn in ai.childNodes:
                    ai_node.appendChild(cn.cloneNode(True))
            node.appendChild(ai_node)
        return node

    def __str__ (self):
        """Return the catenation of all user information elements in the annotation."""
        text = []
        # Values in userInformation are DOM "documentation" elements.
        # We want their combined content.
        for dn in self.__userInformation:
            for cn in dn.childNodes:
                if Node.TEXT_NODE == cn.nodeType:
                    text.append(cn.data)
        return ''.join(text)


# Section 3.14.
class SimpleTypeDefinition (_NamedComponent_mixin, _Resolvable_mixin, _Annotated_mixin):
    """The schema component for simple type definitions.

    This component supports the basic datatypes of XML schema, and
    those that define the values for attributes.

    @see PythonSimpleTypeSupport for additional information.
    """

    # Reference to the SimpleTypeDefinition on which this is based.
    # The value must be non-None except for the simple ur-type
    # definition.
    __baseTypeDefinition = None
    def baseTypeDefinition (self):
        return self.__baseTypeDefinition

    # A map from a subclass of facets.ConstrainingFacet to an instance
    # of that class, or None if the facet has not been constrained in
    # the type.
    __facets = None
    def facets (self):
        assert (self.__facets is None) or (type(self.__facets) == types.DictType)
        return self.__facets

    # A list of instances of facets.FundamentalFacet
    __fundamentalFacets = None
    def fundamentalFacets (self):
        """A frozenset of instances of facets.FundamentallFacet."""
        return self.__fundamentalFacets

    STD_empty = 0          #<<< Marker indicating an empty set of STD forms
    STD_extension = 0x01   #<<< Representation for extension in a set of STD forms
    STD_list = 0x02        #<<< Representation for list in a set of STD forms
    STD_restriction = 0x04 #<<< Representation of restriction in a set of STD forms
    STD_union = 0x08       #<<< Representation of union in a set of STD forms
    # Bitmask defining the subset that comprises the final property
    __final = STD_empty
    @classmethod
    def _FinalToString (cls, final_value):
        """Convert a final value to a string."""
        tags = []
        if final_value & cls.STD_extension:
            tags.append('extension')
        if final_value & cls.STD_list:
            tags.append('list')
        if final_value & cls.STD_restriction:
            tags.append('restriction')
        if final_value & cls.STD_union:
            tags.append('union')
        return ' '.join(tags)

    VARIETY_absent = 0x01       #<<< Only used for the ur-type
    VARIETY_atomic = 0x02       #<<< Use for types based on a primitive type
    VARIETY_list = 0x03         #<<< Use for lists of atomic-variety types
    VARIETY_union = 0x04        #<<< Use for types that aggregate other types

    # Identify the sort of value collection this holds.  This field is
    # used to identify unresolved definitions.
    __variety = None
    def variety (self):
        return self.__variety
    @classmethod
    def VarietyToString (cls, variety):
        """Convert a variety value to a string."""
        if cls.VARIETY_absent == variety:
            return 'absent'
        if cls.VARIETY_atomic == variety:
            return 'atomic'
        if cls.VARIETY_list == variety:
            return 'list'
        if cls.VARIETY_union == variety:
            return 'union'
        return '?NoVariety?'

    # For atomic variety only, the root (excepting ur-type) type.
    __primitiveTypeDefinition = None
    def primitiveTypeDefinition (self):
        if self.variety() != self.VARIETY_atomic:
            raise BadPropertyError('primitiveTypeDefinition only defined for atomic types')
        if self.__primitiveTypeDefinition is None:
            raise LogicError('Expected primitive type')
        return self.__primitiveTypeDefinition

    # For list variety only, the type of items in the list
    __itemTypeDefinition = None
    def itemTypeDefinition (self):
        if self.VARIETY_list != self.variety():
            raise BadPropertyError('itemTypeDefinition only defined for list types')
        if self.__itemTypeDefinition is None:
            raise LogicError('Expected item type')
        return self.__itemTypeDefinition

    # For union variety only, the sequence of candidate members
    __memberTypeDefinitions = None
    def memberTypeDefinitions (self):
        if self.VARIETY_union != self.variety():
            raise BadPropertyError('memberTypeDefinitions only defined for union types')
        if self.__memberTypeDefinitions is None:
            raise LogicError('Expected member types')
        return self.__memberTypeDefinitions

    # A non-property field that holds a reference to the DOM node from
    # which the type is defined.  The value is held only between the
    # point where the simple type definition instance is created until
    # the point it is resolved.
    __domNode = None
    
    # Indicate that this instance was defined as a built-in rather
    # than from a DOM instance.
    __isBuiltin = False

    # Allocate one of these.  Users should use one of the Create*
    # factory methods instead.  In an attempt to keep users from
    # creating these directly rather than through the approved factory
    # methods, the signature does not provide defaults for the core
    # attributes.
    def __init__ (self, *args, **kw):
        super(SimpleTypeDefinition, self).__init__(*args, **kw)
        self.__variety = kw['variety']

    def __str__ (self):
        elts = [ self.name(), ': ' ]
        if self.VARIETY_absent == self.variety():
            elts.append('the ur-type')
        elif self.VARIETY_atomic == self.variety():
            elts.append('restriction of %s' % (self.baseTypeDefinition().name(),))
        elif self.VARIETY_list == self.variety():
            elts.append('list of %s' % (self.itemTypeDefinition().name(),))
        elif self.VARIETY_union == self.variety():
            elts.append('union of %s' % (" ".join([str(_mtd.name()) for _mtd in self.memberTypeDefinitions()],)))
        else:
            elts.append('???')
            #raise LogicError('Unexpected variety %s' % (self.variety(),))
        if self.__facets:
            felts = []
            for (k, v) in self.__facets.items():
                if v is not None:
                    felts.append(str(v))
            elts.append("\n  %s" % (','.join(felts),))
        if self.__fundamentalFacets:
            elts.append("\n  ")
            elts.append(','.join( [str(_f) for _f in self.__fundamentalFacets ]))
        return ''.join(elts)

    def _setFromInstance (self, other):
        """Override fields in this instance with those from the other.

        This method is invoked only by Schema._addNamedComponent, and
        then only when a built-in type collides with a schema-defined
        type.  Material like facets is not (currently) held in the
        built-in copy, so the DOM information is copied over to the
        built-in STD, which is subsequently re-resolved.

        Returns self.
        """
        assert self.isNameEquivalent(other)
        super(SimpleTypeDefinition, self)._setFromInstance(other)

        # The other STD should be an unresolved schema-defined type.
        assert other.__baseTypeDefinition is None
        assert other.__domNode is not None
        self.__domNode = other.__domNode

        # Preserve the python support
        if other.__pythonSupport is not None:
            # @todo ERROR multiple references
            self.__pythonSupport = other.__pythonSupport

        # Mark this instance as unresolved so it is re-examined
        self.__variety = None
        return self

    def isBuiltin (self):
        """Indicate whether this simple type is a built-in type."""
        return self.__isBuiltin

    __SimpleUrTypeDefinition = None
    @classmethod
    def SimpleUrTypeDefinition (cls, in_builtin_definition=False):
        """Create the SimpleTypeDefinition instance that approximates the simple ur-type.

        See section 3.14.7."""

        if in_builtin_definition and (cls.__SimpleUrTypeDefinition is not None):
            raise LogicError('Multiple definitions of SimpleUrType')
        if cls.__SimpleUrTypeDefinition is None:
            # Note: We use a singleton subclass
            bi = _SimpleUrTypeDefinition(name='anySimpleType', target_namespace=Namespace.XMLSchema, variety=cls.VARIETY_absent)
            bi._setPythonSupport(datatypes.anySimpleType)

            # The baseTypeDefinition is the ur-type.
            bi.__baseTypeDefinition = ComplexTypeDefinition.UrTypeDefinition()
            # The simple ur-type has an absent variety, not an atomic
            # variety, so does not have a primitiveTypeDefinition

            # No facets on the ur type
            bi.__facets = {}
            bi.__fundamentalFacets = frozenset()

            bi.__isBuiltin = True

            cls.__SimpleUrTypeDefinition = bi
        return cls.__SimpleUrTypeDefinition

    @classmethod
    def CreatePrimitiveInstance (cls, name, target_namespace, python_support):
        """Create a primitive simple type in the target namespace.

        This is mainly used to pre-load standard built-in primitive
        types, such as those defined by XMLSchema Datatypes.  You can
        use it for your own schemas as well, if you have special types
        that require explicit support to for Pythonic conversion.

        All parameters are required and must be non-None.
        """
        
        bi = cls(name=name, target_namespace=target_namespace, variety=cls.VARIETY_atomic)
        bi._setPythonSupport(python_support)

        # Primitive types are based on the ur-type, and have
        # themselves as their primitive type definition.
        bi.__baseTypeDefinition = cls.SimpleUrTypeDefinition()
        bi.__primitiveTypeDefinition = bi

        # Primitive types are built-in
        bi.__isBuiltin = True
        return bi

    @classmethod
    def CreateDerivedInstance (cls, name, target_namespace, parent_std, python_support):
        """Create a derived simple type in the target namespace.

        This is used to pre-load standard built-in derived types.  You
        can use it for your own schemas as well, if you have special
        types that require explicit support to for Pythonic
        conversion.
        """
        assert parent_std
        assert parent_std.__variety in (cls.VARIETY_absent, cls.VARIETY_atomic)
        bi = cls(name=name, target_namespace=target_namespace, variety=parent_std.__variety)
        bi._setPythonSupport(python_support)

        # We were told the base type.  If this is atomic, we re-use
        # its primitive type.  Note that these all may be in different
        # namespaces.
        bi.__baseTypeDefinition = parent_std
        if cls.VARIETY_atomic == bi.__variety:
            bi.__primitiveTypeDefinition = bi.__baseTypeDefinition.__primitiveTypeDefinition

        # Derived types are built-in
        bi.__isBuiltin = True
        return bi

    @classmethod
    def CreateListInstance (cls, name, target_namespace, item_std):
        """Create a list simple type in the target namespace.

        This is used to preload standard built-in list types.  You can
        use it for your own schemas as well, if you have special types
        that require explicit support to for Pythonic conversion; but
        note that such support is identified by the item_std.
        """
        bi = cls(name=name, target_namespace=target_namespace, variety=cls.VARIETY_list)
        # Note: The pythonSupport__ field remains None, since list
        # instances share a class-level implementation that is based
        # on their itemTypeDefinition.

        # The base type is the ur-type.  We were given the item type.
        bi.__baseTypeDefinition = cls.SimpleUrTypeDefinition()
        assert item_std
        bi.__itemTypeDefinition = item_std

        # List types are built-in
        bi.__isBuiltin = True
        return bi

    @classmethod
    def CreateUnionInstance (cls, name, target_namespace, member_stds):
        """(Placeholder) Create a union simple type in the target namespace.

        This function has not been implemented."""
        raise IncompleteImplementationError('No support for built-in union types')

    def __singleSimpleTypeChild (self, wxs, body):
        simple_type_child = None
        for cn in body.childNodes:
            if (Node.ELEMENT_NODE == cn.nodeType):
                assert cn.nodeName in wxs.xsQualifiedNames('simpleType')
                assert not simple_type_child
                simple_type_child = cn
        assert simple_type_child
        return simple_type_child

    # The __initializeFrom* methods are responsible for identifying
    # the variety and the baseTypeDefinition.  The remainder of the
    # resolution is performed by the __completeResolution method.
    # Note that in some cases resolution might yet be premature, so
    # variety is not saved until it is complete.  All this stuff is
    # from section 3.14.2.

    def __initializeFromList (self, wxs, body):
        self.__baseTypeDefinition = self.SimpleUrTypeDefinition()
        return self.__completeResolution(wxs, body, self.VARIETY_list, 'list')

    def __initializeFromRestriction (self, wxs, body):
        base_attr = NodeAttribute(body, wxs, 'base')
        if base_attr is not None:
            # Look up the base.  If there is no registered type of
            # that name, an exception gets thrown that percolates up
            # to the user.
            base_type = wxs.lookupSimpleType(base_attr)
            # If the base type exists but has not yet been resolve,
            # delay processing this type until the one it depends on
            # has been completed.
            if not base_type.isResolved():
                print 'Holding off resolution of anonymous simple type due to dependence on unresolved %s' % (base_type.name(),)
                wxs._queueForResolution(self)
                return self
            self.__baseTypeDefinition = base_type
        else:
            self.__baseTypeDefinition = self.SimpleUrTypeDefinition()
        # NOTE: 3.14.1 specifies that the variety is the variety of
        # the base type definition; but if that is an ur type, whose
        # variety is absent per 3.14.5, I'm really certain that they mean it to
        # be atomic instead.
        variety = self.__baseTypeDefinition.__variety
        if self.__baseTypeDefinition == self.SimpleUrTypeDefinition():
            variety = self.VARIETY_atomic
        # @todo extract facet constraints
        return self.__completeResolution(wxs, body, variety, 'restriction')

    def __initializeFromUnion (self, wxs, body):
        self.__baseTypeDefinition = self.SimpleUrTypeDefinition()
        return self.__completeResolution(wxs, body, self.VARIETY_union, 'union')

    def __processHasFacetAndProperty (self, wxs):
        """Identify the facets and properties for this stype.

        This method simply identifies the facets that apply to this
        specific type, and records property values.  Only
        explicitly-associated facets and properties are stored; others
        from base types will also affect this type.  The information
        is taken from the applicationInformation children of the
        definition's annotation node, if any.  If there is no support
        for the XMLSchema_hasFacetAndProperty namespace, this is a
        no-op.

        Upon return, self.__facets is a map from the class for an
        associated fact to None, and self.__fundamentalFacets is a
        frozenset of instances of FundamentalFacet.

        The return value is self.
        """
        self.__facets = { }
        self.__fundamentalFacets = frozenset()
        if self.annotation() is None:
            return self
        app_info = self.annotation().applicationInformation()
        if app_info is  None:
            return self
        hfp = None
        try:
            hfp = wxs.namespaceForURI(Namespace.XMLSchema_hfp.uri())
        except SchemaValidationError, e:
            pass
        if hfp is None:
            return None
        facet_map = { }
        fundamental_facets = set()
        has_facet = wxs.qualifiedNames('hasFacet', hfp)
        has_property = wxs.qualifiedNames('hasProperty', hfp)
        seen_facets = set()
        for ai in app_info:
            for cn in ai.childNodes:
                if Node.ELEMENT_NODE != cn.nodeType:
                    continue
                if cn.nodeName in has_facet:
                    facet_name = NodeAttribute(cn, wxs, 'name', Namespace.XMLSchema_hfp)
                    if facet_name is None:
                        raise SchemaValidationError('hasFacet missing name attribute')
                    if facet_name in seen_facets:
                        raise SchemaValidationError('Multiple hasFacet specifications for %s' % (facet_name,))
                    seen_facets.add(facet_name)
                    facet_map[facets.ConstrainingFacet.ClassForFacet(facet_name)] = None
                if cn.nodeName in has_property:
                    fundamental_facets.add(facets.FundamentalFacet.CreateFromDOM(wxs, cn, self))
        if 0 < len(facet_map):
            assert self.__baseTypeDefinition == self.SimpleUrTypeDefinition()
            self.__facets = facet_map
            assert type(self.__facets) == types.DictType
        if 0 < len(fundamental_facets):
            self.__fundamentalFacets = frozenset(fundamental_facets)
        return self

    def __updateFacets (self, wxs, body):
        # We want a map from the union of the facet classes from this
        # STD and the baseTypeDefinition (if present), to None if the
        # facet has not been constrained, or a ConstrainingFacet
        # instance if it is.  ConstrainingFacet instances created for
        # local constraints also need a pointer to the corresponding
        # facet from the base type definition, because those
        # constraints also affect this type.
        base_facets = {}
        base_facets.update(self.__facets)
        if self.__baseTypeDefinition.facets():
            assert type(self.__baseTypeDefinition.facets()) == types.DictType
            base_facets.update(self.__baseTypeDefinition.facets())
        facets = {}
        for fc in base_facets.keys():
            children = LocateMatchingChildren(body, wxs, fc.Name())
            fi = base_facets[fc]
            if 0 < len(children):
                fi = fc(base_type_definition=self.__baseTypeDefinition,
                        owner_type_definition=self,
                        super_facet=base_facets[fc])
                for cn in children:
                    fi.updateFromDOM(wxs, cn)
            facets[fc] = fi
        self.__facets = facets
        assert type(self.__facets) == types.DictType

    # Complete the resolution of some variety of STD.  Note that the
    # variety is compounded by an alternative, since there is no
    # 'restriction' variety.
    def __completeResolution (self, wxs, body, variety, alternative):
        if self.__pythonSupport is None:
            # @todo ERROR multiple references
            print '%s based on %s' % (self.name(), self.__baseTypeDefinition.name())
            self._setPythonSupport(self.__baseTypeDefinition.pythonSupport())
        assert self.__variety is None
        assert variety is not None
        if self.VARIETY_absent == variety:
            # The ur-type is always resolved.  So are restrictions of it,
            # which is how we might get here.
            pass
        elif self.VARIETY_atomic == variety:
            # Atomic types (and their restrictions) use the primitive
            # type, which is the highest type that is below the
            # ur-type (which is not atomic).
            ptd = self
            while isinstance(ptd, SimpleTypeDefinition) and (self.VARIETY_atomic == ptd.variety()):
                assert ptd.__baseTypeDefinition
                ptd = ptd.__baseTypeDefinition
            if not isinstance(ptd, SimpleTypeDefinition):
                assert False
                assert ComplexTypeDefinition.UrTypeDefinition() == ptd
                self.__primitiveTypeDefinition = self.SimpleUrTypeDefinition()
            else:
                self.__primitiveTypeDefinition = ptd
        elif self.VARIETY_list == variety:
            if 'list' == alternative:
                attr_val = NodeAttribute(body, wxs, 'itemType')
                if attr_val is not None:
                    self.__itemTypeDefinition = wxs.lookupSimpleType(attr_val)
                else:
                    # NOTE: The newly created anonymous item type will
                    # not be resolved; the caller needs to handle
                    # that.
                    self.__itemTypeDefinition = self.CreateFromDOM(wxs, self.__singleSimpleTypeChild(wxs, body))
            elif 'restriction' == alternative:
                self.__itemTypeDefinition = self.__baseTypeDefinition.__itemTypeDefinition
            else:
                raise LogicError('completeResolution list variety with alternative %s' % (alternative,))
        elif self.VARIETY_union == variety:
            if 'union' == alternative:
                # First time we try to resolve, create the member type
                # definitions.  If something later prevents us from
                # resolving this type, we don't want to create them
                # again, because we might already have references to
                # them.
                if self.__memberTypeDefinitions is None:
                    print '!! Identifying member type definitions for %s:' % (self.name(),)
                    mtd = []
                    # If present, first extract names from memberTypes,
                    # and add each one to the list
                    member_types = NodeAttribute(body, wxs, 'memberTypes')
                    if member_types is not None:
                        print '!!! Union mt attribute %s' % (member_types,)
                        for mn in member_types.split():
                            # THROW if type has not been defined
                            if 0 > mn.find(':'):
                                mn = wxs.xsQualifiedName(mn)
                            mtd.append(wxs.lookupSimpleType(mn))
                    # Now look for local type definitions
                    for cn in body.childNodes:
                        if (Node.ELEMENT_NODE == cn.nodeType):
                            if cn.nodeName in wxs.xsQualifiedNames('simpleType'):
                                # NB: Attempt resolution right away to
                                # eliminate unnecessary delay below
                                # when looking for union expansions.
                                mtd.append(self.CreateFromDOM(wxs, cn)._resolve(wxs))
                    self.__memberTypeDefinitions = mtd[:]
                    assert None not in self.__memberTypeDefinitions

                # Replace any member types that are themselves unions
                # with the members of those unions, in order.  Note
                # that doing this might indicate we can't resolve this
                # type yet, which is why we separated the member list
                # creation and the substitution phases
                mtd = []
                for mt in self.__memberTypeDefinitions:
                    assert isinstance(mt, SimpleTypeDefinition)
                    if not mt.isResolved():
                        wxs._queueForResolution(self)
                        return self
                    if self.VARIETY_union == mt.variety():
                        mtd.extend(mt.memberTypeDefinitions())
                    else:
                        mtd.append(mt)
            elif 'restriction' == alternative:
                assert self.__baseTypeDefinition__
                # Base type should have been resolved before we got here
                assert self.__baseTypeDefinition__.isResolved()
                mtd = self.__baseTypeDefinition.__memberTypeDefinitions
                assert mtd is not None
            else:
                raise LogicError('completeResolution union variety with alternative %s' % (alternative,))
            # Save a unique copy
            self.__memberTypeDefinitions = mtd[:]
        else:
            print 'VARIETY "%s"' % (self.__variety,)
            raise LogicError('completeResolution with variety 0x%02x' % (self.__variety,))

        # Determine what facets, if any, apply to this type.  This
        # should only do something if this is a primitive type.
        self.__processHasFacetAndProperty(wxs)
        self.__updateFacets(wxs, body)

        self.__variety = variety
        self.__domNode = None
        print 'Completed STD %s' % (self,)
        return self

    def isResolved (self):
        """Indicate whether this simple type is fully defined.
        
        Type resolution for simple types means that the corresponding
        schema component fields have been set.  Specifically, that
        means variety, baseTypeDefinition, and the appropriate
        additional fields depending on variety.  See _resolve() for
        more information.
        """
        # Only unresolved nodes have an unset variety
        return (self.__variety is not None)

    def _resolve (self, wxs):
        """Attempt to resolve the type.

        Type resolution for simple types means that the corresponding
        schema component fields have been set.  Specifically, that
        means variety, baseTypeDefinition, and the appropriate
        additional fields depending on variety.

        All built-in STDs are resolved upon creation.  Schema-defined
        STDs are held unresolved until the schema has been completely
        read, so that references to later schema-defined STDs can be
        resolved.  Resolution is performed after the entire schema has
        been scanned and STD instances created for all
        topLevelSimpleTypes.

        If a built-in STD is also defined in a schema (which it should
        be for XMLSchema), the built-in STD is kept, with the
        schema-related information copied over from the matching
        schema-defined STD.  The former then replaces the latter in
        the list of STDs to be resolved.

        Types defined by restriction have the same variety as the type
        they restrict.  If a simple type restriction depends on an
        unresolved type, this method simply queues it for resolution
        in a later pass and returns.
        """
        if self.__variety is not None:
            return self
        #print 'Resolving STD %s' % (self.name(),)
        assert self.__domNode
        node = self.__domNode
        
        bad_instance = False
        # The guts of the node should be exactly one instance of
        # exactly one of these three types.
        candidate = LocateUniqueChild(node, wxs, 'list')
        if candidate:
            self.__initializeFromList(wxs, candidate)

        candidate = LocateUniqueChild(node, wxs, 'restriction')
        if candidate:
            if self.__variety is None:
                self.__initializeFromRestriction(wxs, candidate)
            else:
                bad_instance = True

        candidate = LocateUniqueChild(node, wxs, 'union')
        if candidate:
            if self.__variety is None:
                self.__initializeFromUnion(wxs, candidate)
            else:
                bad_instance = True

        # It is NOT an error to fail to resolve the type.
        if bad_instance:
            raise SchemaValidationError('Expected exactly one of list, restriction, union as child of simpleType')

        return self

    @classmethod
    def CreateFromDOM (cls, wxs, node):
        # Node should be an XMLSchema simpleType node
        assert node.nodeName in wxs.xsQualifiedNames('simpleType')

        # @todo Process "final" attributes
        
        if NodeAttribute(node, wxs, 'final') is not None:
            raise IncompleteImplementationError('"final" attribute not currently supported')

        name = NodeAttribute(node, wxs, 'name')

        rv = cls(name=name, target_namespace=wxs.getTargetNamespace(), variety=None)
        rv._annotationFromDOM(wxs, node)

        # @todo identify supported facets and properties (hfp)

        # Creation does not attempt to do resolution.  Queue up the newly created
        # whatsis so we can resolve it after everything's been read in.
        rv.__domNode = node
        wxs._queueForResolution(rv)
        
        return rv

    # pythonSupport is an instance of a subclass of
    # PythonSimpleTypeSupport.  When set, this simple type definition
    # must be associated with the support instance using
    # PSTS._setSimpleTypeDefinition.
    __pythonSupport = None

    def _setPythonSupport (self, python_support):
        # Includes check that python_support is not None
        assert issubclass(python_support, datatypes._PST_mixin)
        # Can't share support instances
        self.__pythonSupport = python_support
        return self.__pythonSupport

    def pythonSupport (self):
        if self.__pythonSupport is None:
            raise LogicError('%s: No support defined' % (self.name(),))
        return self.__pythonSupport

    def stringToPython (self, string):
        return self.pythonSupport().stringToPython(string)

    def pythonToString (self, value):
        return self.pythonSupport().pythonToString(value)

class _SimpleUrTypeDefinition (SimpleTypeDefinition, _Singleton_mixin):
    """Subclass ensures there is only one simple ur-type."""
    pass

class Schema (object):
    NT_type = 0x01              #<<< Name represents a simple or complex type
    NT_attributeGroup = 0x02    #<<< Name represents an attribute group definition
    NT_modelGroup = 0x03        #<<< Name represents a model group definition
    NT_attribute = 0x04         #<<< Name represents an attribute declaration
    NT_element = 0x05           #<<< Name represents an element declaration
    NT_notation = 0x06          #<<< Name represents a notation declaration

    __typeDefinitions = None
    __attributeGroupDefinitions = None
    __modelGroupDefinitions = None
    __attributeDeclarations = None
    __elementDeclarations = None
    __notationDeclarations = None
    __annotations = None

    def __mapForNamedType (self, nt):
        if self.NT_type == nt:
            return self.__typeDefinitions
        if self.NT_attributeGroup == nt:
            return self.__attributeGroupDefinitions
        if self.NT_modelGroup == nt:
            return self.__modelGroupDefinitions
        if self.NT_attribute == nt:
            return self.__attributeDeclarations
        if self.NT_element == nt:
            return self.__elementDeclarations
        if self.NT_notation == nt:
            return self.__notationDeclarations
        raise LogicError('Invalid named type 0x02x' % (nt,))

    __unresolvedDefinitions = None

    # Default values for standard recognized schema attributes
    __attributeMap = { 'attributeFormDefault' : 'unqualified'
                     , 'elementFormDefault' : 'unqualified'
                     , 'blockDefault' : ''
                     , 'finalDefault' : ''
                     , 'id' : None
                     , 'targetNamespace' : None
                     , 'version' : None
                     # , 'xml:lang' : None
                     } 

    def _setAttributeFromDOM (self, attr):
        self.__attributeMap[attr.name] = attr.nodeValue
        return self

    def schemaHasAttribute (self, attr_name):
        return self.__attributeMap.has_key(attr_name)

    def schemaAttribute (self, attr_name):
        return self.__attributeMap[attr_name]

    def __init__ (self, *args, **kw):
        super(Schema, self).__init__(*args, **kw)
        self.__annotations = [ ]

        self.__typeDefinitions = { }
        self.__attributeGroupDefinitions = { }
        self.__modelGroupDefinitions = { }
        self.__attributeDeclarations = { }
        self.__elementDeclarations = { }
        self.__notationDeclarations = { }

        self.__unresolvedDefinitions = []

    def _queueForResolution (self, std):
        """Invoked to note that a component may have unresolved references.

        Newly created named components are unresolved, as are
        components which, in the course of resolution, are found to
        depend on another unresolved component.
        """
        assert isinstance(std, _Resolvable_mixin)
        self.__unresolvedDefinitions.append(std)
        return std

    def __replaceUnresolvedDefinition (self, existing_def, replacement_def):
        assert existing_def in self.__unresolvedDefinitions
        self.__unresolvedDefinitions.remove(existing_def)
        assert replacement_def not in self.__unresolvedDefinitions
        assert isinstance(replacement_def, _Resolvable_mixin)
        self.__unresolvedDefinitions.append(replacement_def)
        return replacement_def

    def _resolveDefinitions (self):
        """Loop until all components associated with a name are
        sufficiently defined."""
        while self.__unresolvedDefinitions:
            # Save the list of unresolved TDs, reset the list to
            # capture any new TDs defined during resolution (or TDs
            # that depend on an unresolved type), and attempt the
            # resolution for everything that isn't resolved.
            unresolved = self.__unresolvedDefinitions
            self.__unresolvedDefinitions = []
            for std in unresolved:
                std._resolve(self)
            if self.__unresolvedDefinitions == unresolved:
                # This only happens if we didn't code things right, or
                # the schema actually has a circular dependency in
                # some named component.
                failed_components = []
                for d in self.__unresolvedDefinitions:
                    if isinstance(d, _NamedComponent_mixin):
                        failed_components.append('%s named %s' % (d.__class__.__name__, d.name()))
                    else:
                        failed_components.append('Anonymous %s' % (d.__class__.__name__,))
                raise LogicError('Infinite loop in resolution:\n  %s' % ("\n  ".join(failed_components),))
        self.__unresolvedDefinitions = None
        return self

    def _addAnnotation (self, annotation):
        self.__annotations.append(annotation)
        return annotation

    def _addNamedComponent (self, nc):
        if not isinstance(nc, _NamedComponent_mixin):
            raise LogicError('Attempt to add unnamed %s instance to dictionary' % (nc.__class__,))
        if nc.ncName() is None:
            raise LogicError('Attempt to add anonymous component to dictionary: %s', (nc.__class__,))
        #print 'Adding %s as %s' % (nc.__class__.__name__, nc.name())
        if isinstance(nc, (SimpleTypeDefinition, ComplexTypeDefinition)):
            return self.__addTypeDefinition(nc)
        if isinstance(nc, AttributeGroupDefinition):
            return self.__addAttributeGroupDefinition(nc)
        if isinstance(nc, AttributeDeclaration):
            return self.__addAttributeDeclaration(nc)
        if isinstance(nc, ModelGroupDefinition):
            return self.__addModelGroupDefinition(nc)
        if isinstance(nc, ElementDeclaration):
            return self.__addElementDeclaration(nc)
        if isinstance(nc, NotationDeclaration):
            return self.__addNotationDeclaration(nc)
        raise IncompleteImplementationError('No support to record named component of type %s' % (nc.__class__,))

    def __addTypeDefinition (self, td):
        local_name = td.ncName()
        old_td = self.__typeDefinitions.get(local_name, None)
        if old_td is not None:
            # @todo validation error if old_td is not a built-in
            if isinstance(td, ComplexTypeDefinition) != isinstance(old_td, ComplexTypeDefinition):
                raise SchemaValidationError('Name %s used for both simple and complex types' % (td.name(),))
            # Copy schema-related information from the new definition
            # into the old one, and continue to use the old one.
            td = self.__replaceUnresolvedDefinition(td, old_td._setFromInstance(td))
        else:
            self.__typeDefinitions[local_name] = td
        assert td is not None
        return td
    
    def _typeDefinitions (self):
        return self.__typeDefinitions.values()

    def _lookupTypeDefinition (self, local_name):
        return self.__typeDefinitions.get(local_name, None)

    def __addAttributeGroupDefinition (self, agd):
        assert isinstance(agd, AttributeGroupDefinition)
        local_name = agd.ncName()
        old_agd = self.__attributeGroupDefinitions.get(local_name, None)
        if old_agd is not None:
            raise SchemaValidationError('Name %s used for multiple attribute group definitions' % (local_name,))
        self.__attributeGroupDefinitions[local_name] = agd
        return agd

    def _lookupAttributeGroupDefinition (self, local_name):
        return self.__attributeGroupDefinitions.get(local_name, None)

    def _attributeGroupDefinitions (self):
        return self.__attributeGroupDefinitions.values()

    def __addModelGroupDefinition (self, ad):
        assert isinstance(ad, ModelGroupDefinition)
        local_name = ad.ncName()
        #print 'Defining group %s' % (local_name,)
        old_ad = self.__modelGroupDefinitions.get(local_name, None)
        if old_ad is not None:
            raise SchemaValidationError('Name %s used for multiple groups' % (local_name,))
        self.__modelGroupDefinitions[local_name] = ad
        return ad

    def _lookupModelGroupDefinition (self, local_name):
        return self.__modelGroupDefinitions.get(local_name, None)

    def _modelGroupDefinitions (self):
        return self.__modelGroupDefinitions.values()

    def __addAttributeDeclaration (self, ad):
        assert isinstance(ad, AttributeDeclaration)
        local_name = ad.ncName()
        old_ad = self.__attributeDeclarations.get(local_name, None)
        if old_ad is not None:
            raise SchemaValidationError('Name %s used for multiple attribute declarations' % (local_name,))
        self.__attributeDeclarations[local_name] = ad
        return ad

    def _lookupAttributeDeclaration (self, local_name):
        return self.__attributeDeclarations.get(local_name, None)

    def _attributeDeclarations (self):
        return self.__attributeDeclarations.values()

    def __addElementDeclaration (self, ed):
        assert isinstance(ed, ElementDeclaration)
        local_name = ed.ncName()
        #print 'Defining element %s' % (local_name,)
        old_ed = self.__elementDeclarations.get(local_name, None)
        if old_ed is not None:
            raise SchemaValidationError('Name %s used for multiple elements' % (local_name,))
        self.__elementDeclarations[local_name] = ed
        return ed

    def _lookupElementDeclaration (self, local_name):
        return self.__elementDeclarations.get(local_name, None)

    def _elementDeclarations (self):
        return self.__elementDeclarations.values()

    def __addNotationDeclaration (self, nd):
        assert isinstance(nd, NotationDeclaration)
        local_name = nd.ncName()
        #print 'Defining notation %s' % (local_name,)
        old_nd = self.__notationDeclarations.get(local_name, None)
        if old_nd is not None:
            raise SchemaValidationError('Name %s used for multiple notations' % (local_name,))
        self.__notationDeclarations[local_name] = nd
        return nd

    def _lookupNotationDeclaration (self, local_name):
        return self.__notationDeclarations.get(local_name, None)

    def _notationDeclarations (self):
        return self.__notationDeclarations.values()

    def _lookupNamedComponent (self, ncname, component_type):
        return self.__mapForNamedType(component_type).get(ncname, None)
