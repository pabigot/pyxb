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

"""Classes corresponding to W3C XML Schema components.

Class names and behavior should conform to the schema components described in
http://www.w3.org/TR/xmlschema-1/.  References to sections in the
documentation of this module generally refers to that document.

Each class has a CreateFromDOM class method that creates an instance and
initializes it from a DOM node.  Only the Wildcard, Particle, and ModelGroup
components are created from non-DOM sources.

@group Mixins: *_mixin
@group Ur Type Specializations: *UrType*
@group Utilities: _PluralityData, _ImportElementInformationItem

"""

import pyxb
import pyxb.xmlschema
from xml.dom import Node
import xml.dom
import types

from pyxb.binding import basis
from pyxb.binding import datatypes
from pyxb.binding import facets
from pyxb.utils.domutils import *
import copy
import urllib2

# Make it easier to check node names in the XMLSchema namespace
from pyxb.namespace import XMLSchema as xsd

class _SchemaComponent_mixin (pyxb.namespace._ComponentDependency_mixin):
    """A mix-in that marks the class as representing a schema component.

    This exists so that we can determine the owning schema for any
    component we encounter.  This is normally done at construction
    time by passing a schema=val parameter to the constructor.  
    """

    # The namespace context for this schema: where it looks things up,
    # where it puts things it createas, the in-scope namespace
    # declarations, etc.  Must be defined for all but the most trivial
    # components, so in fact we require it of everything.
    __namespaceContext = None
    def _namespaceContext (self):
        return self.__namespaceContext

    # The name by which this component is known within the binding
    # module.  This is in component rather than _NamedComponent_mixin
    # because some unnamed components (like ModelGroup and Wildcard)
    # have Python objects to represent them.
    __nameInBinding = None

    # The schema component that owns this.  If None, the component is
    # owned directly by the schema.
    __owner = None

    # The schema components owned by this component.
    __ownedComponents = None

    def _context (self):
        """The context within which element and attribute references are
        looked up."""
        return self.__context
    __context = None

    def _scope (self):
        """The context into which declarations in or subordinate to this nodeare placed."""
        return self.__scope
    __scope = None

    def _scopeIsIndeterminate (self):
        """Return True iff nobody has defined a scope for this node."""
        return _ScopedDeclaration_mixin.ScopeIsIndeterminate(self._scope())

    def _setScope (self, ctd):
        """Set the scope of this instance after construction.

        This should only be invoked on cloned declarations belonging
        to a group and being incorporated into a complex type
        definition."""
        assert self.__cloneSource is not None
        assert isinstance(self, _ScopedDeclaration_mixin)
        assert isinstance(ctd, ComplexTypeDefinition)
        assert self._scopeIsIndeterminate()
        self.__scope = ctd
        return self._recordInScope()

    def __init__ (self, *args, **kw):
        self.__ownedComponents = set()
        self.__scope = kw.get('scope')
        self.__context = kw.get('context')
        self.__namespaceContext = kw.get('namespace_context')
        if self.__namespaceContext is None:
            node = kw.get('node')
            if node is None:
                raise pyxb.LogicError('Schema component constructor must be given namespace_context or node')
            self.__namespaceContext = pyxb.namespace.NamespaceContext.GetNodeContext(node)
        if self.__namespaceContext is None:
            raise pyxb.LogicError('No namespace_context for schema component')

        super(_SchemaComponent_mixin, self).__init__(*args, **kw)
        self._namespaceContext().targetNamespace()._associateComponent(self)

        self._setOwner(kw.get('owner'))

    def _dissociateFromNamespace (self):
        """Dissociate this component from its owning namespace.  This should
        only be done whwen there are no other references to the component, and
        you want to ensure it does not appear in the model."""
        self._namespaceContext().targetNamespace()._replaceComponent(self, None)
        return self

    def _setOwner (self, owner):
        if owner is not None:
            assert (self.__owner is None) or (self.__owner == owner)
            self.__owner = owner
            owner.__ownedComponents.add(self)
        return self

    def owner (self): return self.__owner

    # A reference to the instance from which this instance was cloned.
    __cloneSource = None

    def _cloneSource (self):
        """The source component from which this is a clone.

        Returns None if this is not a clone."""
        return self.__cloneSource

    # A set of references to all instances that are clones of this one.
    __clones = None

    def _clones (self):
        """The set of instances cloned from this component.

        Returns None if no instances have been cloned from this."""
        return self.__clones

    def _resetClone_csc (self):
        """Virtual method to clear whatever attributes should be reset
        in a cloned component.

        This instance should be an instance created by copy.copy().

        The implementation in this class clears the owner and
        dependency relations.

        Returns self.
        """
        assert self.__cloneSource is not None
        self.__owner = None
        self.__ownedComponents = set()
        self.__clones = None
        assert self.__nameInBinding is None
        self._namespaceContext().targetNamespace()._associateComponent(self)
        return getattr(super(_SchemaComponent_mixin, self), '_resetClone_csc', lambda *args, **kw: self)()

    def _clone (self):
        """Create a copy of this instance suitable for adoption by
        some other component.
        
        This is used for things like creating a locally-scoped
        declaration from a group declaration."""

        # We only care about cloning declarations, and they should
        # have an unassigned scope.  However, we do clone
        # non-declarations that contain cloned declarations.
        assert (not isinstance(self, _ScopedDeclaration_mixin)) or self._scopeIsIndeterminate()
        if isinstance(self, pyxb.namespace._Resolvable_mixin):
            assert self.isResolved()

        that = copy.copy(self)
        that.__cloneSource = self
        if self.__clones is None:
            self.__clones = set()
        self.__clones.add(that)
        that._resetClone_csc()
        if isinstance(that, pyxb.namespace._Resolvable_mixin):
            assert that.isResolved()
        return that

    def isTypeDefinition (self):
        """Return True iff this component is a simple or complex type
        definition."""
        return isinstance(self, (SimpleTypeDefinition, ComplexTypeDefinition))

    def isUrTypeDefinition (self):
        """Return True iff this component is a simple or complex type
        definition."""
        return isinstance(self, (_SimpleUrTypeDefinition, _UrTypeDefinition))

    def bestNCName (self):
        """Return the name of this component, as best it can be
        determined.

        For example, ModelGroup instances will be named by their
        ModelGroupDefinition, if available.  Returns None if no name
        can be inferred."""
        if isinstance(self, _NamedComponent_mixin):
            return self.name()
        if isinstance(self, ModelGroup):
            agd = self.modelGroupDefinition()
            if agd is not None:
                return agd.name()
        return None

    def nameInBinding (self):
        """Return the name by which this component is known in the XSD
        binding.  NB: To support builtin datatypes,
        SimpleTypeDefinitions with an associated pythonSupport class
        initialize their binding name from the class name when the
        support association is created."""
        return self.__nameInBinding

    def setNameInBinding (self, name_in_binding):
        """Set the name by which this component shall be known in the XSD binding."""
        self.__nameInBinding = name_in_binding
        return self

    def _setBuiltinFromInstance (self, other):
        """Override fields in this instance with those from the other.

        Post-extended; description in leaf implementation in
        ComplexTypeDefinition and SimpleTypeDefinition."""
        assert self != other
        super_fn = getattr(super(_SchemaComponent_mixin, self), '_setBuiltinFromInstance', lambda *args, **kw: None)
        super_fn(other)
        # The only thing we update is the binding name, and that only if it's new.
        if self.__nameInBinding is None:
            self.__nameInBinding = other.__nameInBinding
        return self

class _Singleton_mixin (pyxb.cscRoot):
    """This class is a mix-in which guarantees that only one instance
    of the class will be created.  It is used to ensure that the
    ur-type instances are pointer-equivalent even when unpickling.
    See ComplexTypeDefinition.UrTypeDefinition()."""
    def __new__ (cls, *args, **kw):
        singleton_property = '_%s__singleton' % (cls.__name__,)
        if not (singleton_property in cls.__dict__):
            setattr(cls, singleton_property, object.__new__(cls, *args, **kw))
        return cls.__dict__[singleton_property]

class _Annotated_mixin (pyxb.cscRoot):
    """Mix-in that supports an optional single annotation that describes the component.

    Most schema components have annotations.  The ones that don't are
    AttributeUse, Particle, and Annotation.  ComplexTypeDefinition and
    Schema support multiple annotations, so do not mix-in this class."""

    # Optional Annotation instance
    __annotation = None

    def __init__ (self, *args, **kw):
        super(_Annotated_mixin, self).__init__(*args, **kw)
        self.__annotation = kw.get('annotation')

    def _annotationFromDOM (self, node):
        cn = LocateUniqueChild(node, 'annotation')
        if cn is not None:
            kw = { }
            if isinstance(self, _SchemaComponent_mixin):
                kw['owner'] = self
            self.__annotation = Annotation.CreateFromDOM(cn, **kw)

    def _setBuiltinFromInstance (self, other):
        """Override fields in this instance with those from the other.

        Post-extended; description in leaf implementation in
        ComplexTypeDefinition and SimpleTypeDefinition."""
        assert self != other
        super_fn = getattr(super(_Annotated_mixin, self), '_setBuiltinFromInstance', lambda *args, **kw: None)
        super_fn(other)
        # @todo: make this a copy?
        self.__annotation = other.__annotation
        return self

    def annotation (self):
        return self.__annotation

class _NamedComponent_mixin (pyxb.cscRoot):
    """Mix-in to hold the name and targetNamespace of a component.

    The name may be None, indicating an anonymous component.  The
    targetNamespace is never None, though it could be an empty namespace.  The
    name and targetNamespace values are immutable after creation.

    This class overrides the pickling behavior: when pickling a Namespace,
    objects that do not belong to that namespace are pickled as references,
    not as values.  This ensures the uniqueness of objects when multiple
    namespace definitions are pre-loaded.

    This class must follow L{_SchemaComponent_mixin} in the MRO.
    """

    def name (self):
        """Name of the component within its scope or namespace.

        This is an NCName.  The value isNone if the component is
        anonymous.  The attribute is immutable after the component is
        created creation."""
        return self.__name
    __name = None

    def isAnonymous (self):
        """Return true iff this instance is locally scoped (has no name)."""
        return self.__name is None

    def targetNamespace (self):
        """The targetNamespace of a componen.

        This is None, or a reference to a Namespace in which the
        component is declared (either as a global or local to one of
        the namespace's complex type definitions).  This is immutable
        after creation.
        """
        return self.__targetNamespace
    __targetNamespace = None
    
    def expandedName (self):
        """Return the L{pyxb.namespace.ExpandedName} of this object."""
        return pyxb.namespace.ExpandedName(self.targetNamespace(), self.name())

    def __new__ (cls, *args, **kw):
        """Pickling support.

        Normally, we just create a new instance of this class.
        However, if we're unpickling a reference in a loadable schema,
        we need to return the existing component instance by looking
        up the name in the component map of the desired namespace.  We
        can tell the difference because no normal constructors that
        inherit from this have positional arguments; only invocations
        by unpickling with a value returned in __getnewargs__ do.

        This does require that the dependent namespace already have
        been validated (or that it be validated here).  That shouldn't
        be a problem, except for the dependency loop resulting from
        use of xml:lang in the XMLSchema namespace.  For that issue,
        see pyxb.namespace._XMLSchema.
        """

        if 0 == len(args):
            rv = super(_NamedComponent_mixin, cls).__new__(cls)
            return rv
        ( expanded_name_tuple, scope, icls ) = args
        (uri, ncname) = expanded_name_tuple
        ns = pyxb.namespace.NamespaceForURI(uri)

        if ns is None:
            # This shouldn't happen: it implies somebody's unpickling
            # a schema that includes references to components in a
            # namespace that was not associated with the schema.
            print 'URI %s ncname %s scope %s icls %s' % args
            raise pyxb.IncompleteImplementationError('Unable to resolve namespace %s in external reference' % (uri,))
        # Explicitly validate here: the lookup operations won't do so,
        # but will abort if the namespace hasn't been validated yet.
        ns.validateComponentModel()
        #print 'Need to lookup %s in %s' % (ncname, scope)
        if isinstance(scope, tuple):
            ( scope_uri, scope_ncname ) = scope
            # Expect following to fail when we test qualified form defaults
            assert uri == scope_uri
            scope_ctd = ns.typeDefinitions().get(scope_ncname)
            if scope_ctd is None:
                raise pyxb.SchemaValidationError('Unable to resolve local scope %s in %s' % (scope_ncname, scope_uri))
            if issubclass(icls, AttributeDeclaration):
                rv = scope_ctd.lookupScopedAttributeDeclaration(expanded_name)
            elif issubclass(icls, ElementDeclaration):
                rv = scope_ctd.lookupScopedElementDeclaration(expanded_name)
            else:
                raise pyxb.IncompleteImplementationError('Local scope reference lookup not implemented for type %s searching %s in %s' % (icls, ncname, uri))
            if rv is None:
                raise pyxb.SchemaValidationError('Unable to resolve local %s as %s in %s in %s' % (ncname, icls, scope_ncname, uri))
        # @todo WRONG WRONG WRONG: Not the right thing for indeterminate
        elif (_ScopedDeclaration_mixin.SCOPE_global == scope) or _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope):
            #assert not _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope)
            if (issubclass(icls, SimpleTypeDefinition) or issubclass(icls, ComplexTypeDefinition)):
                rv = ns.typeDefinitions().get(ncname)
            elif issubclass(icls, AttributeGroupDefinition):
                rv = ns.attributeGroupDefinitions().get(ncname)
            elif issubclass(icls, ModelGroupDefinition):
                rv = ns.modelGroupDefinitions().get(ncname)
            elif issubclass(icls, AttributeDeclaration):
                rv = ns.attributeDeclarations().get(ncname)
            elif issubclass(icls, ElementDeclaration):
                rv = ns.elementDeclarations().get(ncname)
            elif issubclass(icls, IdentityConstraintDefinition):
                rv = ns.identityConstraintDefinitions().get(ncname)
            else:
                raise pyxb.IncompleteImplementationError('Reference lookup not implemented for type %s searching %s in %s' % (icls, ncname, uri))
            if rv is None:
                raise pyxb.SchemaValidationError('Unable to resolve %s as %s in %s' % (ncname, icls, uri))
        elif _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope):
            print 'WARNING: Unable to resolve %s in indeterminate scope' % (ncname,)
            rv = None
        else:
            raise pyxb.IncompleteImplementationError('Unable to resolve reference %s in scope %s in %s' % (ncname, scope, uri))
        #print 'Returning %s' % (rv,)
        return rv

    def __init__ (self, *args, **kw):
        assert 0 == len(args)
        name = kw.get('name')
        # Must be None or a valid NCName
        assert (name is None) or (0 > name.find(':'))
        self.__name = name
        
        # Target namespace is taken from the context, unless somebody
        # overrides it (as is done for local declarations if the form is
        # unqualified).
        self.__targetNamespace = kw.get('target_namespace', self._namespaceContext().targetNamespace())

        # Do parent invocations after we've set the name: they might need it.
        super(_NamedComponent_mixin, self).__init__(*args, **kw)
            
    def isNameEquivalent (self, other):
        """Return true iff this and the other component share the same name and target namespace.
        
        Anonymous components are inherently name inequivalent."""
        # Note that unpickled objects 
        return (not self.isAnonymous()) and (self.expandedName() == other.expandedName())

    def isTypeEquivalent (self, other):
        """Return True iff this and the other component have matching types.

        For now, this uses name equivalence within types.  In the future,
        structural equivalence may be used."""
        return (type(self) == type(other)) and self.isNameEquivalent(other)

    def __pickleAsReference (self):
        if self.targetNamespace() is None:
            return False
        # Get the namespace we're pickling.  If the namespace is None,
        # we're not pickling; we're probably cloning, and in that case
        # we don't want to use the reference state encoding.
        pickling_namespace = pyxb.namespace.Namespace.PicklingNamespace()
        if pickling_namespace is None:
            return False
        if pickling_namespace == self.targetNamespace():
            return False
        if self.isAnonymous():
            raise pyxb.LogicError('Unable to pickle reference to unnamed object %s in %s: %s' % (self.name(), self.targetNamespace().uri(), object.__str__(self)))
        return True

    def __getstate__ (self):
        if self.__pickleAsReference():
            # NB: This instance may be a scoped declaration, but in
            # this case (unlike getnewargs) we don't care about trying
            # to look up a previous instance, so we don't need to
            # encode the scope in the reference tuple.
            return self.expandedName().uriTuple()
        if self.targetNamespace() is None:
            # The only internal named objects that should exist are
            # ones that have a non-global scope (including those with
            # absent scope).
            # @todo: this is wrong for schema that are not bound to a
            # namespace, unless we use an unbound Namespace instance
            assert isinstance(self, _ScopedDeclaration_mixin)
            assert self.SCOPE_global != self.scope()
            # NOTE: The name of the scope may be None.  This is not a
            # problem unless somebody tries to extend or restrict the
            # scope type, which at the moment I'm thinking is
            # impossible for anonymous types.  If it isn't, we're
            # gonna need some other sort of ID, like a UUID associated
            # with the anonymous class at the time it's written to the
            # preprocessed schema file.
        return self.__dict__

    def __getnewargs__ (self):
        """Pickling support.

        If this instance is being pickled as a reference, provide the
        arguments that are necessary so that the unpickler can locate
        the appropriate component rather than create a duplicate
        instance."""

        if self.__pickleAsReference ():
            scope = self._scope()
            if isinstance(self, _ScopedDeclaration_mixin):
                # If scope is global, we can look it up in the namespace.
                # If scope is indeterminate, this must be within a group in
                # another namespace.  Why are we serializing it?
                # If scope is local, provide the namespace and name of
                # the type that holds it
                if self.SCOPE_global == self.scope():
                    pass
                elif isinstance(self.scope(), ComplexTypeDefinition):
                    scope = self.scope().expandedName().uriTuple()
                elif self._scopeIsIndeterminate():
                    # This is actually a serious problem, but only shows up
                    # when one schema imports another that has a model group
                    # (or probably attribute group) definition.  For some
                    # reason, the first schema has a reference to the
                    # definition (rather than the scope-adapted clones), and
                    # wants to serialize it.  I haven't yet figured out where
                    # that definition comes from, or how to remove it.
                    print 'Indeterminate scope for %s parentage:' % (self,)
                    owner = self.owner()
                    while owner is not None:
                        print ' %s' % (owner,)
                        owner = owner.owner()
                    assert False
            rv = ( self.expandedName().uriTuple(), scope, self.__class__ )
            return rv
        return ()

    def __setstate__ (self, state):
        if isinstance(state, tuple):
            # We don't actually have to set any state here; we just
            # make sure that we resolved to an already-configured
            # instance.
            assert self.targetNamespace() is not None
            assert self.targetNamespace().uri() == state[0]
            assert self.name() == state[1]
            return
        self.__dict__.update(state)
            
class _ValueConstraint_mixin (pyxb.cscRoot):
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

    def default (self):
        """If this instance constraints a default value, return that
        value; otherwise return None."""
        if not isinstance(self.__valueConstraint, tuple):
            return None
        if self.VC_default != self.__valueConstraint[1]:
            return None
        return self.__valueConstraint[0]

    def fixed (self):
        """If this instance constraints a fixed value, return that
        value; otherwise return None."""
        if not isinstance(self.__valueConstraint, tuple):
            return None
        if self.VC_fixed != self.__valueConstraint[1]:
            return None
        return self.__valueConstraint[0]

    def _valueConstraintFromDOM (self, node):
        aval = NodeAttribute(node, 'default')
        if aval is not None:
            self.__valueConstraint = (aval, self.VC_default)
            return self
        aval = NodeAttribute(node, 'fixed')
        if aval is not None:
            self.__valueConstraint = (aval, self.VC_fixed)
            return self
        self.__valueConstraint = None
        return self
        
class _ScopedDeclaration_mixin (pyxb.cscRoot):
    """Mix-in class for named components that have a scope.

    Scope is important when doing cross-namespace inheritance,
    e.g. extending or restricting a complex type definition that is
    from a different namespace.  In this case, we will need to retain
    a reference to the external component when the schema is
    serialized.

    This is done in the pickling process by including the scope when
    pickling a component as a reference.  The scope is the
    SCOPE_global if global; otherwise, it is a tuple containing the
    external namespace URI and the NCName of the complex type
    definition in that namespace.  We assume that the complex type
    definition has global scope; otherwise, it should not have been
    possible to extend or restrict it.  (Should this be untrue, there
    are comments in the code about a possible solution.)

    @warning: This mix-in must follow L{_NamedComponent_mixin} in the C{mro}.
    """

    SCOPE_global = 'global'     #<<< Marker to indicate global scope
    XSCOPE_indeterminate = 'indeterminate' #<<< Marker to indicate scope has not been assigned

    @classmethod
    def IsValidScope (cls, value):
        return (cls.SCOPE_global == value) or isinstance(value, ComplexTypeDefinition)

    @classmethod
    def ScopeIsIndeterminate (cls, value):
        return (cls.XSCOPE_indeterminate == value)

    def _scopeIsCompatible (self, scope):
        """Return True if this scope currently assigned to this instance is compatible with the given scope.

        If either scope is indeterminate, presume they will ultimately be
        compatible.  Scopes that are equal are compatible, as is a local scope
        if this already has a global scope."""
        if self.ScopeIsIndeterminate(scope) or self.ScopeIsIndeterminate(self.scope()):
            return True
        if self.scope() == scope:
            return True
        return (self.SCOPE_global == self.scope()) and isinstance(scope, ComplexTypeDefinition)

    # The scope for the element.  Valid values are SCOPE_global or a
    # complex type definition.  None is an invalid value, but may
    # appear if scope is determined by an ancestor component.
    def scope (self):
        """The scope for the declaration.

        Valid values are SCOPE_global, or a complex type definition.
        A value of None means a non-global declaration that is not
        owned by a complex type definition.  These can only appear in
        attribute group definitions or model group definitions.

        @todo: For declarations in named model groups (viz., local
        elements that aren't references), the scope needs to be set by
        the owning complex type.
        """
        return self._scope()

    def __init__ (self, *args, **kw):
        super(_ScopedDeclaration_mixin, self).__init__(*args, **kw)
        assert 'scope' in kw
        assert kw['scope'] is not None
        # Note: This requires that the _NamedComponent_mixin have
        # already done its thing and recorded the scope.

        # Provide a back door to prevent this from being recorded (or, more
        # specifically, to prevent a collision with an alternative declaration
        # we know is already recorded).  For example, we do this when we don't
        # know whether we have a type violation with multiple local elements
        # with the same expanded name.
        if not kw.get('scope_inhibit_record', False):
            self._recordInScope()

    def _recordInScope (self):
        # Absent scope doesn't get recorded anywhere.  Global scope is
        # recorded in the namespace by somebody else.  Local scopes
        # are recorded here.
        if isinstance(self.scope(), ComplexTypeDefinition):
            self.scope()._recordLocalDeclaration(self)
        return self


class _PluralityData (types.ListType):
    """This class represents an abstraction of the set of documents conformant
    to a particle or particle term.

    The abstraction of a given document is a map from element declarations
    that can appear at the top level of the document to a boolean that is true
    iff there could be multiple instances of that element declaration at the
    top level of a valid document.  The abstraction of the set is a list of
    document abstractions.

    This information is used in binding generation to determine whether a
    field associated with a tag might need to hold multiple instances.
    """
    
    @classmethod
    def _MapUnion (self, map1, map2):
        """Given two maps, return an updated map indicating the unified
        plurality."""
        umap = { }
        for k in set(map1.keys()).union(map2.keys()):
            if k in map1:
                umap[k] = (k in map2) or map1[k]
            else:
                umap[k] = map2[k]
        return umap

    def nameBasedPlurality (self):
        """Return a map from expanded names to pairs consisting of a boolean
        representing the plurality of the aggregated name, and the element
        declaration with that name.

        Note that this requires cos-element-consistent to have been validated,
        and element declarations with the same expanded name to have been
        replaced with a single element declaration."""

        name_plurality = { }
        name_types = { }
        for pdm in self:
            npdm = { }
            for (ed, v) in pdm.items():
                if isinstance(ed, ElementDeclaration):
                    tag = ed.expandedName()
                    name_types.setdefault(tag, ed)
                    # Should only be one with that name
                    assert name_types[tag] == ed
                    npdm[tag] = npdm.get(tag, False) or v
                elif isinstance(ed, Wildcard):
                    pass
                else:
                    raise pyxb.LogicError('Unexpected plurality index %s' % (ed,))
            name_plurality = self._MapUnion(name_plurality, npdm)
        rv = { }
        for (name, ed) in name_types.items():
            rv[name] = ( name_plurality[name], ed )
        return rv

    def __fromModelGroup (self, model_group):
        # Start by collecting the data for each of the particles.
        pdll = [ _PluralityData(_p) for _p in model_group.particles() ]
        if (ModelGroup.C_CHOICE == model_group.compositor()):
            # Plurality for choice is simply any of the pluralities of the particles.
            for pd in pdll:
                union_map = { }
                for pdm in pd:
                    union_map = self._MapUnion(union_map, pdm)
                self.append(union_map)
        elif ((ModelGroup.C_SEQUENCE == model_group.compositor()) or (ModelGroup.C_ALL == model_group.compositor())):
            # Sequence means all of them, in all their glory
            # All is treated the same way
            # Essentially this is a pointwise OR of the pluralities of the particles.
            if 0 < len(pdll):
                new_pd = pdll.pop()
                for pd in pdll:
                    stage_pd = [ ]
                    for pdm1 in new_pd:
                        for pdm2 in pd:
                            stage_pd.append(self._MapUnion(pdm1, pdm2))
                    new_pd = stage_pd
                self.extend(new_pd)
        else:
            raise pyxb.LogicError('Unrecognized compositor value %s' % (model_group.compositor(),))

    def __fromParticle (self, particle):
        assert particle.isResolved()
        pd = particle.term().pluralityData()

        # If the particle can't appear at all, there are no results.
        if 0 == particle.maxOccurs():
            return

        # If the particle can only occur once, it has no effect on the
        # pluralities; use the term to identify them
        if 1 == particle.maxOccurs():
            self.__setFromComponent(particle.term())
            return
        
        # If there are multiple alternatives, assume they are all
        # taken.  Do this by creating a map that treats every possible
        # element as appearing multiple times.
        true_map = {}
        pd = _PluralityData(particle.term())
        while 0 < len(pd):
            pdm = pd.pop()
            [ true_map.setdefault(_k, True) for _k in pdm.keys() ]
        self.append(true_map)

    def __setFromComponent (self, component=None):
        del self[:]
        if isinstance(component, ElementDeclaration):
            assert component.isResolved()
            self.append( { component: False } )
        elif isinstance(component, ModelGroup):
            self.__fromModelGroup(component)
        elif isinstance(component, Particle):
            self.__fromParticle(component)
        elif isinstance(component, Wildcard):
            self.append( { component: False } )
        elif component is not None:
            raise pyxb.NotImplementedError("No support for plurality of component type %s" % (type(component),))

    def __init__ (self, component=None):
        super(_PluralityData, self).__init__()
        self.__setFromComponent(component)

class _AttributeWildcard_mixin (pyxb.cscRoot):
    """Support for components that accept attribute wildcards.

    That is AttributeGroupDefinition and ComplexType.  The
    calculations of the appropriate wildcard are sufficiently complex
    that they need to be abstracted out to a mix-in class."""

    # Optional wildcard that constrains attributes
    __attributeWildcard = None

    def attributeWildcard (self):
        """Return the Wildcard component associated with attributes of
        this instance, or None if attribute wildcards are not present
        in the instance."""
        return self.__attributeWildcard

    def _setAttributeWildcard (self, attribute_wildcard):
        """Set the attribute wildcard property for this instance."""
        assert (attribute_wildcard is None) or isinstance(attribute_wildcard, Wildcard)
        self.__attributeWildcard = attribute_wildcard
        return self

    def _attributeRelevantChildren (self, node_list):
        """Return the nodes that are relevant for attribute processing.

        The input is a schema, and a sequence of nodes found in the
        document that defines the schema.

        A successful return value is a 3-element tuple.  The first
        element is a list of DOM Nodes with nodeName attribute, the
        second a list of AttributeGroupDefinition instances, and the
        third a single DOM Node with nodeName anyAttribute.  The third
        element will be None if there is no anyAttribute child of the
        given node.

        The return value will be None if any of the children involve a
        reference to an unresolved component."""
        
        attributes = []
        attribute_groups = []
        any_attribute = None
        # Handle clauses 1 and 2 (common between simple and complex types)
        for node in node_list:
            if Node.ELEMENT_NODE != node.nodeType:
                continue
            if xsd.nodeIsNamed(node, 'attribute'):
                # Note: This attribute use instance may have use=prohibited
                attributes.append(node)
            elif xsd.nodeIsNamed(node, 'attributeGroup'):
                # This must be an attributeGroupRef
                agd_attr = NodeAttribute(node, 'ref')
                if agd_attr is None:
                    raise pyxb.SchemaValidationError('Require ref attribute on internal attributeGroup elements')
                agen = self._namespaceContext().interpretQName(agd_attr) 
                agd = agen.attributeGroupDefinition()
                if agd is None:
                    raise pyxb.SchemaValidationError('No attribute group definition %s in %s' % (agen.localName(), agen.namespace()))
                if not agd.isResolved():
                    return None
                attribute_groups.append(agd)
            elif xsd.nodeIsNamed(node, 'anyAttribute'):
                if any_attribute is not None:
                    raise pyxb.SchemaValidationError('Multiple anyAttribute children are not allowed')
                any_attribute = node
                
        return (attributes, attribute_groups, any_attribute)

    @classmethod
    def CompleteWildcard (cls, namespace_context, attribute_groups, any_attribute, local_wildcard):
        # Non-absent wildcard properties of attribute groups
        agd_wildcards = []
        for agd in attribute_groups:
            if agd.attributeWildcard() is not None:
                agd_wildcards.append(agd.attributeWildcard())
        agd_constraints = [ _agd.namespaceConstraint() for _agd in agd_wildcards ]

        # Clause 2.1
        if 0 == len(agd_wildcards):
            return local_wildcard

        if any_attribute is not None:
            # Clause 2.2.1
            return Wildcard(process_contents=local_wildcard.processContents(),
                            namespace_constraint=Wildcard.IntensionalIntersection(agd_constraints + [local_wildcard.namespaecConstraint()]),
                            annotation=local_wildcard.annotation(),
                            namespace_context=namespace_context)
        # Clause 2.2.2
        return Wildcard(process_contents=agd_wildcards[0].processContents(),
                        namespace_constraint=Wildcard.IntensionalIntersection(agd_constraints),
                        namespace_context=namespace_context)

class AttributeDeclaration (_SchemaComponent_mixin, _NamedComponent_mixin, pyxb.namespace._Resolvable_mixin, _Annotated_mixin, _ValueConstraint_mixin, _ScopedDeclaration_mixin):
    """An XMLSchema Attribute Declaration component.

    See http://www.w3.org/TR/xmlschema-1/index.html#cAttribute_Declarations
    """

    # The STD to which attribute values must conform
    __typeDefinition = None
    def typeDefinition (self):
        """The simple type definition to which an attribute value must
         conform."""
        return self.__typeDefinition

    def __init__ (self, *args, **kw):
        super(AttributeDeclaration, self).__init__(*args, **kw)
        assert 'scope' in kw

    def __str__ (self):
        if self.typeDefinition():
            return 'AD[%s:%s]' % (self.name(), self.typeDefinition().name())
        return 'AD[%s:?]' % (self.name(),)

    @classmethod
    def CreateBaseInstance (cls, name, target_namespace, std=None):
        """Create an attribute declaration component for a specified namespace."""
        bi = cls(name=name, namespace_context=target_namespace.initialNamespaceContext(), scope=_ScopedDeclaration_mixin.SCOPE_global)
        if std is not None:
            bi.__typeDefinition = std
        return bi

    # CFD:AD CFD:AttributeDeclaration
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create an attribute declaration from the given DOM node.

        wxs is a Schema instance within which the attribute is being
        declared.

        node is a DOM element.  The name must be one of ( 'all',
        'choice', 'sequence' ), and the node must be in the XMLSchema
        namespace.

        scope is the _ScopeDeclaration_mxin context into which the
        attribute declaration is placed.  It can be SCOPE_global, a
        complex type definition, or XSCOPE_indeterminate if this is an
        anonymous declaration within an attribute group.  It is a
        required parameter for this function.
        """
        
        scope = kw['scope']
        assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or _ScopedDeclaration_mixin.IsValidScope(scope)

        # Node should be an XMLSchema attribute node
        assert xsd.nodeIsNamed(node, 'attribute')

        name = NodeAttribute(node, 'name')

        # Implement per section 3.2.2
        if xsd.nodeIsNamed(node.parentNode, 'schema'):
            assert cls.SCOPE_global == scope
        elif NodeAttribute(node, 'ref') is None:
            # This is an anonymous declaration within an attribute use
            assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or isinstance(scope, ComplexTypeDefinition)
        else:
            raise pyxb.SchemaValidationError('Internal attribute declaration by reference')

        rv = cls(name=name, node=node, **kw)
        rv._annotationFromDOM(node)
        rv._valueConstraintFromDOM(node)
        rv.__domNode = node
        rv._queueForResolution()
        return rv

    def isResolved (self):
        return self.__typeDefinition is not None

    # res:AD res:AttributeDeclaration
    def _resolve (self):
        if self.isResolved():
            return self
        #print 'Resolving AD %s' % (self.name(),)
        node = self.__domNode

        st_node = LocateUniqueChild(node, 'simpleType')
        type_attr = NodeAttribute(node, 'type')
        if st_node is not None:
            self.__typeDefinition = SimpleTypeDefinition.CreateFromDOM(st_node, owner=self)
        elif type_attr is not None:
            # Although the type definition may not be resolved, *this* component
            # is resolved, since we don't look into the type definition for anything.
            type_en = self._namespaceContext().interpretQName(type_attr)
            self.__typeDefinition = type_en.typeDefinition()
            if self.__typeDefinition is None:
                self._queueForResolution()
                return self
            if not isinstance(self.__typeDefinition, SimpleTypeDefinition):
                raise pyxb.SchemaValidationError('Need %s to be a simple type' % (type_ln,))
        else:
            self.__typeDefinition = SimpleTypeDefinition.SimpleUrTypeDefinition()

        self.__domNode = None
        return self

    def _setBuiltinFromInstance (self, other):
        """Override fields in this instance with those from the other.

        This method is invoked only by Schema._addNamedComponent, and
        then only when a built-in type collides with a schema-defined
        type.  Material like facets is not (currently) held in the
        built-in copy, so the DOM information is copied over to the
        built-in STD, which is subsequently re-resolved.

        Returns self.
        """
        assert self != other
        assert self.isNameEquivalent(other)
        super(AttributeDeclaration, self)._setBuiltinFromInstance(other)
        assert self.name() is not None
        assert other.name() is not None

        # The other STD should be an unresolved schema-defined type.
        assert other.__typeDefinition is None
        assert other.__domNode is not None
        self.__domNode = other.__domNode

        # Mark this instance as unresolved so it is re-examined
        self.__typeDefinition = None
        return self

    def _dependentComponents_vx (self):
        """Implement base class method.

        AttributeDeclarations depend only on the type definition for their value.
        """
        return frozenset([self.__typeDefinition])

class AttributeUse (_SchemaComponent_mixin, pyxb.namespace._Resolvable_mixin, _ValueConstraint_mixin):
    """An XMLSchema Attribute Use component.

    See http://www.w3.org/TR/xmlschema-1/index.html#cAttribute_Use
    """

    # How this attribute can be used.  The component property
    # "required" is true iff the value is USE_required.
    __use = False

    USE_required = 0x01         #<<< The attribute is required
    USE_optional = 0x02         #<<< The attribute may or may not appear
    USE_prohibited = 0x04       #<<< The attribute must not appear
    def required (self): return self.USE_required == self.__use
    def prohibited (self): return self.USE_prohibited == self.__use

    # A reference to an AttributeDeclaration
    __attributeDeclaration = None
    def attributeDeclaration (self): return self.__attributeDeclaration

    # Define so superclasses can take keywords
    def __init__ (self, **kw):
        super(AttributeUse, self).__init__(**kw)

    def _dependentComponents_vx (self):
        """Implement base class method.

        Attribute uses depend only on their attribute declarations.
        """
        return frozenset([self.__attributeDeclaration])

    def matchingQNameMembers (self, au_set):
        """Return the subset of au_set for which the use names match this use."""

        # This use may be brand new, and temporary, and if we don't
        # resolve it now it may be thrown away and we'll loop forever
        # creating new instances that aren't resolved.
        if not self.isResolved():
            self._resolve()
        # If it's still not resolved, hold off, and indicate that the
        # caller should hold off too.
        if not self.isResolved():
            return None
        this_ad = self.attributeDeclaration()
        rv = set()
        for au in au_set:
            if not au.isResolved():
                return None
            that_ad = au.attributeDeclaration()
            if this_ad.isNameEquivalent(that_ad):
                rv.add(au)
        return rv

    # CFD:AU CFD:AttributeUse
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create an Attribute Use from the given DOM node.

        wxs is a Schema instance within which the attribute use is
        being defined.

        context is the _ScopeDeclaration_mixin context that is used to
        resolve attribute references.

        node is a DOM element.  The name must be 'attribute', and the
        node must be in the XMLSchema namespace.

        scope is the _ScopeDeclaration_mixin context into which any
        required anonymous attribute declaration is put.  This must be
        a complex type definition, or None if this use is in an
        attribute group.
        """

        context = kw['context']
        assert _ScopedDeclaration_mixin.IsValidScope(context)
        scope = kw['scope']
        assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or isinstance(scope, ComplexTypeDefinition)
        assert xsd.nodeIsNamed(node, 'attribute')
        rv = cls(node=node, **kw)
        rv.__use = cls.USE_optional
        use = NodeAttribute(node, 'use')
        if use is not None:
            if 'required' == use:
                rv.__use = cls.USE_required
            elif 'optional' == use:
                rv.__use = cls.USE_optional
            elif 'prohibited' == use:
                rv.__use = cls.USE_prohibited
            else:
                raise pyxb.SchemaValidationError('Unexpected value %s for attribute use attribute' % (use,))

        rv._valueConstraintFromDOM(node)
        rv.__domNode = node
        rv._queueForResolution()
        return rv

    def isResolved (self):
        return self.__attributeDeclaration is not None

    def _resolve (self):
        if self.isResolved():
            return self
        assert self.__domNode
        node = self.__domNode
        ref_attr = NodeAttribute(node, 'ref')
        if ref_attr is None:
            # Create an anonymous declaration.  Although this can
            # never be referenced, we need the right scope so when we
            # generate the binding we can place the attribute in the
            # correct type.  Is this true?
            kw = { }
            kw['owner'] = self
            kw['scope'] = self._scope()
            kw['target_namespace'] = self._resolvingSchema().targetNamespaceForNode(node, AttributeDeclaration)
            self.__attributeDeclaration = AttributeDeclaration.CreateFromDOM(node, **kw)
        else:
            ad_en = self._namespaceContext().interpretQName(ref_attr)
            self.__attributeDeclaration = ad_en.attributeDeclaration()
        if self.__attributeDeclaration is None:
            self._queueForResolution()
            return self
        # Although the attribute declaration definition may not be
        # resolved, *this* component is resolved, since we don't look
        # into the attribute declaration for anything.
        assert isinstance(self.__attributeDeclaration, AttributeDeclaration)
        self.__domNode = None
        return self

    def _adaptForScope (self, ctd):
        """Adapt this instance for the given complex type.

        If the attribute declaration for this instance has scope None,
        then it's part of an attribute group that was incorporated
        into the given CTD.  In that case, clone this instance and
        return the clone with its attribute declaration also set to a
        clone with proper scope."""
        assert self.isResolved()
        ad = self.__attributeDeclaration
        rv = self
        if ad.scope() is None:
            rv = self._clone()
            rv._setOwner(ctd)
            rv.__attributeDeclaration = ad._clone()
            rv.__attributeDeclaration._setOwner(rv)
            rv.__attributeDeclaration._setScope(ctd)
        return rv

    def __str__ (self):
        return 'AU[%s]' % (self.attributeDeclaration(),)


class ElementDeclaration (_SchemaComponent_mixin, _NamedComponent_mixin, pyxb.namespace._Resolvable_mixin, _Annotated_mixin, _ValueConstraint_mixin, _ScopedDeclaration_mixin):
    """An XMLSchema Element Declaration component.

    See http://www.w3.org/TR/xmlschema-1/index.html#cElement_Declarations
    """

    # Simple or complex type definition
    __typeDefinition = None
    def typeDefinition (self):
        """The simple or complex type to which the element value conforms."""
        return self.__typeDefinition
    def _typeDefinition (self, type_definition):
        """Set the type of the element."""
        self.__typeDefinition = type_definition
        return self

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

    SGE_none = 0                #<<< No substitution group exclusion specified
    SGE_extension = 0x01        #<<< Substitution by an extension of the base type
    SGE_restriction = 0x02      #<<< Substitution by a restriction of the base type
    SGE_substitution = 0x04     #<<< Substitution by replacement (?)

    # Subset of SGE marks formed by bitmask.  SGE_substitution is disallowed.
    __substitutionGroupExclusions = SGE_none

    # Subset of SGE marks formed by bitmask
    __disallowedSubstitutions = SGE_none

    __abstract = False
    def abstract (self): return self.__abstract

    # The containing component which provides the scope
    __ancestorComponent = None
    def ancestorComponent (self):
        """The containing component which will ultimately provide the
        scope.

        None if at the top level, or a ComplexTypeDefinition or a
        ModelGroup.  """
        return self.__ancestorComponent

    def pluralityData (self):
        """Return the plurality information for this component.

        An ElementDeclaration produces one instance of a single element."""
        return _PluralityData(self)

    def hasWildcardElement (self):
        """Return False, since element declarations are not wildcards."""
        return False

    def _dependentComponents_vx (self):
        """Implement base class method.

        Element declarations depend on the type definition of their
        content.  Note: The ancestor component depends on this
        component, not the other way 'round.
        """
        return frozenset([self.__typeDefinition])

    def __init__ (self, *args, **kw):
        super(ElementDeclaration, self).__init__(*args, **kw)

    def isPlural (self):
        """Element declarations are not multivalued in themselves."""
        return False

    # CFD:ED CFD:ElementDeclaration
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create an element declaration from the given DOM node.

        wxs is a Schema instance within which the element is being
        declared.

        scope is the _ScopeDeclaration_mixin context into which the
        element declaration is recorded.  It can be SCOPE_global, a
        complex type definition, or None in the case of elements
        declared in a named model group.

        node is a DOM element.  The name must be 'element', and the
        node must be in the XMLSchema namespace."""

        scope = kw['scope']
        assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or _ScopedDeclaration_mixin.IsValidScope(scope)

        # Node should be an XMLSchema element node
        assert xsd.nodeIsNamed(node, 'element')

        # Might be top-level, might be local
        name = NodeAttribute(node, 'name')
        if xsd.nodeIsNamed(node.parentNode, 'schema'):
            assert _ScopedDeclaration_mixin.SCOPE_global == scope
        elif NodeAttribute(node, 'ref') is None:
            # Scope may be None or a CTD.
            assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or isinstance(scope, ComplexTypeDefinition)
        else:
            raise pyxb.SchemaValidationError('Created reference as element declaration')
        
        rv = cls(name=name, node=node, **kw)
        rv._annotationFromDOM(node)
        rv._valueConstraintFromDOM(node)

        # Creation does not attempt to do resolution.  Queue up the newly created
        # whatsis so we can resolve it after everything's been read in.
        rv.__domNode = node
        rv._queueForResolution()
        
        return rv

    def isDeepResolved (self):
        return True

    def _adaptForScope (self, owner, scope):
        rv = self
        if (self._scopeIsIndeterminate()) and (scope is not None):
            if isinstance(scope, ComplexTypeDefinition):
                rv = scope.lookupScopedElementDeclaration(self.expandedName())
                if rv is not None:
                    assert rv.isResolved()
                    assert self.isResolved()
                    if not rv.typeDefinition().isTypeEquivalent(self.typeDefinition()):
                        raise pyxb.SchemaValidationError('Conflicting element declarations for %s' % (self.expandedName(),))
                    print 'Re-using existing scoped element'
                    return rv
            rv = self._clone()
            assert owner is not None
            rv._setOwner(owner)
            rv._setScope(scope)
        else:
            assert self._scopeIsCompatible(scope)
        return rv

    def isResolved (self):
        return self.__typeDefinition is not None

    # res:ED res:ElementDeclaration
    def _resolve (self):
        if self.isResolved():
            return self

        if self.scope() is None:
            print 'Not resolving unscoped ElementDeclaration %s' % (self.name(),)
            # DO NOT REQUEUE
            return self

        node = self.__domNode

        sg_attr = NodeAttribute(node, 'substitutionGroup')
        if sg_attr is not None:
            sg_en = self._namespaceContext().interpretQName(sg_attr)
            sga = sg_en.elementDeclaration()
            if sga is None:
                # print 'Holding off ED resolution, unrecognized substitution group %s' % (sg_en,)
                self._queueForResolution()
                return self
            if not sga.isResolved():
                print 'Not resolving, substitutiongroup %s unresolved' % (sg_en,)
                self._queueForResolution()
                return self
            self.__substitutionGroupAffiliation = sga
            
        identity_constraints = []
        for cn in node.childNodes:
            if (Node.ELEMENT_NODE == cn.nodeType) and xsd.nodeIsNamed(cn, 'key', 'unique', 'keyref'):
                identity_constraints.append(IdentityConstraintDefinition.CreateFromDOM(cn, owner=self, scope=self.scope()))
        self.__identityConstraintDefinitions = identity_constraints

        type_def = None
        td_node = LocateUniqueChild(node, 'simpleType')
        if td_node is not None:
            type_def = SimpleTypeDefinition.CreateFromDOM(td_node, owner=self)
        else:
            td_node = LocateUniqueChild(node, 'complexType')
            if td_node is not None:
                type_def = ComplexTypeDefinition.CreateFromDOM(td_node, scope=_ScopedDeclaration_mixin.XSCOPE_indeterminate, owner=self)
        if type_def is None:
            type_attr = NodeAttribute(node, 'type')
            if type_attr is not None:
                type_en = self._namespaceContext().interpretQName(type_attr)
                type_def = type_en.typeDefinition()
                if type_def is None:
                    #print 'Not resolving ED, missing %s %s' % type_qname
                    self._queueForResolution()
                    return self
            elif self.__substitutionGroupAffiliation is not None:
                type_def = self.__substitutionGroupAffiliation.typeDefinition()
            else:
                type_def = ComplexTypeDefinition.UrTypeDefinition()
        self._typeDefinition(type_def)

        attr_val = NodeAttribute(node, 'nillable')
        if attr_val is not None:
            self.__nillable = datatypes.boolean(attr_val)

        # @todo: disallowed substitutions, substitution group exclusions

        attr_val = NodeAttribute(node, 'abstract')
        if attr_val is not None:
            self.__abstract = datatypes.boolean(attr_val)
                
        self.__domNode = None
        return self

    def __str__ (self):
        if self.typeDefinition() is not None:
            return 'ED[%s:%s]' % (self.name(), self.typeDefinition().name())
        return 'ED[%s:?]' % (self.name(),)


class ComplexTypeDefinition (_SchemaComponent_mixin, _NamedComponent_mixin, pyxb.namespace._Resolvable_mixin, _Annotated_mixin, _AttributeWildcard_mixin):
    # The type resolved from the base attribute.
    __baseTypeDefinition = None
    def baseTypeDefinition (self):
        "The type resolved from the base attribute."""
        return self.__baseTypeDefinition

    DM_empty = 0                #<<< No derivation method specified
    DM_extension = 0x01         #<<< Derivation by extension
    DM_restriction = 0x02       #<<< Derivation by restriction

    # How the type was derived (a DM_* value)
    # (This field is used to identify unresolved definitions.)
    __derivationMethod = None
    def derivationMethod (self):
        """How the type was derived."""
        return self.__derivationMethod

    # Derived from the final and finalDefault attributes
    __final = DM_empty

    # Derived from the abstract attribute
    __abstract = False
    
    # A frozenset() of AttributeUse instances.
    __attributeUses = None
    def attributeUses (self):
        """A frozenset() of AttributeUse instances."""
        return self.__attributeUses

    # A map from NCNames to AttributeDeclaration instances that are
    # local to this type.
    __scopedAttributeDeclarations = None
    def lookupScopedAttributeDeclaration (self, expanded_name):
        """Find an attribute declaration with the given name that is local to this type.

        Returns None if there is no such local attribute declaration."""
        if self.__scopedAttributeDeclarations is None:
            return None
        return self.__scopedAttributeDeclarations.get(expanded_name)

    # A map from NCNames to ElementDeclaration instances that are
    # local to this type.
    __scopedElementDeclarations = None
    def lookupScopedElementDeclaration (self, expanded_name):
        """Find an element declaration with the given name that is local to this type.

        Returns None if there is no such local element declaration."""
        if self.__scopedElementDeclarations is None:
            return None
        return self.__scopedElementDeclarations.get(expanded_name)

    def _recordLocalDeclaration (self, decl):
        """Record the given declaration as being locally scoped in
        this type."""
        assert decl.scope() == self
        if isinstance(decl, ElementDeclaration):
            scope_map = self.__scopedElementDeclarations
        elif isinstance(decl, AttributeDeclaration):
            scope_map = self.__scopedAttributeDeclarations
        else:
            raise pyxb.LogicError('Unexpected instance of %s recording as local declaration' % (type(decl),))
        if decl.expandedName() in scope_map:
            raise pyxb.SchemaValidationError('Multiple definitions of %s as %s local to %s' % (decl.expandedName(), type(decl).__name__, self.expandedName()))
        scope_map[decl.expandedName()] = decl
        return self

    CT_EMPTY = 0                #<<< No content
    CT_SIMPLE = 1               #<<< Simple (character) content
    CT_MIXED = 2                #<<< Children may be elements or other (e.g., character) content
    CT_ELEMENT_ONLY = 3         #<<< Expect only element content.

    # Identify the sort of content in this type.
    __contentType = None
    def contentType (self):
        """Identify the sort of content in this type.

        Valid values are:
         - C{CT_EMPTY}
         - ( C{CT_SIMPLE}, a L{SimpleTypeDefinition} instance )
         - ( C{CT_MIXED}, a L{Particle} instance )
         - ( C{CT_ELEMENT_ONLY}, a L{Particle} instance )
        """
        return self.__contentType

    def contentTypeAsString (self):
        if self.CT_EMPTY == self.contentType():
            return 'EMPTY'
        ( tag, particle ) = self.contentType()
        if self.CT_SIMPLE == tag:
            return 'Simple [%s]' % (particle,)
        if self.CT_MIXED == tag:
            return 'Mixed [%s]' % (particle,)
        if self.CT_ELEMENT_ONLY == tag:
            return 'Element [%s]' % (particle,)
        raise pyxb.LogicError('Unhandled content type')

    # Derived from the block and blockDefault attributes
    __prohibitedSubstitutions = DM_empty

    # @todo: Extracted from children of various types
    __annotations = None
    
    def __init__ (self, *args, **kw):
        super(ComplexTypeDefinition, self).__init__(*args, **kw)
        self.__derivationMethod = kw.get('derivation_method')
        assert self._scopeIsIndeterminate()
        self.__scopedElementDeclarations = { }
        self.__scopedAttributeDeclarations = { }

    def hasWildcardElement (self):
        """Return True iff this type includes a wildcard element in
        its content model."""
        if self.CT_EMPTY == self.contentType():
            return False
        ( tag, particle ) = self.contentType()
        if self.CT_SIMPLE == tag:
            return False
        return particle.hasWildcardElement()

    def _setBuiltinFromInstance (self, other):
        """Override fields in this instance with those from the other.

        This method is invoked only by Schema._addNamedComponent, and
        then only when a built-in type collides with a schema-defined
        type.  Material like facets is not (currently) held in the
        built-in copy, so the DOM information is copied over to the
        built-in STD, which is subsequently re-resolved.

        Returns self.
        """
        assert self != other
        assert self.isNameEquivalent(other)
        super(ComplexTypeDefinition, self)._setBuiltinFromInstance(other)

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
        #if in_builtin_definition and (cls.__UrTypeDefinition is not None):
        #    raise pyxb.LogicError('Multiple definitions of UrType')
        if cls.__UrTypeDefinition is None:
            # NOTE: We use a singleton subclass of this class
            ns_ctx = pyxb.namespace.XMLSchema.initialNamespaceContext()
            bi = _UrTypeDefinition(name='anyType', namespace_context=ns_ctx, derivation_method=cls.DM_restriction, scope=_ScopedDeclaration_mixin.XSCOPE_indeterminate)

            # The ur-type is its own baseTypeDefinition
            bi.__baseTypeDefinition = bi

            # No constraints on attributes
            bi._setAttributeWildcard(Wildcard(namespace_context=ns_ctx, namespace_constraint=Wildcard.NC_any, process_contents=Wildcard.PC_lax))

            # There isn't anything to look up, but context is still global.
            # No declarations will be created, so use indeterminate scope to
            # be consistent with validity checks in Particle constructor.
            # Content is mixed, with elements completely unconstrained. @todo:
            # not associated with a schema (it should be)
            kw = { 'namespace_context' : ns_ctx
                 , 'context': _ScopedDeclaration_mixin.SCOPE_global
                 , 'scope': _ScopedDeclaration_mixin.XSCOPE_indeterminate }
            w = Wildcard(namespace_constraint=Wildcard.NC_any, process_contents=Wildcard.PC_lax, **kw)
            p = Particle(w, min_occurs=0, max_occurs=None, **kw)
            m = ModelGroup(compositor=ModelGroup.C_SEQUENCE, particles=[ p ], **kw)
            bi.__contentType = ( cls.CT_MIXED, Particle(m, **kw) )

            # No attribute uses
            bi.__attributeUses = set()

            # No constraints on extension or substitution
            bi.__final = cls.DM_empty
            bi.__prohibitedSubstitutions = cls.DM_empty

            bi.__abstract = False

            # Refer to it by name
            bi.setNameInBinding(bi.name())

            # The ur-type is always resolved
            bi.__derivationMethod = cls.DM_restriction

            cls.__UrTypeDefinition = bi
        return cls.__UrTypeDefinition

    def isBuiltin (self):
        """Indicate whether this simple type is a built-in type."""
        return (self.UrTypeDefinition() == self)

    def _dependentComponents_vx (self):
        """Implement base class method.

        Complex type definitions depend on their base type definition
        and their attribute uses, any associated wildcard, and any
        particle that appears in the content.
        """
        rv = set()
        assert self.__baseTypeDefinition is not None
        rv.add(self.__baseTypeDefinition)
        assert self.__attributeUses is not None
        rv.update(self.__attributeUses)
        if self.attributeWildcard() is not None:
            rv.add(self.attributeWildcard())
        if self.CT_EMPTY != self.contentType():
            rv.add(self.contentType()[1])
        return frozenset(rv)

    # CFD:CTD CFD:ComplexTypeDefinition
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        # Node should be an XMLSchema complexType node
        assert xsd.nodeIsNamed(node, 'complexType')

        name = NodeAttribute(node, 'name')

        rv = cls(name=name, node=node, derivation_method=None, **kw)

        # Creation does not attempt to do resolution.  Queue up the newly created
        # whatsis so we can resolve it after everything's been read in.
        rv.__domNode = node
        rv._annotationFromDOM(node)
        rv._queueForResolution()
        
        return rv

    __usesC1 = None

    # Handle attributeUses, attributeWildcard, contentType
    def __completeProcessing (self, definition_node_list, method, content_style):
        rv = self._attributeRelevantChildren(definition_node_list)
        if rv is None:
            self._queueForResolution()
            print 'Holding off CTD %s resolution due to unresolved attribute or group' % (self.name(),)
            return self

        (attributes, attribute_groups, any_attribute) = rv
        
        # Handle clauses 1 and 2 (common between simple and complex types)
        uses_c1 = self.__usesC1
        uses_c2 = set()
        uses_c3 = set()
        if uses_c1 is None:
            uses_c1 = set()
            for cn in attributes:
                au = AttributeUse.CreateFromDOM(cn, context=self, scope=self, owner=self)
                uses_c1.add(au)
            self.__usesC1 = uses_c1
        for agd in attribute_groups:
            uses_c2.update(agd.attributeUses())

        # Handle clause 3.  Note the slight difference in description
        # between simple and complex content is just that the complex
        # content doesn't bother to check that the base type
        # definition is a complex type definition.  So the same code
        # should work for both, and we don't bother to check
        # content_style.
        if isinstance(self.__baseTypeDefinition, ComplexTypeDefinition):
            uses_c3 = uses_c3.union(self.__baseTypeDefinition.__attributeUses)
            if self.DM_restriction == method:
                # Exclude attributes per clause 3.  Note that this
                # process handles both 3.1 and 3.2, since we have
                # not yet filtered uses_c1 for prohibited attributes.
                uses_c12 = uses_c1.union(uses_c2)
                for au in uses_c12:
                    matching_uses = au.matchingQNameMembers(uses_c3)
                    if matching_uses is None:
                        self._queueForResolution()
                        print 'Holding off CTD %s resolution to check for attribute restrictions' % (self.name(),)
                        return self
                    uses_c3 = uses_c3.difference(matching_uses)

        # Can't adapt for scope things that have not been resolved.
        all_uses = uses_c1.union(uses_c2).union(uses_c3)
        for au in all_uses:
            if not au.isResolved():
                self._queueForResolution()
                return self

        # Past the last point where we might not resolve this instance.  Store
        # the attribute uses, also recording local attribute declarations.
        self.__attributeUses = frozenset([ _u._adaptForScope(self) for _u in all_uses ])

        # @todo: Handle attributeWildcard
        # Clause 1
        local_wildcard = None
        if any_attribute is not None:
            local_wildcard = Wildcard.CreateFromDOM(any_attribute)

        # Clause 2
        complete_wildcard = _AttributeWildcard_mixin.CompleteWildcard(self._namespaceContext(), attribute_groups, any_attribute, local_wildcard)

        # Clause 3
        if self.DM_restriction == method:
            # Clause 3.1
            self._setAttributeWildcard(complete_wildcard)
        else:
            assert (self.DM_extension == method)
            assert self.baseTypeDefinition().isResolved()
            # 3.2.1
            base_wildcard = None
            if isinstance(self.baseTypeDefinition(), ComplexTypeDefinition):
                base_wildcard = self.baseTypeDefinition().attributeWildcard()
            # 3.2.2
            if base_wildcard is not None:
                if complete_wildcard is None:
                    # 3.2.2.1.1
                    self._setAttributeWildcard(base_wildcard)
                else:
                    # 3.2.2.1.2
                    self._setAttributeWildcard(process_contents=complete_wildcard.processContents(),
                                               namespace_constraint = Wildcard.IntensionalUnion([complete_wildcard.namespaceConstraint(),
                                                                                                 base_wildcard.namespaceConstraint()]),
                                               annotation=complete_wildcard.annotation())
            else:
                # 3.2.2.2
                self._setAttributeWildcard(complete_wildcard)

        # @todo: Make sure we didn't miss any child nodes

        self.__usesC1 = None

        # Only now that we've succeeded do we store the method, which
        # marks this component resolved.
        self.__derivationMethod = method
        return self

    def __simpleContent (self, method):
        # Do content type
        if isinstance(self.__baseTypeDefinition, ComplexTypeDefinition):
            # Clauses 1, 2, and 3 might apply
            parent_content_type = self.__baseTypeDefinition.__contentType
            if (isinstance(parent_content_type, SimpleTypeDefinition) \
                    and (self.DM_restriction == method)):
                # Clause 1
                raise pyxb.IncompleteImplementationError("contentType clause 1 of simple content in CTD")
            elif ((type(parent_content_type) == tuple) \
                    and (self.CT_mixed == parent_content_type[1]) \
                    and parent_content_type[0].isEmptiable()):
                # Clause 2
                raise pyxb.IncompleteImplementationError("contentType clause 2 of simple content in CTD")
            else:
                # Clause 3
                raise pyxb.IncompleteImplementationError("contentType clause 3 of simple content in CTD")
        else:
            # Clause 4
            return ( self.CT_SIMPLE, self.__baseTypeDefinition )
        assert False

    def __complexContent (self, type_node, content_node, definition_node_list, method):
        # Do content type.  Cache the keywords that need to be used
        # for newly created schema components.
        ckw = { 'node' : type_node
              , 'context' : self
              , 'owner' : self
              , 'scope' : self }

        # Definition 1: effective mixed
        mixed_attr = None
        if content_node is not None:
            mixed_attr = NodeAttribute(content_node, 'mixed')
        if mixed_attr is None:
            mixed_attr = NodeAttribute(type_node, 'mixed')
        if mixed_attr is not None:
            effective_mixed = datatypes.boolean(mixed_attr)
        else:
            effective_mixed = False

        # Definition 2: effective content
        case_2_1_predicate_count = 0
        test_2_1_1 = True
        test_2_1_2 = False
        test_2_1_3 = False
        typedef_node = None
        for cn in definition_node_list:
            if Node.ELEMENT_NODE != cn.nodeType:
                continue
            if xsd.nodeIsNamed(cn, 'simpleContent', 'complexContent'):
                # Should have found the content node earlier.
                raise pyxb.LogicError('Missed explicit wrapper in complexType content')
            if Particle.IsTypedefNode(cn):
                typedef_node = cn
                test_2_1_1 = False
            if xsd.nodeIsNamed(cn, 'all', 'sequence') \
                    and (not HasNonAnnotationChild(cn)):
                test_2_1_2 = True
            if xsd.nodeIsNamed(cn, 'choice') \
                    and (not HasNonAnnotationChild(cn)):
                mo_attr = NodeAttribute(cn, 'minOccurs')
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
                m = ModelGroup(compositor=ModelGroup.C_SEQUENCE, particles=[], **ckw)
                effective_content = Particle(m, **ckw)
            else:
                # Clause 2.1.5
                effective_content = self.CT_EMPTY
        else:
            # Clause 2.2
            assert typedef_node is not None
            # Context and scope are both this CTD
            pkw = ckw.copy()
            del pkw['node']
            effective_content = Particle.CreateFromDOM(typedef_node, **pkw)

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
                content_type = self.CT_EMPTY                     # ASSIGN CT_EMPTY
            else:
                # Clause 3.1.2(.2)
                content_type = ( ct, effective_content )         # ASSIGN RESTRICTION
        else:
            # Clause 3.2
            assert self.DM_extension == method
            assert self.__baseTypeDefinition.isResolved()
            parent_content_type = self.__baseTypeDefinition.contentType()
            if self.CT_EMPTY == effective_content:
                content_type = parent_content_type               # ASSIGN EXTENSION PARENT ONLY
            elif self.CT_EMPTY == parent_content_type:
                # Clause 3.2.2
                content_type = ( ct, effective_content )         # ASSIGN EXTENSION LOCAL ONLY
            else:
                assert type(parent_content_type) == tuple
                m = ModelGroup(compositor=ModelGroup.C_SEQUENCE, particles=[ parent_content_type[1], effective_content ], **ckw)
                content_type = ( ct, Particle(m, **ckw) )        # ASSIGN EXTENSION PARENT AND LOCAL

        assert (self.CT_EMPTY == content_type) or ((type(content_type) == tuple) and (content_type[1] is not None))
        return content_type

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

    # Back door to allow the ur-type to re-resolve itself.  Only needed when
    # we're generating bindings for XMLSchema itself.
    def _setDerivationMethod (self, derivation_method):
        self.__derivationMethod = derivation_method
        return self

    # Resolution of a CTD can be delayed for the following reasons:
    #
    # * It extends or restricts a base type that has not been resolved
    #   [_resolve]
    #
    # * It refers to an attribute or attribute group that has not been
    #   resolved [__completeProcessing]
    #
    # * It includes an attribute that matches in NCName and namespace
    #   an unresolved attribute from the base type
    #   [__completeProcessing]
    #
    # * The content model includes a particle which cannot be resolved
    #   (so has not contributed any local element declarations).
    def _resolve (self):
        if self.isResolved():
            return self
        assert self.__domNode
        node = self.__domNode
        
        #print 'Resolving CTD %s' % (self.name(),)
        attr_val = NodeAttribute(node, 'abstract')
        if attr_val is not None:
            self.__abstract = datatypes.boolean(attr_val)

        # @todo: implement prohibitedSubstitutions, final, annotations

        # See whether we've resolved through to the base type
        if self.__baseTypeDefinition is None:
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
                if xsd.nodeIsNamed(first_elt, 'simpleContent'):
                    have_content = True
                    is_complex_content = False
                elif xsd.nodeIsNamed(first_elt, 'complexContent'):
                    have_content = True
                else:
                    # Not one of the wrappers; use implicit wrapper around
                    # the children
                    pass
                if have_content:
                    # Repeat the search to verify that only the one child is present.
                    content_node = LocateFirstChildElement(node, require_unique=True)
                    assert content_node == first_elt
                    
                    # Identify the contained restriction or extension
                    # element, and extract the base type.
                    ions = LocateFirstChildElement(content_node, absent_ok=False)
                    if xsd.nodeIsNamed(ions, 'restriction'):
                        method = self.DM_restriction
                    elif xsd.nodeIsNamed(ions, 'extension'):
                        method = self.DM_extension
                    else:
                        raise pyxb.SchemaValidationError('Expected restriction or extension as sole child of %s in %s' % (content_node.name(), self.name()))
                    base_attr = NodeAttribute(ions, 'base')
                    if base_attr is None:
                        raise pyxb.SchemaValidationError('Element %s missing base attribute' % (ions.nodeName,))
                    base_en = self._namespaceContext().interpretQName(base_attr)
                    base_type = base_en.typeDefinition()
                    if base_type is None:
                        raise pyxb.SchemaValidationError('Cannot locate %s: need import?' % (base_en,))
                    if not base_type.isResolved():
                        # Have to delay resolution until the type this
                        # depends on is available.
                        #print 'Holding off resolution of %s due to dependence on unresolved %s' % (self.name(), base_type.name())
                        self._queueForResolution()
                        return self
                    # The content is defined by the restriction/extension element
                    definition_node_list = ions.childNodes
            # deriviationMethod is assigned after resolution completes
            self.__baseTypeDefinition = base_type
            self.__pendingDerivationMethod = method
            self.__definitionNodeList = definition_node_list
            self.__contentNode = content_node

        if self.__baseTypeDefinition is None:
            self._queueForResolution()
            return self

        # Only build the content once.  This all completes now that we
        # have a base type.
        if self.__contentType is None:
            if is_complex_content:
                content_type = self.__complexContent(node, self.__contentNode, self.__definitionNodeList, self.__pendingDerivationMethod)
                self.__contentStyle = 'complex'
            else:
                # The definition node list is not relevant to simple content
                content_type = self.__simpleContent(self.__pendingDerivationMethod)
                self.__contentStyle = 'simple'
            assert content_type is not None
            self.__contentType = content_type

        # If something went wrong building the content, we'll have to
        # try again later
        if self.__contentType is None:
            self._queueForResolution()
            return self

        # Last chance for failure is if we haven't been able to
        # extract all the element declarations that might appear in
        # this complex type.  That technically wouldn't stop this from
        # being resolved, but it does prevent us from using it as a
        # context.
        if isinstance(self.__contentType, tuple) and isinstance(self.__contentType[1], Particle):
            prt = self.__contentType[1]
            if not prt.isDeepResolved():
                self._queueForResolution()
                return self

        return self.__completeProcessing(self.__definitionNodeList, self.__pendingDerivationMethod, self.__contentStyle)

    def __str__ (self):
        return 'CTD[%s]' % (self.name(),)


class _UrTypeDefinition (ComplexTypeDefinition, _Singleton_mixin):
    """Subclass ensures there is only one ur-type."""
    def _dependentComponents_vx (self):
        """The UrTypeDefinition is not dependent on anything."""
        return frozenset()

    def _resolve (self):
        # The ur type is always resolved, except when it gets unresolved
        # through being updated from an instance read from the schema.
        return self._setDerivationMethod(self.DM_restriction)
 

class AttributeGroupDefinition (_SchemaComponent_mixin, _NamedComponent_mixin, pyxb.namespace._Resolvable_mixin, _Annotated_mixin, _AttributeWildcard_mixin):
    # A frozenset of AttributeUse instances
    __attributeUses = None

    def _dependentComponents_vx (self):
        """Implement base class method.

        Attribute group definitions depend on their attribute uses and
        any associated wildcard.
        """
        rv = set(self.__attributeUses)
        if self.attributeWildcard() is not None:
            rv.add(self.attributeWildcard())
        return frozenset(rv)

    def __init__ (self, *args, **kw):
        super(AttributeGroupDefinition, self).__init__(*args, **kw)
        assert _ScopedDeclaration_mixin.SCOPE_global == self._context()
        assert 'scope' in kw
        assert self._scopeIsIndeterminate()

    # CFD:AGD CFD:AttributeGroupDefinition
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create an attribute group definition from the given DOM node.

        """
        
        assert xsd.nodeIsNamed(node, 'attributeGroup')
        name = NodeAttribute(node, 'name')

        # Attribute group definitions can only appear at the top level
        # of the schema, so the context is always SCOPE_global.  Any
        # definitions in them are scope indeterminate, until they're
        # referenced in a complex type.
        kw.update({ 'context' : _ScopedDeclaration_mixin.SCOPE_global,
                    'scope' : _ScopedDeclaration_mixin.XSCOPE_indeterminate })
        rv = cls(name=name, node=node, **kw)

        rv._annotationFromDOM(node)
        rv._queueForResolution()
        rv.__domNode = node
        return rv

    # Indicates whether we have resolved any references
    __isResolved = False
    def isResolved (self):
        return self.__isResolved

    def _resolve (self):
        if self.__isResolved:
            return self
        node = self.__domNode

        # Attribute group definitions must not be references
        ref_attr = NodeAttribute(node, 'ref')
        if ref_attr is not None:
            raise pyxb.SchemaValidationError('Attribute reference at top level')

        rv = self._attributeRelevantChildren(node.childNodes)
        if rv is None:
            self._queueForResolution()
            return self

        (attributes, attribute_groups, any_attribute) = rv
        uses = set()
        for cn in attributes:
            uses.add(AttributeUse.CreateFromDOM(cn, context=self._context(), scope=self._scope(), owner=self))
        for agd in attribute_groups:
            uses = uses.union(agd.attributeUses())

        # "Complete wildcard" per CTD
        local_wildcard = None
        if any_attribute is not None:
            local_wildcard = Wildcard.CreateFromDOM(any_attribute)
        self._setAttributeWildcard(_AttributeWildcard_mixin.CompleteWildcard(self._namespaceContext(), attribute_groups, any_attribute, local_wildcard))

        self.__attributeUses = frozenset(uses)
        self.__isResolved = True
        self.__domNode = None
        return self
        
    def attributeUses (self):
        return self.__attributeUses

class ModelGroupDefinition (_SchemaComponent_mixin, _NamedComponent_mixin, _Annotated_mixin):
    # Reference to a _ModelGroup
    __modelGroup = None

    def modelGroup (self):
        """The model group for which this definition provides a name."""
        return self.__modelGroup

    def _dependentComponents_vx (self):
        """Implement base class method.

        Model group definitions depend only on their model group.
        """
        return frozenset([self.__modelGroup])

    # CFD:MGD CFD:ModelGroupDefinition
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create a Model Group Definition from a DOM element node.

        wxs is a Schema instance within which the model group is being
        defined.

        node is a DOM element.  The name must be 'group', and the node
        must be in the XMLSchema namespace.  The node must have a
        'name' attribute, and must not have a 'ref' attribute.
        """
        assert xsd.nodeIsNamed(node, 'group')

        assert NodeAttribute(node, 'ref') is None

        name = NodeAttribute(node, 'name')
        kw.update({ 'context' : _ScopedDeclaration_mixin.SCOPE_global,
                    'scope' : _ScopedDeclaration_mixin.XSCOPE_indeterminate })
        rv = cls(name=name, node=node, **kw)
        rv._annotationFromDOM(node)

        for cn in node.childNodes:
            if Node.ELEMENT_NODE != cn.nodeType:
                continue
            if ModelGroup.IsGroupMemberNode(cn):
                assert not rv.__modelGroup
                # Model group definitions always occur at the top level of the
                # schema, so their lookup context is SCOPE_global.  The
                # element declared in them are not bound to a scope until they
                # are referenced in a complex type, so the scope is
                # indeterminate.
                rv.__modelGroup = ModelGroup.CreateFromDOM(cn, context=_ScopedDeclaration_mixin.SCOPE_global, scope=_ScopedDeclaration_mixin.XSCOPE_indeterminate, model_group_definition=rv, owner=rv)
        assert rv.__modelGroup is not None
        return rv

    def __str__ (self):
        return 'MGD[%s: %s]' % (self.name(), self.modelGroup())


class ModelGroup (_SchemaComponent_mixin, _Annotated_mixin):
    C_INVALID = 0
    C_ALL = 0x01
    C_CHOICE = 0x02
    C_SEQUENCE = 0x03

    # One of the C_* values above.  Set at construction time from the
    # keyword parameter "compositor".
    __compositor = C_INVALID
    def compositor (self): return self.__compositor

    @classmethod
    def CompositorToString (cls, compositor):
        """Map a compositor value to a string."""
        if cls.C_ALL == compositor:
            return 'all'
        if cls.C_CHOICE == compositor:
            return 'choice'
        if cls.C_SEQUENCE == compositor:
            return 'sequence'
        return 'invalid'

    def compositorToString (self):
        """Return a string representing the compositor value."""
        return self.CompositorToString(self.__compositor)

    # A list of Particle instances.  Set at construction time from
    # the keyword parameter "particles".
    __particles = None
    def particles (self): return self.__particles

    def isDeepResolved (self):
        """A model group has an unresolvable particle if any of its
        particles is unresolvable.  Duh."""
        for p in self.particles():
            if not p.isDeepResolved():
                return False
        return True

    # The ModelGroupDefinition that names this ModelGroup, or None if
    # the ModelGroup is anonymous.  This is set at construction time
    # from the keyword parameter "model_group_definition".
    __modelGroupDefinition = None
    def modelGroupDefinition (self):
        """The ModelGroupDefinition that names this group, or None if it is unnamed."""
        return self.__modelGroupDefinition

    def _dependentComponents_vx (self):
        """Implement base class method.

        Model groups depend on their particles.
        """
        return frozenset(self.__particles)

    def __init__ (self, compositor, particles, *args, **kw):
        """Create a new model group.

        compositor must be a legal compositor value (one of C_ALL, C_CHOICE, C_SEQUENCE).

        particles must be a list of zero or more Particle instances.
        
        context must be a valid scope in which declaration references found
        within this model will be resolved.

        scope is the _ScopeDeclaration_mixin context into which new
        declarations are recorded.  It can be SCOPE_global, a complex
        type definition, or None if this is (or is within) a named
        model group.

        model_group_definition is an instance of ModelGroupDefinition
        if this is a named model group.  It defaults to None
        indicating a local group.
        """

        super(ModelGroup, self).__init__(*args, **kw)
        assert 'context' in kw
        assert 'scope' in kw
        self.__compositor = compositor
        #print 'Incoming particles %s with scope %s' % (particles, self._scope())
        self.__particles = particles
        self.__modelGroupDefinition = kw.get('model_group_definition')

    def isPlural (self):
        """A model group is multi-valued if it has a multi-valued particle."""
        for p in self.particles():
            if p.isPlural():
                return True
        return False

    def pluralityData (self):
        """Get the plurality data for this model group.
        """
        return _PluralityData(self)

    def hasWildcardElement (self):
        """Return True if the model includes a wildcard amongst its particles."""
        for p in self.particles():
            if p.hasWildcardElement():
                return True
        return False

    # CFD:MG CFD:ModelGroup
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create a model group from the given DOM node.

        wxs is a Schema instance within which the model group is being
        defined.

        context is the _ScopeDeclaration_mixin context that is used to
        resolve references internal to the model group.  The context
        is passed down to child particles that are being created.

        node is a DOM element.  The name must be one of ( 'all',
        'choice', 'sequence' ), and the node must be in the XMLSchema
        namespace.

        scope is the _ScopeDeclaration_mxin context that is assigned
        to declarations that appear within the model group.  It can be
        None, indicating no scope defined, or a complex type
        definition.
        """
        
        context = kw['context']
        assert _ScopedDeclaration_mixin.IsValidScope(context)
        scope = kw['scope']
        assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or isinstance(scope, ComplexTypeDefinition)

        if xsd.nodeIsNamed(node, 'all'):
            compositor = cls.C_ALL
        elif xsd.nodeIsNamed(node, 'choice'):
            compositor = cls.C_CHOICE
        elif xsd.nodeIsNamed(node, 'sequence'):
            compositor = cls.C_SEQUENCE
        else:
            raise pyxb.IncompleteImplementationError('ModelGroup: Got unexpected %s' % (node.nodeName,))
        particles = []
        # Remove the owner from particle constructor arguments: we need to set it later
        kw.pop('owner', None)
        for cn in node.childNodes:
            if Node.ELEMENT_NODE != cn.nodeType:
                continue
            if Particle.IsParticleNode(cn):
                # NB: Ancestor of particle is set in the ModelGroup constructor
                particles.append(Particle.CreateFromDOM(node=cn, **kw))
        rv = cls(compositor, particles, node=node, **kw)
        for p in particles:
            p._setOwner(rv)
        rv._annotationFromDOM(node)
        return rv

    @classmethod
    def IsGroupMemberNode (cls, node):
        return xsd.nodeIsNamed(node, 'all', 'choice', 'sequence')

    def elementDeclarations (self):
        """Return a list of all ElementDeclarations that are at the
        top level of this model group, in the order in which they can
        occur."""
        element_decls = []
        model_groups = [ self ]
        #print 'Extracting element declarations from model group with %d particles: %s'  % (len(self.particles()), self.particles())
        while model_groups:
            mg = model_groups.pop(0)
            for p in mg.particles():
                if isinstance(p.term(), ModelGroup):
                    model_groups.append(p.term())
                elif isinstance(p.term(), ElementDeclaration):
                    element_decls.extend(p.elementDeclarations())
                else:
                    assert p.term() is not None
                    pass
                #print 'Particle term: %s' % (object.__str__(p.term()),)
        #print 'Model group with %d particles produced %d element declarations' % (len(self.particles()), len(element_decls))
        return element_decls

    def _adaptForScope (self, owner, scope):
        rv = self
        scoped_particles = [ _p._adaptForScope(None, scope) for _p in self.particles() ]
        if scoped_particles != self.particles():
            rv = self._clone()
            rv._setOwner(owner)
            rv.__particles = scoped_particles
        return rv

    def __str__ (self):
        comp = None
        if self.C_ALL == self.compositor():
            comp = 'ALL'
        elif self.C_CHOICE == self.compositor():
            comp = 'CHOICE'
        elif self.C_SEQUENCE == self.compositor():
            comp = 'SEQUENCE'
        return '%s:(%s)' % (comp, ",".join( [ str(_p) for _p in self.particles() ] ) )

class Particle (_SchemaComponent_mixin, pyxb.namespace._Resolvable_mixin):
    """Some entity along with occurrence information."""

    # The minimum number of times the term may appear.
    __minOccurs = 1
    def minOccurs (self):
        """The minimum number of times the term may appear.

        Defaults to 1."""
        return self.__minOccurs

    # Upper limit on number of times the term may appear.
    __maxOccurs = 1
    def maxOccurs (self):
        """Upper limit on number of times the term may appear.

        If None, the term may appear any number of times; otherwise,
        this is an integral value indicating the maximum number of times
        the term may appear.  The default value is 1; the value, unless
        None, must always be at least minOccurs().
        """
        return self.__maxOccurs

    # A reference to a ModelGroup, WildCard, or ElementDeclaration
    __term = None
    def term (self):
        """A reference to a ModelGroup, Wildcard, or ElementDeclaration."""
        return self.__term
    __pendingTerm = None

    def elementDeclarations (self):
        assert self.__term is not None
        if isinstance(self.__term, ModelGroup):
            return self.__term.elementDeclarations()
        if isinstance(self.__term, ElementDeclaration):
            return [ self.__term ]
        if isinstance(self.__term, Wildcard):
            return [ ]
        raise pyxb.LogicError('Unexpected term type %s' % (self.__term,))

    def pluralityData (self):
        """Return the plurality data for this component.

        The plurality data for a particle is the plurality data for
        its term, with the counts scaled by the effect of
        maxOccurs."""
        return _PluralityData(self)

    def isPlural (self):
        """Return true iff the term might appear multiple times."""
        if (self.maxOccurs() is None) or 1 < self.maxOccurs():
            return True
        # @todo: is this correct?
        return self.term().isPlural()

    def hasWildcardElement (self):
        """Return True iff this particle has a wildcard in its term.

        Note that the wildcard may be in a nested model group."""
        return self.term().hasWildcardElement()

    def _dependentComponents_vx (self):
        """Implement base class method.

        Particles depend on their term.
        """
        return frozenset([self.__term])

    # The ComplexTypeDefinition or ModelGroup in which this particle
    # appears.  Need this during resolution to handle non-reference
    # local ElementDeclarations.
    __ancestorComponent = None

    def __init__ (self, term, *args, **kw):
        """Create a particle from the given DOM node.

        term is a XML Schema Component: one of ModelGroup,
        ElementDeclaration, and Wildcard.

        The following keyword arguments are processed:

        min_occurs is a non-negative integer value with default 1,
        denoting the minimum number of terms required by the content
        model.

        max_occurs is a positive integer value with default 1, or None
        indicating unbounded, denoting the maximum number of terms
        allowed by the content model.

        context is the _ScopeDeclaration_mixin context that is used to
        resolve element references.  The context is passed down to
        child model groups that are created.

        scope is the _ScopeDeclaration_mxin context that is assigned
        to declarations that appear within the particle.  It can be
        None, indicating no scope defined, or a complex type
        definition.
        """

        super(Particle, self).__init__(*args, **kw)

        min_occurs = kw.get('min_occurs', 1)
        max_occurs = kw.get('max_occurs', 1)

        assert 'context' in kw
        assert 'scope' in kw
        assert _ScopedDeclaration_mixin.IsValidScope(self._context())
        assert (self._scopeIsIndeterminate()) or isinstance(self._scope(), ComplexTypeDefinition)

        if term is not None:
            # It may be possible to get here with an unresolved term.  I
            # thought I saw that once when processing XMLSchema.  If so, we
            # need to hold off resolution of this particle.
            assert (not isinstance(term, pyxb.namespace._Resolvable_mixin)) or term.isResolved()
            self.__term = term._adaptForScope(self, self._scope())

        assert isinstance(min_occurs, (types.IntType, types.LongType))
        self.__minOccurs = min_occurs
        assert (max_occurs is None) or isinstance(max_occurs, (types.IntType, types.LongType))
        self.__maxOccurs = max_occurs
        if self.__maxOccurs is not None:
            if self.__minOccurs > self.__maxOccurs:
                raise pyxb.LogicError('Particle minOccurs %s is greater than maxOccurs %s on creation' % (min_occurs, max_occurs))
    
    # res:Particle
    def _resolve (self):
        if self.isResolved():
            return self
        node = self.__domNode
        context = self._context()
        scope = self._scope()
        ref_attr = NodeAttribute(node, 'ref')
        if xsd.nodeIsNamed(node, 'group'):
            # 3.9.2 says use 3.8.2, which is ModelGroup.  The group
            # inside a particle is a groupRef.  If there is no group
            # with that name, this throws an exception as expected.
            if ref_attr is None:
                raise pyxb.SchemaValidationError('group particle without reference')
            # Named groups can only appear at global scope, so no need
            # to use context here.
            ref_en = self._namespaceContext().interpretQName(ref_attr)
            group_decl = ref_en.modelGroupDefinition()
            if group_decl is None:
                self._queueForResolution()
                return self

            # Neither group definitions nor model groups require themselves,
            # but model groups contain things that do require resolution, and
            # we can't adapt the group for scope if it isn't deep-resolved.
            if not group_decl.modelGroup().isDeepResolved():
                self._queueForResolution()
                return self

            # Only time this gets hit is in processing the XMLSchema schema.
            # Suspending results in the namespace being unresolvable; for now,
            # don't know why, nor need to.
            if self._scopeIsIndeterminate():
                self._queueForResolution()
                return self

            term = group_decl.modelGroup()._adaptForScope(self, scope)
            assert term is not None
        elif xsd.nodeIsNamed(node, 'element'):
            assert not xsd.nodeIsNamed(node.parentNode, 'schema')
            # 3.9.2 says use 3.3.2, which is Element.  The element inside a
            # particle is a localElement, so we either get the one it refers
            # to (which is top-level), or create a local one here.
            if ref_attr is not None:
                ref_en = self._namespaceContext().interpretQName(ref_attr)
                term = ref_en.elementDeclaration()
                if term is None:
                    raise pyxb.SchemaValidationError('Unable to locate element referenced by %s' % (ref_en,))
            else:
                target_namespace = self._resolvingSchema().targetNamespaceForNode(node, ElementDeclaration)
                alt_term = None
                if isinstance(scope, ComplexTypeDefinition):
                    # Look for an existing local element declaration with the
                    # same expanded name.
                    name = NodeAttribute(node, 'name')
                    assert name is not None
                    elt_en = pyxb.namespace.ExpandedName(target_namespace, name)
                    alt_term = scope.lookupScopedElementDeclaration(elt_en)

                # If we haven't already created a component for this
                # declaration, do so.  Note that we won't record it if we
                # already have one with the same name.
                if self.__pendingTerm is None:
                    aux_kw = { }
                    if alt_term is not None:
                        aux_kw['scope_inhibit_record'] = True
                    self.__pendingTerm = ElementDeclaration.CreateFromDOM(node=node, scope=scope, owner=self, target_namespace=target_namespace, **aux_kw)

                if alt_term is None:
                    # No pre-existing element with same name; go with the one we created
                    term = self.__pendingTerm
                    self.__pendingTerm = None
                else:
                    # Might be a conflict.  Both candidates must be resolved before we can tell.
                    if not (alt_term.isResolved() and self.__pendingTerm.isResolved()):
                        self._queueForResolution()
                        return self
                    # Test cos-element-consistent
                    alt_type = alt_term.typeDefinition()
                    pending_type = self.__pendingTerm.typeDefinition()
                    if not alt_type.isTypeEquivalent(pending_type):
                        raise pyxb.SchemaValidationError('Conflicting element declarations for %s: %s versus %s' % (alt_term.expandedName(), alt_type, pending_type))
                    # They're equivalent; just re-use the old one, discarding the new one.
                    self.__pendingTerm._dissociateFromNamespace()
                    self.__pendingTerm = None
                    term = alt_term
            assert term is not None
        elif xsd.nodeIsNamed(node, 'any'):
            # 3.9.2 says use 3.10.2, which is Wildcard.
            term = Wildcard.CreateFromDOM(node=node)
            assert term is not None
        elif ModelGroup.IsGroupMemberNode(node):
            # Choice, sequence, and all inside a particle are explicit
            # groups (or a restriction of explicit group, in the case
            # of all)
            term = ModelGroup.CreateFromDOM(node=node, context=context, scope=scope, owner=self)
        else:
            raise pyxb.LogicError('Unhandled node in Particle._resolve: %s' % (node.toxml(),))
        self.__domNode = None
        self.__term = term
        assert self.__term is not None
        return self

    def isResolved (self):
        return self.__term is not None

    # CFD:Particle
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        """Create a particle from the given DOM node.

        wxs is a Schema instance within which the model group is being
        defined.

        context is the _ScopeDeclaration_mixin context that is used to
        resolve element references.

        node is a DOM element.  The name must be one of ( 'group',
        'element', 'any', 'all', 'choice', 'sequence' ), and the node
        must be in the XMLSchema namespace.

        scope is the _ScopeDeclaration_mxin context that is assigned
        to declarations that appear within the model group.  It can be
        None, indicating no scope defined, or a complex type
        definition.
        """
        context = kw['context']
        assert _ScopedDeclaration_mixin.IsValidScope(context)
        scope = kw['scope']
        assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or isinstance(scope, ComplexTypeDefinition)

        kw.update({ 'min_occurs' : 1
                  , 'max_occurs' : 1
                  , 'node' : node })
               
        if not Particle.IsParticleNode(node):
            raise pyxb.LogicError('Attempted to create particle from illegal element %s' % (node.nodeName,))
        attr_val = NodeAttribute(node, 'minOccurs')
        if attr_val is not None:
            kw['min_occurs'] = datatypes.nonNegativeInteger(attr_val)
        attr_val = NodeAttribute(node, 'maxOccurs')
        if attr_val is not None:
            if 'unbounded' == attr_val:
                kw['max_occurs'] = None
            else:
                kw['max_occurs'] = datatypes.nonNegativeInteger(attr_val)

        rv = cls(None, **kw)
        rv.__domNode = node
        rv._queueForResolution()
        return rv

    def _adaptForScope (self, owner, scope):
        rv = self
        if (self._scopeIsIndeterminate()) and (scope is not None):
            rv = self._clone()
            rv._setOwner(owner)
            rv.__term = rv.__term._adaptForScope(rv, scope)
        else:
            try:
                assert self.__term._scopeIsCompatible(scope)
            except AttributeError, e:
                pass
        return rv

    def isDeepResolved (self):
        """A particle has an unresolvable particle if it cannot be
        resolved, or if it has resolved to a term which is a model
        group that has an unresolvable particle.

        wxs is a schema within which resolution proceeds, or None to
        indicate that this should simply test for lack of
        resolvability, not do any resolution.

        """
        if not self.isResolved():
            return False
        return self.term().isDeepResolved()
        
    @classmethod
    def IsTypedefNode (cls, node):
        return xsd.nodeIsNamed(node, 'group', 'all', 'choice', 'sequence')

    @classmethod
    def IsParticleNode (cls, node):
        return xsd.nodeIsNamed(node, 'group', 'all', 'choice', 'sequence', 'element', 'any')

    def __str__ (self):
        #return 'PART{%s:%d,%s}' % (self.term(), self.minOccurs(), self.maxOccurs())
        return 'PART{%s:%d,%s}' % ('TERM', self.minOccurs(), self.maxOccurs())


# 3.10.1
class Wildcard (_SchemaComponent_mixin, _Annotated_mixin):
    NC_any = '##any'            #<<< The namespace constraint "##any"
    NC_not = '##other'          #<<< A flag indicating constraint "##other"
    NC_targetNamespace = '##targetNamespace'
    NC_local = '##local'

    __namespaceConstraint = None
    def namespaceConstraint (self):
        """A constraint on the namespace for the wildcard.

        Valid values are:
         - L{Wildcard.NC_any}
         - A tuple ( L{Wildcard.NC_not}, a_namespace )
         - set(of_namespaces)

        Note that namespace are represented by
        L{Namespace<pyxb.namespace.Namespace>} instances, not the URIs that
        actually define a namespace.  Absence of a namespace is represented by
        C{None}, both in the "not" pair and in the set.
        """
        return self.__namespaceConstraint

    @classmethod
    def IntensionalUnion (cls, constraints):
        """http://www.w3.org/TR/xmlschema-1/#cos-aw-union"""
        assert 0 < len(constraints)
        o1 = constraints.pop(0);
        while 0 < len(constraints):
            o2 = constraints.pop(0);
            # 1
            if (o1 == o2):
                continue
            # 2
            if (cls.NC_any == o1) or (cls.NC_any == o2):
                o1 = cls.NC_any
                continue
            # 3
            if isinstance(o1, set) and isinstance(o2, set):
                o1 = o1.union(o2)
                continue
            # 4
            if (isinstance(o1, tuple) and isinstance(o2, tuple)) and (o1[1] != o2[1]):
                o1 = ( cls.NC_not, None )
                continue
            # At this point, one must be a negated namespace and the
            # other a set.  Identify them.
            c_tuple = None
            c_set = None
            if isinstance(o1, tuple):
                assert isinstance(o2, set)
                c_tuple = o1
                c_set = o2
            else:
                assert isinstance(o1, set)
                assert isinstance(o2, tuple)
                c_tuple = o2
                c_set = o1
            negated_ns = c_tuple[1]
            if negated_ns is not None:
                # 5.1
                if (negated_ns in c_set) and (None in c_set):
                    o1 = cls.NC_any
                    continue
                # 5.2
                if negated_ns in c_set:
                    o1 = ( cls.NC_not, None )
                    continue
                # 5.3
                if None in c_set:
                    raise pyxb.SchemaValidationError('Union of wildcard namespace constraints not expressible')
                o1 = c_tuple
                continue
            # 6
            if None in c_set:
                o1 = cls.NC_any
            else:
                o1 = ( cls.NC_not, None )
        return o1

    @classmethod
    def IntensionalIntersection (cls, constraints):
        """http://www.w3.org/TR/xmlschema-1/#cos-aw-intersect"""
        assert 0 < len(constraints)
        o1 = constraints.pop(0);
        while 0 < len(constraints):
            o2 = constraints.pop(0);
            # 1
            if (o1 == o2):
                continue
            # 2
            if (cls.NC_any == o1) or (cls.NC_any == o2):
                if cls.NC_any == o1:
                    o1 = o2
                continue
            # 4
            if isinstance(o1, set) and isinstance(o2, set):
                o1 = o1.intersection(o2)
                continue
            if isinstance(o1, tuple) and isinstance(o2, tuple):
                ns1 = o1[1]
                ns2 = o2[1]
                # 5
                if (ns1 is not None) and (ns2 is not None) and (ns1 != ns2):
                    raise pyxb.SchemaValidationError('Intersection of wildcard namespace constraints not expressible')
                # 6
                assert (ns1 is None) or (ns2 is None)
                if ns1 is None:
                    assert ns2 is not None
                    o1 = ( cls.NC_not, ns2 )
                else:
                    assert ns1 is not None
                    o1 = ( cls.NC_not, ns1 )
                continue
            # 3
            # At this point, one must be a negated namespace and the
            # other a set.  Identify them.
            c_tuple = None
            c_set = None
            if isinstance(o1, tuple):
                assert isinstance(o2, set)
                c_tuple = o1
                c_set = o2
            else:
                assert isinstance(o1, set)
                assert isinstance(o2, tuple)
                c_tuple = o2
                c_set = o1
            negated_ns = c_tuple[1]
            if negated_ns in c_set:
                c_set.remove(negated_ns)
            if None in c_set:
                c_set.remove(None)
            o1 = c_set
        return o1

    PC_skip = 'skip'            #<<< No constraint is applied
    PC_lax = 'lax'              #<<< Validate against available uniquely determined declaration
    PC_strict = 'strict'        #<<< Validate against declaration or xsi:type which must be available

    # One of PC_*
    __processContents = None
    def processContents (self): return self.__processContents

    def pluralityData (self):
        """Get the plurality data for this wildcard
        """
        return _PluralityData(self)

    def isPlural (self):
        """Wildcards are not multi-valued."""
        return False

    def hasWildcardElement (self):
        """Return True, since Wildcard components are wildcards."""
        return True

    def __init__ (self, *args, **kw):
        assert 0 == len(args)
        super(Wildcard, self).__init__(*args, **kw)
        self.__namespaceConstraint = kw['namespace_constraint']
        self.__processContents = kw['process_contents']

    def _dependentComponents_vx (self):
        """Implement base class method.

        Wildcards depend on nothing.
        """
        return frozenset()

    def isDeepResolved (self):
        return True

    def _adaptForScope (self, owner, ctd):
        """Wildcards are scope-independent; return self"""
        return self

    # CFD:Wildcard
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        namespace_context = pyxb.namespace.NamespaceContext.GetNodeContext(node)
        assert xsd.nodeIsNamed(node, 'any', 'anyAttribute')
        nc = NodeAttribute(node, 'namespace')
        if nc is None:
            namespace_constraint = cls.NC_any
        else:
            if cls.NC_any == nc:
                namespace_constraint = cls.NC_any
            elif cls.NC_not == nc:
                namespace_constraint = ( cls.NC_not, namespace_context.targetNamespace() )
            else:
                ncs = set()
                for ns_uri in nc.split():
                    if cls.NC_local == ns_uri:
                        ncs.add(None)
                    elif cls.NC_targetNamespace == ns_uri:
                        ncs.add(namespace_context.targetNamespace())
                    else:
                        ncs.add(pyxb.namespace.NamespaceForURI(ns_uri, create_if_missing=True))
                namespace_constraint = frozenset(ncs)

        pc = NodeAttribute(node, 'processContents')
        if pc is None:
            process_contents = cls.PC_strict
        else:
            if pc in [ cls.PC_skip, cls.PC_lax, cls.PC_strict ]:
                process_contents = pc
            else:
                raise pyxb.SchemaValidationError('illegal value "%s" for any processContents attribute' % (pc,))

        rv = cls(node=node, namespace_constraint=namespace_constraint, process_contents=process_contents, **kw)
        rv._annotationFromDOM(node)
        return rv

# 3.11.1
class IdentityConstraintDefinition (_SchemaComponent_mixin, _NamedComponent_mixin, _Annotated_mixin, pyxb.namespace._Resolvable_mixin):
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

    def _dependentComponents_vx (self):
        """Implement base class method.

        Identity constraint definitions depend on nothing.
        """
        return frozenset()

    # CFD:ICD CFD:IdentityConstraintDefinition
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        name = NodeAttribute(node, 'name')
        scope = kw['scope']
        assert _ScopedDeclaration_mixin.ScopeIsIndeterminate(scope) or _ScopedDeclaration_mixin.IsValidScope(scope)
        rv = cls(name=name, node=node, **kw)
        rv.__domNode = node
        rv._queueForResolution()
        return rv

    def isResolved (self):
        return self.__identityConstraintCategory is not None

    # res:ICD res:IdentityConstraintDefinition
    def _resolve (self):
        if self.isResolved():
            return self
        node = self.__domNode

        #self._annotationFromDOM(node);
        icc = None
        if xsd.nodeIsNamed(node, 'key'):
            icc = self.ICC_KEY
        elif xsd.nodeIsNamed(node, 'keyref'):
            icc = self.ICC_KEYREF
            refer_attr = NodeAttribute(node, 'refer')
            if refer_attr is None:
                raise pyxb.SchemaValidationError('Require refer attribute on keyref elements')
            refer_en = self._namespaceContext().interpretQName(refer_attr)
            refer = refer_en.identityConstraintDefinition()
            if refer is None:
                self._queueForResolution()
                return self
            self.__referencedKey = refer
        elif xsd.nodeIsNamed(node, 'unique'):
            icc = self.ICC_UNIQUE
        else:
            raise pyxb.LogicError('Unexpected identity constraint node %s' % (node.toxml(),))

        cn = LocateUniqueChild(node, 'selector')
        self.__selector = NodeAttribute(cn, 'xpath')
        if self.__selector is None:
            raise pyxb.SchemaValidationError('selector element missing xpath attribute')

        self.__fields = []
        for cn in LocateMatchingChildren(node, 'field'):
            xp_attr = NodeAttribute(cn, 'xpath')
            if xp_attr is None:
                raise pyxb.SchemaValidationError('field element missing xpath attribute')
            self.__fields.append(xp_attr)

        self._annotationFromDOM(node)
        self.__annotations = []
        if self.annotation() is not None:
            self.__annotations.append(self)

        for cn in node.childNodes:
            if (Node.ELEMENT_NODE != cn.nodeType):
                continue
            an = None
            if xsd.nodeIsNamed(cn, 'selector', 'field'):
                an = LocateUniqueChild(cn, 'annotation')
            elif xsd.nodeIsNamed(cn, 'annotation'):
                an = cn
            if an is not None:
                self.__annotations.append(Annotation.CreateFromDOM(an, owner=self))

        self.__identityConstraintCategory = icc
        if self.ICC_KEYREF != self.__identityConstraintCategory:
            self._namespaceContext().targetNamespace().addCategoryObject('identityConstraintDefinition', self.name(), self)

        self.__domNode = None
        return self
    
# 3.12.1
class NotationDeclaration (_SchemaComponent_mixin, _NamedComponent_mixin, _Annotated_mixin):
    __systemIdentifier = None
    def systemIdentifier (self): return self.__systemIdentifier
    
    __publicIdentifier = None
    def publicIdentifier (self): return self.__publicIdentifier

    def _dependentComponents_vx (self):
        """Implement base class method.

        Notation declarations depend on nothing.
        """
        return frozenset()

    # CFD:ND CFD:NotationDeclaration
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        name = NodeAttribute(node, 'name')
        rv = cls(name=name, node=node, **kw)

        rv.__systemIdentifier = NodeAttribute(node, 'system')
        rv.__publicIdentifier = NodeAttribute(node, 'public')

        rv._annotationFromDOM(node)
        return rv

# 3.13.1
class Annotation (_SchemaComponent_mixin):
    __applicationInformation = None
    def applicationInformation (self):
        return self.__applicationInformation
    
    __userInformation = None
    def userInformation (self):
        return self.__userInformation

    # Define so superclasses can take keywords
    def __init__ (self, **kw):
        super(Annotation, self).__init__(**kw)

    def _dependentComponents_vx (self):
        """Implement base class method.

        Annotations depend on nothing.
        """
        return frozenset()

    # @todo: what the hell is this?  From 3.13.2, I think it's a place
    # to stuff attributes from the annotation element, which makes
    # sense, as well as from the annotation's parent element, which
    # doesn't.  Apparently it's for attributes that don't belong to
    # the XMLSchema namespace; so maybe we're not supposed to add
    # those to the other components.  Note that these are attribute
    # information items, not attribute uses.
    __attributes = None

    # CFD:Annotation
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        rv = cls(node=node, **kw)

        # @todo:: Scan for attributes in the node itself that do not
        # belong to the XMLSchema namespace.

        # Node should be an XMLSchema annotation node
        assert xsd.nodeIsNamed(node, 'annotation')
        app_info = []
        user_info = []
        for cn in node.childNodes:
            if xsd.nodeIsNamed(cn, 'appinfo'):
                app_info.append(cn)
            elif xsd.nodeIsNamed(cn, 'documentation'):
                user_info.append(cn)
            else:
                pass
        if 0 < len(app_info):
            rv.__applicationInformation = app_info
        if 0 < len(user_info):
            rv.__userInformation = user_info

        return rv

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
class SimpleTypeDefinition (_SchemaComponent_mixin, _NamedComponent_mixin, pyxb.namespace._Resolvable_mixin, _Annotated_mixin):
    """The schema component for simple type definitions.

    This component supports the basic datatypes of XML schema, and
    those that define the values for attributes.
    """

    # Reference to the SimpleTypeDefinition on which this is based.
    # The value must be non-None except for the simple ur-type
    # definition.
    __baseTypeDefinition = None
    def baseTypeDefinition (self):
        return self.__baseTypeDefinition

    # A map from a subclass of facets.Facet to an instance of that class.
    # Presence of a facet class as a key in this map is the indicator that the
    # type definition and its subtypes are permitted to use the corresponding
    # facet.  All facets in force for this type are present in the map,
    # including those constraints inherited parent types.
    __facets = None
    def facets (self):
        assert (self.__facets is None) or (type(self.__facets) == types.DictType)
        return self.__facets

    # The facets.FundamentalFacet instances that describe this type
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
            raise pyxb.BadPropertyError('[%s] primitiveTypeDefinition only defined for atomic types' % (self.name(), self.variety()))
        if self.__primitiveTypeDefinition is None:
            raise pyxb.LogicError('Expected primitive type')
        return self.__primitiveTypeDefinition

    # For list variety only, the type of items in the list
    __itemTypeDefinition = None
    def itemTypeDefinition (self):
        if self.VARIETY_list != self.variety():
            raise pyxb.BadPropertyError('itemTypeDefinition only defined for list types')
        if self.__itemTypeDefinition is None:
            raise pyxb.LogicError('Expected item type')
        return self.__itemTypeDefinition

    # For union variety only, the sequence of candidate members
    __memberTypeDefinitions = None
    def memberTypeDefinitions (self):
        if self.VARIETY_union != self.variety():
            raise pyxb.BadPropertyError('memberTypeDefinitions only defined for union types')
        if self.__memberTypeDefinitions is None:
            raise pyxb.LogicError('Expected member types')
        return self.__memberTypeDefinitions

    def _dependentComponents_vx (self):
        """Implement base class method.

        This STD depends on its baseTypeDefinition, unless its variety
        is absent.  Other dependencies are on item, primitive, or
        member type definitions."""
        type_definitions = set()
        if self != self.baseTypeDefinition():
            type_definitions.add(self.baseTypeDefinition())
        if self.VARIETY_absent == self.variety():
            type_definitions = set()
        elif self.VARIETY_atomic == self.variety():
            if self != self.primitiveTypeDefinition():
                type_definitions.add(self.primitiveTypeDefinition())
        elif self.VARIETY_list == self.variety():
            assert self != self.itemTypeDefinition()
            type_definitions.add(self.itemTypeDefinition())
        elif self.VARIETY_union == self.variety():
            assert self not in self.memberTypeDefinitions()
            type_definitions.update(self.memberTypeDefinitions())
        else:
            raise pyxb.LogicError('Unable to identify dependent types: variety %s' % (self.variety(),))
        # NB: This type also depends on the value type definitions for
        # any facets that apply to it.  This fact only matters when
        # generating the datatypes_facets source.  That, and the fact
        # that there are dependency loops (e.g., integer requires a
        # nonNegativeInteger for its length facet) means we don't
        # bother adding in those.
        return frozenset(type_definitions)
        
    # A non-property field that holds a reference to the DOM node from
    # which the type is defined.  The value is held only between the
    # point where the simple type definition instance is created until
    # the point it is resolved.
    __domNode = None
    
    # Indicate that this instance was defined as a built-in rather
    # than from a DOM instance.
    __isBuiltin = False

    # Allocate one of these.  Users should use one of the Create*
    # factory methods instead.
    def __init__ (self, *args, **kw):
        super(SimpleTypeDefinition, self).__init__(*args, **kw)
        self.__variety = kw['variety']

    def __setstate__ (self, state):
        """Extend base class unpickle support to retain link between
        this instance and the Python class that it describes.

        This is because the pythonSupport value is a class reference,
        not an instance reference, so it wasn't deserialized, and its
        class member link was never set.
        """
        super_fn = getattr(super(SimpleTypeDefinition, self), '__setstate__', lambda _state: self.__dict__.update(_state))
        super_fn(state)
        if self.__pythonSupport is not None:
            self.__pythonSupport._SimpleTypeDefinition(self)

    def __str__ (self):
        if self.name() is not None:
            elts = [ self.name(), ': ' ]
        else:
            elts = [ '<anonymous>:' ]
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
            #raise pyxb.LogicError('Unexpected variety %s' % (self.variety(),))
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

    def _setBuiltinFromInstance (self, other):
        """Override fields in this instance with those from the other.

        This method is invoked only by Schema._addNamedComponent, and
        then only when a built-in type collides with a schema-defined
        type.  Material like facets is not (currently) held in the
        built-in copy, so the DOM information is copied over to the
        built-in STD, which is subsequently re-resolved.

        Returns self.
        """
        assert self != other
        assert self.isNameEquivalent(other)
        super(SimpleTypeDefinition, self)._setBuiltinFromInstance(other)

        # The other STD should be an unresolved schema-defined type.
        assert other.__baseTypeDefinition is None
        assert other.__domNode is not None
        self.__domNode = other.__domNode

        # Preserve the python support
        if other.__pythonSupport is not None:
            # @todo: ERROR multiple references
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

        #if in_builtin_definition and (cls.__SimpleUrTypeDefinition is not None):
        #    raise pyxb.LogicError('Multiple definitions of SimpleUrType')
        if cls.__SimpleUrTypeDefinition is None:
            # Note: We use a singleton subclass
            bi = _SimpleUrTypeDefinition(name='anySimpleType', namespace_context=pyxb.namespace.XMLSchema.initialNamespaceContext(), variety=cls.VARIETY_absent, scope=_ScopedDeclaration_mixin.XSCOPE_indeterminate)
            bi._setPythonSupport(datatypes.anySimpleType)

            # The baseTypeDefinition is the ur-type.
            bi.__baseTypeDefinition = ComplexTypeDefinition.UrTypeDefinition()
            # The simple ur-type has an absent variety, not an atomic
            # variety, so does not have a primitiveTypeDefinition

            # No facets on the ur type
            bi.__facets = {}
            bi.__fundamentalFacets = frozenset()

            bi.__resolveBuiltin()

            cls.__SimpleUrTypeDefinition = bi
        return cls.__SimpleUrTypeDefinition

    @classmethod
    def CreatePrimitiveInstance (cls, name, schema, python_support):
        """Create a primitive simple type in the target namespace.

        This is mainly used to pre-load standard built-in primitive
        types, such as those defined by XMLSchema Datatypes.  You can
        use it for your own schemas as well, if you have special types
        that require explicit support to for Pythonic conversion.

        All parameters are required and must be non-None.
        """
        
        bi = cls(name=name, namespace_context=schema.targetNamespace().initialNamespaceContext(), variety=cls.VARIETY_atomic, scope=_ScopedDeclaration_mixin.XSCOPE_indeterminate)
        bi._setPythonSupport(python_support)

        # Primitive types are based on the ur-type, and have
        # themselves as their primitive type definition.
        bi.__baseTypeDefinition = cls.SimpleUrTypeDefinition()
        bi.__primitiveTypeDefinition = bi

        # Primitive types are built-in
        bi.__resolveBuiltin()
        assert bi.isResolved()
        return bi

    @classmethod
    def CreateDerivedInstance (cls, name, schema, parent_std, python_support):
        """Create a derived simple type in the target namespace.

        This is used to pre-load standard built-in derived types.  You
        can use it for your own schemas as well, if you have special
        types that require explicit support to for Pythonic
        conversion.
        """
        assert parent_std
        assert parent_std.__variety in (cls.VARIETY_absent, cls.VARIETY_atomic)
        bi = cls(name=name, namespace_context=schema.targetNamespace().initialNamespaceContext(), variety=parent_std.__variety, scope=_ScopedDeclaration_mixin.XSCOPE_indeterminate)
        bi._setPythonSupport(python_support)

        # We were told the base type.  If this is atomic, we re-use
        # its primitive type.  Note that these all may be in different
        # namespaces.
        bi.__baseTypeDefinition = parent_std
        if cls.VARIETY_atomic == bi.__variety:
            bi.__primitiveTypeDefinition = bi.__baseTypeDefinition.__primitiveTypeDefinition

        # Derived types are built-in
        bi.__resolveBuiltin()
        return bi

    @classmethod
    def CreateListInstance (cls, name, schema, item_std, python_support):
        """Create a list simple type in the target namespace.

        This is used to preload standard built-in list types.  You can
        use it for your own schemas as well, if you have special types
        that require explicit support to for Pythonic conversion; but
        note that such support is identified by the item_std.
        """
        bi = cls(name=name, namespace_context=schema.targetNamespace().initialNamespaceContext(), variety=cls.VARIETY_list, scope=_ScopedDeclaration_mixin.XSCOPE_indeterminate)
        bi._setPythonSupport(python_support)

        # The base type is the ur-type.  We were given the item type.
        bi.__baseTypeDefinition = cls.SimpleUrTypeDefinition()
        assert item_std
        bi.__itemTypeDefinition = item_std

        # List types are built-in
        bi.__resolveBuiltin()
        return bi

    @classmethod
    def CreateUnionInstance (cls, name, schema, member_stds):
        """(Placeholder) Create a union simple type in the target namespace.

        This function has not been implemented."""
        raise pyxb.IncompleteImplementationError('No support for built-in union types')

    def __singleSimpleTypeChild (self, body):
        simple_type_child = None
        for cn in body.childNodes:
            if (Node.ELEMENT_NODE == cn.nodeType):
                assert xsd.nodeIsNamed(cn, 'simpleType')
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

    def __initializeFromList (self, body):
        self.__baseTypeDefinition = self.SimpleUrTypeDefinition()
        return self.__completeResolution(body, self.VARIETY_list, 'list')

    def __initializeFromRestriction (self, body):
        base_attr = NodeAttribute(body, 'base')
        if base_attr is not None:
            # Look up the base.  If there is no registered type of
            # that name, an exception gets thrown that percolates up
            # to the user.
            base_en = self._namespaceContext().interpretQName(base_attr)
            base_type = base_en.typeDefinition()
            if not isinstance(base_type, SimpleTypeDefinition):
                raise pyxb.SchemaValidationError('Unable to locate base type %s' % (base_en,))
            # If the base type exists but has not yet been resolve,
            # delay processing this type until the one it depends on
            # has been completed.
            if not base_type.isResolved():
                self._queueForResolution()
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
        return self.__completeResolution(body, variety, 'restriction')

    def __initializeFromUnion (self, body):
        self.__baseTypeDefinition = self.SimpleUrTypeDefinition()
        return self.__completeResolution(body, self.VARIETY_union, 'union')

    def __resolveBuiltin (self):
        if self.hasPythonSupport():
            self.__facets = { }
            for v in self.pythonSupport().__dict__.values():
                if isinstance(v, facets.ConstrainingFacet):
                    #print 'Adding facet %s to %s' % (v, self.name())
                    self.__facets[v.__class__] = v
                    if v.ownerTypeDefinition() is None:
                        v.setFromKeywords(_constructor=True, owner_type_definition=self)
        self.__isBuiltin = True
        return self

    def __defineDefaultFacets (self, variety):
        """Create facets for varieties that can take facets that are undeclared.

        This means unions, which per section 4.1.2.3 of
        http://www.w3.org/TR/xmlschema-2/ can have enumeration or
        pattern restrictions."""
        if self.VARIETY_union != variety:
            return self
        self.__facets.setdefault(facets.CF_pattern)
        self.__facets.setdefault(facets.CF_enumeration)
        return self

    def __processHasFacetAndProperty (self, variety):
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
            return self.__defineDefaultFacets(variety)
        app_info = self.annotation().applicationInformation()
        if app_info is  None:
            return self.__defineDefaultFacets(variety)
        facet_map = { }
        fundamental_facets = set()
        seen_facets = set()
        for ai in app_info:
            for cn in ai.childNodes:
                if Node.ELEMENT_NODE != cn.nodeType:
                    continue
                if pyxb.namespace.XMLSchema_hfp.nodeIsNamed(cn, 'hasFacet'):
                    facet_name = NodeAttribute(cn, 'name', pyxb.namespace.XMLSchema_hfp)
                    if facet_name is None:
                        raise pyxb.SchemaValidationError('hasFacet missing name attribute')
                    if facet_name in seen_facets:
                        raise pyxb.SchemaValidationError('Multiple hasFacet specifications for %s' % (facet_name,))
                    seen_facets.add(facet_name)
                    facet_class = facets.ConstrainingFacet.ClassForFacet(facet_name)
                    #facet_map[facet_class] = facet_class(base_type_definition=self)
                    facet_map[facet_class] = None
                if pyxb.namespace.XMLSchema_hfp.nodeIsNamed(cn, 'hasProperty'):
                    fundamental_facets.add(facets.FundamentalFacet.CreateFromDOM(cn, self))
        if 0 < len(facet_map):
            assert self.__baseTypeDefinition == self.SimpleUrTypeDefinition()
            self.__facets = facet_map
            assert type(self.__facets) == types.DictType
        if 0 < len(fundamental_facets):
            self.__fundamentalFacets = frozenset(fundamental_facets)
        return self

    def __updateFacets (self, body):
        # We want a map from the union of the facet classes from this STD up
        # through its baseTypeDefinition (if present).  Map elements should be
        # to None if the facet has not been constrained, or to the nearest
        # ConstrainingFacet instance if it is.  ConstrainingFacet instances
        # created for local constraints also need a pointer to the
        # corresponding facet from the ancestor type definition, because those
        # constraints also affect this type.
        base_facets = {}

        # Built-ins didn't get their facets() setting configured, so use the
        # _FacetMap() instead.
        if self.__baseTypeDefinition.isBuiltin():
            pstd = self.__baseTypeDefinition.pythonSupport()
            if pstd != datatypes.anySimpleType:
                base_facets.update(pstd._FacetMap())
        elif self.__baseTypeDefinition.facets():
            assert type(self.__baseTypeDefinition.facets()) == types.DictType
            base_facets.update(self.__baseTypeDefinition.facets())
        base_facets.update(self.facets())

        local_facets = {}
        for fc in base_facets.keys():
            children = LocateMatchingChildren(body, fc.Name())
            fi = base_facets[fc]
            if 0 < len(children):
                fi = fc(base_type_definition=self.__baseTypeDefinition,
                        owner_type_definition=self,
                        super_facet=fi)
                if isinstance(fi, facets._LateDatatype_mixin):
                    fi.bindValueDatatype(self)
                for cn in children:
                    kw = { 'annotation': LocateUniqueChild(cn, 'annotation') }
                    for ai in range(0, cn.attributes.length):
                        attr = cn.attributes.item(ai)
                        # Convert name from unicode to string
                        kw[str(attr.name)] = attr.value
                    #print 'set %s from %s' % (fi.Name(), kw)
                    fi.setFromKeywords(**kw)
            local_facets[fc] = fi
        self.__facets = local_facets
        assert type(self.__facets) == types.DictType

    # Complete the resolution of some variety of STD.  Note that the
    # variety is compounded by an alternative, since there is no
    # 'restriction' variety.
    def __completeResolution (self, body, variety, alternative):
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
                if (ptd != self) and (not ptd.isResolved()):
                    assert False
                    self._queueForResolution()
                    return self
                self.__primitiveTypeDefinition = ptd
        elif self.VARIETY_list == variety:
            if 'list' == alternative:
                it_attr = NodeAttribute(body, 'itemType')
                if it_attr is not None:
                    it_en = self._namespaceContext().interpretQName(it_attr)
                    self.__itemTypeDefinition = it_en.typeDefinition()
                    if not isinstance(self.__itemTypeDefinition, SimpleTypeDefinition):
                        raise pyxb.InvalidSchemaError('Unable to locate STD %s for items' % (it_en,))
                else:
                    # NOTE: The newly created anonymous item type will
                    # not be resolved; the caller needs to handle
                    # that.
                    self.__itemTypeDefinition = self.CreateFromDOM(self.__singleSimpleTypeChild(body), owner=self)
            elif 'restriction' == alternative:
                self.__itemTypeDefinition = self.__baseTypeDefinition.__itemTypeDefinition
            else:
                raise pyxb.LogicError('completeResolution list variety with alternative %s' % (alternative,))
        elif self.VARIETY_union == variety:
            if 'union' == alternative:
                # First time we try to resolve, create the member type
                # definitions.  If something later prevents us from
                # resolving this type, we don't want to create them
                # again, because we might already have references to
                # them.
                if self.__memberTypeDefinitions is None:
                    mtd = []
                    # If present, first extract names from memberTypes,
                    # and add each one to the list
                    member_types = NodeAttribute(body, 'memberTypes')
                    if member_types is not None:
                        for mn in member_types.split():
                            # THROW if type has not been defined
                            mn_en = self._namespaceContext().interpretQName(mn)
                            std = mn_en.typeDefinition()
                            if std is None:
                                raise pyxb.InvalidSchemaError('Unable to locate member type %s' % (mn_en,))
                            assert isinstance(std, SimpleTypeDefinition)
                            mtd.append(std)
                    # Now look for local type definitions
                    for cn in body.childNodes:
                        if (Node.ELEMENT_NODE == cn.nodeType):
                            if xsd.nodeIsNamed(cn, 'simpleType'):
                                # NB: Attempt resolution right away to
                                # eliminate unnecessary delay below
                                # when looking for union expansions.
                                mtd.append(self.CreateFromDOM(cn, owner=self)._resolve())
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
                        self._queueForResolution()
                        return self
                    if self.VARIETY_union == mt.variety():
                        mtd.extend(mt.memberTypeDefinitions())
                    else:
                        mtd.append(mt)
            elif 'restriction' == alternative:
                assert self.__baseTypeDefinition
                # Base type should have been resolved before we got here
                assert self.__baseTypeDefinition.isResolved()
                mtd = self.__baseTypeDefinition.__memberTypeDefinitions
                assert mtd is not None
            else:
                raise pyxb.LogicError('completeResolution union variety with alternative %s' % (alternative,))
            # Save a unique copy
            self.__memberTypeDefinitions = mtd[:]
        else:
            print 'VARIETY "%s"' % (variety,)
            raise pyxb.LogicError('completeResolution with variety 0x%02x' % (variety,))

        # Determine what facets, if any, apply to this type.  This
        # should only do something if this is a primitive type.
        self.__processHasFacetAndProperty(variety)
        self.__updateFacets(body)

        self.__variety = variety
        self.__domNode = None
        #print 'Completed STD %s' % (self,)
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

    def _resolve (self):
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
        candidate = LocateUniqueChild(node, 'list')
        if candidate:
            self.__initializeFromList(candidate)

        candidate = LocateUniqueChild(node, 'restriction')
        if candidate:
            if self.__variety is None:
                self.__initializeFromRestriction(candidate)
            else:
                bad_instance = True

        candidate = LocateUniqueChild(node, 'union')
        if candidate:
            if self.__variety is None:
                self.__initializeFromUnion(candidate)
            else:
                bad_instance = True

        # It is NOT an error to fail to resolve the type.
        if bad_instance:
            raise pyxb.SchemaValidationError('Expected exactly one of list, restriction, union as child of simpleType')

        return self

    # CFD:STD CFD:SimpleTypeDefinition
    @classmethod
    def CreateFromDOM (cls, node, **kw):
        # Node should be an XMLSchema simpleType node
        assert xsd.nodeIsNamed(node, 'simpleType')

        # @todo: Process "final" attributes
        
        if NodeAttribute(node, 'final') is not None:
            raise pyxb.IncompleteImplementationError('"final" attribute not currently supported')

        name = NodeAttribute(node, 'name')

        rv = cls(name=name, node=node, variety=None, **kw)
        rv._annotationFromDOM(node)

        # @todo: identify supported facets and properties (hfp)

        # Creation does not attempt to do resolution.  Queue up the newly created
        # whatsis so we can resolve it after everything's been read in.
        rv.__domNode = node
        rv._queueForResolution()
        
        return rv

    # pythonSupport is None, or a subclass of datatypes._PSTS_mixin.
    # When set, this simple type definition instance must be uniquely
    # associated with the PST class using
    # _PSTS_mixin._SimpleTypeDefinition().
    __pythonSupport = None

    def _setPythonSupport (self, python_support):
        # Includes check that python_support is not None
        assert issubclass(python_support, basis.simpleTypeDefinition)
        # Can't share support instances
        self.__pythonSupport = python_support
        self.__pythonSupport._SimpleTypeDefinition(self)
        if self.nameInBinding() is None:
            self.setNameInBinding(self.__pythonSupport.__name__)
        return self.__pythonSupport

    def hasPythonSupport (self):
        return self.__pythonSupport is not None

    def pythonSupport (self):
        if self.__pythonSupport is None:
            raise pyxb.LogicError('%s: No support defined' % (self.name(),))
        return self.__pythonSupport

    def stringToPython (self, string):
        return self.pythonSupport().stringToPython(string)

    def pythonToString (self, value):
        return self.pythonSupport().pythonToString(value)

class _SimpleUrTypeDefinition (SimpleTypeDefinition, _Singleton_mixin):
    """Subclass ensures there is only one simple ur-type."""
    def _dependentComponents_vx (self):
        """The SimpleUrTypeDefinition is not dependent on anything."""
        return frozenset()

class _ImportElementInformationItem (_Annotated_mixin):
    """A class representing an import statement within a schema.

    See section 4.2.3."""

    def id (self):
        """The value of the id attribute from the import statement."""
        return self.__id
    __id = None

    def namespace (self):
        """The Namespace instance corresponding to the value of the
        namespace attribute from the import statement."""
        return self.__namespace
    __namespace = None

    def schemaLocation (self):
        """The value of the schemaLocation attribute from the import statement."""
        return self.__schemaLocation
    __schemaLocation = None

    def prefix (self):
        """A prefix to be used for this namespace.

        The value is inferred from an XML Namespace declaration in the
        enclosing schema.  If no such declaration can be found, a
        prefix is assigned using the form "imported_#" where "#" makes
        the prefix unique within the enclosing schema.

        The prefix is used in generated bindings as the module
        reference for the imported namespace.
        """
        return self.__prefix
    def setPrefix (self, prefix):
        """Allow override of the import prefix."""
        self.__prefix = prefix
    __prefix = None
    
    def schema (self):
        return self.__schema
    __schema = None

    def __init__ (self, schema, node, **kw):
        super(_ImportElementInformationItem, self).__init__(**kw)
        uri = NodeAttribute(node, 'namespace')
        if uri is None:
            raise pyxb.IncompleteImplementationError('import statements without namespace not supported')
        self.__schemaLocation = NodeAttribute(node, 'schemaLocation')
        self.__namespace = pyxb.namespace.NamespaceForURI(uri, create_if_missing=True)
        if uri in pyxb.namespace.AvailableForLoad():
            try:
                self.__namespace.validateComponentModel()
            except Exception, e:
                print 'ERROR validating imported namespace %s: %s' % (uri, e)

            # @todo: validate that something got loaded
        elif self.schemaLocation() is not None:
            print 'Attempt to read %s from %s' % (uri, self.schemaLocation())
            ns_ctx = pyxb.namespace.NamespaceContext.GetNodeContext(node)
            try:
                xmls = urllib2.urlopen(self.schemaLocation()).read()
            except ValueError, e:
                print 'Caught with urllib: %s' % (e,)
                xmls = open(self.schemaLocation()).read()
            dom = StringToDOM(xmls)
            self.__schema = Schema.CreateFromDOM(dom, ns_ctx)

        self._annotationFromDOM(node)

class Schema (_SchemaComponent_mixin):
    # List of annotations
    __annotations = None

    # True when we have started seeing elements, attributes, or
    # notations.
    __pastProlog = False

    def targetNamespace (self):
        """The targetNamespace of a componen.

        This is None, or a reference to a Namespace in which the
        component is declared (either as a global or local to one of
        the namespace's complex type definitions).  This is immutable
        after creation.
        """
        return self.__targetNamespace
    __targetNamespace = None
    
    def defaultNamespace (self):
        """Default namespace of the schema.

        Will be None unless the schema has an 'xmlns' attribute.  The
        value must currently be provided as a keyword parameter to the
        constructor.  """
        return self.__defaultNamespace
    __defaultNamespace = None

    def importedNamespaces (self):
        """The list of Namespace instances that were imported into this schema."""
        return self.__importedNamespaces
    __importedNamespaces = None

    # Tuple of component classes in order in which they must be generated in
    # order to satisfy the Python references between bindings.
    # 
    __ComponentOrder = (
        Annotation                   # no dependencies
      , IdentityConstraintDefinition # no dependencies
      , NotationDeclaration          # no dependencies
      , Wildcard                     # no dependencies
      , SimpleTypeDefinition         # no dependencies
      , AttributeDeclaration         # SimpleTypeDefinition
      , AttributeUse                 # AttributeDeclaration
      , AttributeGroupDefinition     # AttributeUse
      , ComplexTypeDefinition        # SimpleTypeDefinition, AttributeUse
      , ElementDeclaration           # *TypeDefinition
      , ModelGroup                   # ComplexTypeDefinition, ElementDeclaration, Wildcard
      , ModelGroupDefinition         # ModelGroup
      , Particle                     # ModelGroup, WildCard, ElementDeclaration
        )

    def _dependentComponents_vx (self):
        """Implement base class method.

        The schema as a whole depends on nothing (that we have any
        control over, at least).
        """
        return frozenset()

    def orderedComponents (self):
        assert self.completedResolution()
        return self.targetNamespace().orderedComponents(self.__ComponentOrder)

    def completedResolution (self):
        """Return True iff all resolvable elements have been resolved.

        After this point, nobody should be messing with the any of the
        definition or declaration maps."""
        return self.targetNamespace()._unresolvedComponents() is None

    _QUALIFIED = "qualified"
    _UNQUALIFIED = "unqualified"
    
    # Default values for standard recognized schema attributes
    __attributeMap = { 'attributeFormDefault' : _UNQUALIFIED
                     , 'elementFormDefault' : _UNQUALIFIED
                     , 'blockDefault' : ''
                     , 'finalDefault' : ''
                     , 'id' : None
                     , 'targetNamespace' : None
                     , 'version' : None
                     , 'xml:lang' : None
                     } 

    def _setAttributeFromDOM (self, attr):
        """Override the schema attribute with the given DOM value."""
        self.__attributeMap[attr.name] = attr.nodeValue
        return self

    def _setAttributesFromMap (self, attr_map):
        """Override the schema attributes with values from the given map."""
        self.__attributeMap.update(attr_map)
        return self

    def schemaHasAttribute (self, attr_name):
        """Return True iff the schema has an attribute with the given (nc)name."""
        return self.__attributeMap.has_key(attr_name)

    def schemaAttribute (self, attr_name):
        """Return the schema attribute value associated with the given (nc)name."""
        return self.__attributeMap[attr_name]

    __SchemaCategories = ( 'typeDefinition', 'attributeGroupDefinition', 'modelGroupDefinition',
                           'attributeDeclaration', 'elementDeclaration', 'notationDeclaration',
                           'identityConstraintDefinition' )

    def __init__ (self, *args, **kw):
        assert 'schema' not in kw
        super(Schema, self).__init__(*args, **kw)
        self.__targetNamespace = kw.get('target_namespace', self._namespaceContext().targetNamespace())
        if not isinstance(self.__targetNamespace, pyxb.namespace.Namespace):
            raise pyxb.LogicError('Schema constructor requires valid Namespace instance as target_namespace')
        self.__defaultNamespace = kw.get('default_namespace', self._namespaceContext().defaultNamespace())
        if not ((self.__defaultNamespace is None) or isinstance(self.__defaultNamespace, pyxb.namespace.Namespace)):
            raise pyxb.LogicError('Schema default namespace must be None or a valid Namespace instance')

        self.__targetNamespace.configureCategories(self.__SchemaCategories)
        if self.__defaultNamespace is not None:
            self.__defaultNamespace.configureCategories(self.__SchemaCategories)

        self.__attributeMap = self.__attributeMap.copy()
        self.__annotations = [ ]
        self.__importedNamespaces = []

    __TopLevelComponentMap = {
        'element' : ElementDeclaration,
        'attribute' : AttributeDeclaration,
        'notation' : NotationDeclaration,
        'simpleType' : SimpleTypeDefinition,
        'complexType' : ComplexTypeDefinition,
        'group' : ModelGroupDefinition,
        'attributeGroup' : AttributeGroupDefinition
        }

    # @todo: put these in base class
    @classmethod
    def CreateFromDOM (cls, node, namespace_context=None, inherit_default_namespace=False, skip_resolution=False):
        """Take the root element of the document, and scan its attributes under
        the assumption it is an XMLSchema schema element.  That means
        recognize namespace declarations and process them.  Also look for
        and set the default namespace.  All other attributes are passed up
        to the parent class for storage."""

        default_namespace = None
        root_node = node
        if Node.DOCUMENT_NODE == node.nodeType:
            root_node = root_node.documentElement
        if Node.ELEMENT_NODE != root_node.nodeType:
            raise pyxb.LogicError('Must be given a DOM node of type ELEMENT')

        assert (namespace_context is None) or isinstance(namespace_context, pyxb.namespace.NamespaceContext)
        ns_ctx = pyxb.namespace.NamespaceContext(root_node, parent_context=namespace_context)

        tns = ns_ctx.targetNamespace()
        assert tns is not None
        schema = cls(namespace_context=ns_ctx)
        schema.__namespaceData = ns_ctx
            
        assert schema.targetNamespace() == ns_ctx.targetNamespace()
        assert schema.defaultNamespace() == ns_ctx.defaultNamespace()

        # Update the attribute map
        schema._setAttributesFromMap(ns_ctx.attributeMap())

        # Verify that the root node is an XML schema element
        if not xsd.nodeIsNamed(root_node, 'schema'):
            raise pyxb.SchemaValidationError('Root node %s of document is not an XML schema element' % (root_node.nodeName,))

        for cn in root_node.childNodes:
            if Node.ELEMENT_NODE == cn.nodeType:
                rv = schema.__processTopLevelNode(cn)
                if rv is None:
                    print 'Unrecognized: %s %s' % (cn.nodeName, cn.toxml())
            elif Node.TEXT_NODE == cn.nodeType:
                # Non-element content really should just be whitespace.
                # If something else is seen, print it for inspection.
                text = cn.data.strip()
                if text:
                    print 'Ignored text: %s' % (text,)
            elif Node.COMMENT_NODE == cn.nodeType:
                #print 'comment: %s' % (cn.data.strip(),)
                pass
            else:
                # ATTRIBUTE_NODE
                # CDATA_SECTION_NODE
                # ENTITY_NODE
                # PROCESSING_INSTRUCTION
                # DOCUMENT_NODE
                # DOCUMENT_TYPE_NODE
                # NOTATION_NODE
                print 'Ignoring non-element: %s' % (cn,)

        if not skip_resolution:
            schema.targetNamespace().resolveDefinitions(schema)

        return schema

    def targetNamespaceForNode (self, dom_node, declaration_type):
        """Determine the target namespace for a local attribute or element declaration.

        Look at the node's C{form} attribute, or if none the schema's
        C{attributeFormDefault} or C{elementFormDefault} value.  If the
        resulting value is C{"qualified"} and the parent schema has a
        non-absent target namespace, return it to use as the declaration
        target namespace.  Otherwise, return None to indicate that the
        declaration has no namespace.

        @param dom_node: The node defining an element or attribute declaration
        @param declaration_type: Either L{AttributeDeclaration} or L{ElementDeclaration}
        @return: L{pyxb.namespace.Namespace} or None
        """

        form_type = None
        if dom_node.hasAttributeNS(xml.dom.EMPTY_NAMESPACE, 'form'):
            form_type = dom_node.getAttributeNS(xml.dom.EMPTY_NAMESPACE, 'form')
        if form_type is None:
            if declaration_type == ElementDeclaration:
                form_type = self.schemaAttribute('elementFormDefault')
            elif declaration_type == AttributeDeclaration:
                form_type = self.schemaAttribute('attributeFormDefault')
            else:
                raise LogicError('Expected ElementDeclaration or AttributeDeclaration: got %s' % (declaration_type,))
        tns = None
        if (self._QUALIFIED == form_type):
            tns = self.targetNamespace()
            if tns.isAbsentNamespace():
                tns = None
        else:
            if (self._UNQUALIFIED != form_type):
                raise pyxb.SchemaValidationError('Form type neither %s nor %s' % (self._QUALIFIED, self._UNQUALIFIED))
        return tns

    def __requireInProlog (self, node_name):
        """Throw a SchemaValidationException referencing the given
        node if we have passed the sequence point representing the end
        of prolog elements."""
        
        if self.__pastProlog:
            print '%s past prolog' % (object.__str__(self),)
            raise pyxb.SchemaValidationError('Unexpected node %s after prolog' % (node_name,))

    def __processInclude (self, node):
        self.__requireInProlog(node.nodeName)
        # See section 4.2.1 of Structures.
        uri = NodeAttribute(node, 'schemaLocation')
        xml = urllib2.urlopen(uri).read()
        included_schema = self.CreateFromDOM(StringToDOM(xml), self.__namespaceData, inherit_default_namespace=True, skip_resolution=True)
        print '%s completed including %s' % (object.__str__(self), object.__str__(included_schema))
        assert self.targetNamespace() == included_schema.targetNamespace()
        #print xml
        return node

    def __processImport (self, node):
        """Process an import directive.

        This attempts to locate schema (named entity) information for
        a namespace that is referenced by this schema.
        """

        self.__requireInProlog(node.nodeName)
        import_eii = _ImportElementInformationItem(self, node)
        ns_map = pyxb.namespace.NamespaceContext.GetNodeContext(node).inScopeNamespaces()
        for (pfx, ns) in ns_map.items():
            if import_eii.namespace() == ns:
                import_eii.setPrefix(pfx)
                break
        if import_eii.prefix() is None:
            print 'NO PREFIX FOR %s'
        print 'Imported %s, prefix %s, %d types' % (import_eii.namespace().uri(), import_eii.prefix(), len(import_eii.namespace().typeDefinitions()))
        self.__importedNamespaces.append(import_eii)
        return node

    def __processRedefine (self, node):
        self.__requireInProlog(node.nodeName)
        raise IncompleteImplementationException('redefine not implemented')

    def __processAnnotation (self, node):
        an = self._addAnnotation(Annotation.CreateFromDOM(node))
        return self

    def __processTopLevelNode (self, node):
        """Process a DOM node from the top level of the schema.

        This should return a non-None value if the node was
        successfully recognized."""
        if xsd.nodeIsNamed(node, 'include'):
            return self.__processInclude(node)
        if xsd.nodeIsNamed(node, 'import'):
            return self.__processImport(node)
        if xsd.nodeIsNamed(node, 'redefine'):
            return self.__processRedefine(node)
        if xsd.nodeIsNamed(node, 'annotation'):
            return self.__processAnnotation(node)

        component = self.__TopLevelComponentMap.get(node.localName)
        if component is not None:
            self.__pastProlog = True
            kw = { 'context' : _ScopedDeclaration_mixin.SCOPE_global,
                   'scope' : _ScopedDeclaration_mixin.XSCOPE_indeterminate,
                   'owner' : self }
            if issubclass(component, _ScopedDeclaration_mixin):
                kw['scope'] = _ScopedDeclaration_mixin.SCOPE_global
            return self._addNamedComponent(component.CreateFromDOM(node, **kw))

        raise pyxb.SchemaValidationError('Unexpected top-level element %s' % (node.nodeName,))

    def __replaceUnresolvedDefinition (self, existing_def, replacement_def):
        unresolved_components = self.targetNamespace()._unresolvedComponents()
        assert existing_def in unresolved_components
        unresolved_components.remove(existing_def)
        assert replacement_def not in unresolved_components
        assert isinstance(replacement_def, pyxb.namespace._Resolvable_mixin)
        unresolved_components.append(replacement_def)
        # Throw away the reference to the previous component and use
        # the replacement one
        return self.targetNamespace()._replaceComponent(existing_def, replacement_def)

    def _addAnnotation (self, annotation):
        self.__annotations.append(annotation)
        return annotation

    def _addNamedComponent (self, nc):
        tns = self.targetNamespace()
        assert tns is not None
        if not isinstance(nc, _NamedComponent_mixin):
            raise pyxb.LogicError('Attempt to add unnamed %s instance to dictionary' % (nc.__class__,))
        if nc.isAnonymous():
            raise pyxb.LogicError('Attempt to add anonymous component to dictionary: %s', (nc.__class__,))
        if isinstance(nc, _ScopedDeclaration_mixin):
            assert _ScopedDeclaration_mixin.SCOPE_global == nc.scope()
        #print 'Adding %s as %s' % (nc.__class__.__name__, nc.name())
        if isinstance(nc, (SimpleTypeDefinition, ComplexTypeDefinition)):
            return self.__addTypeDefinition(nc)
        if isinstance(nc, AttributeDeclaration):
            return self.__addAttributeDeclaration(nc)
        if isinstance(nc, AttributeGroupDefinition):
            return tns.addCategoryObject('attributeGroupDefinition', nc.name(), nc)
        if isinstance(nc, ModelGroupDefinition):
            return tns.addCategoryObject('modelGroupDefinition', nc.name(), nc)
        if isinstance(nc, ElementDeclaration):
            return tns.addCategoryObject('elementDeclaration', nc.name(), nc)
        if isinstance(nc, NotationDeclaration):
            return tns.addCategoryObject('notationDeclaration', nc.name(), nc)
        if isinstance(nc, IdentityConstraintDefinition):
            return tns.addCategoryObject('identityConstraintDefinition', nc.name(), nc)
        raise pyxb.IncompleteImplementationError('No support to record named component of type %s' % (nc.__class__,))

    def __addTypeDefinition (self, td):
        local_name = td.name()
        assert self.__targetNamespace
        tns = self.targetNamespace()
        old_td = tns.typeDefinitions().get(local_name)
        if (old_td is not None) and (old_td != td):
            # @todo: validation error if old_td is not a built-in
            if isinstance(td, ComplexTypeDefinition) != isinstance(old_td, ComplexTypeDefinition):
                raise pyxb.SchemaValidationError('Name %s used for both simple and complex types' % (td.name(),))
            # Copy schema-related information from the new definition
            # into the old one, and continue to use the old one.
            td = self.__replaceUnresolvedDefinition(td, old_td._setBuiltinFromInstance(td))
        else:
            tns.addCategoryObject('typeDefinition', td.name(), td)
        assert td is not None
        return td

    def __addAttributeDeclaration (self, ad):
        local_name = ad.name()
        assert self.__targetNamespace
        tns = self.targetNamespace()
        old_ad = tns.attributeDeclarations().get(local_name)
        if (old_ad is not None) and (old_ad != ad):
            # @todo: validation error if old_ad is not a built-in
            if isinstance(ad, AttributeDeclaration) != isinstance(old_ad, AttributeDeclaration):
                raise pyxb.SchemaValidationError('Name %s used for both simple and complex types' % (ad.name(),))
            # Copy schema-related information from the new definition
            # into the old one, and continue to use the old one.
            ad = self.__replaceUnresolvedDefinition(ad, old_ad._setBuiltinFromInstance(ad))
        else:
            tns.addCategoryObject('attributeDeclaration', ad.name(), ad)
        assert ad is not None
        return ad

def _AddSimpleTypes (namespace):
    """Add to the schema the definitions of the built-in types of XMLSchema.
    This should only be invoked by L{pyxb.namespace} when the built-in
    namespaces are initialized. """
    # Add the ur type
    #schema = namespace.schema()
    schema = Schema(namespace_context=pyxb.namespace.XMLSchema.initialNamespaceContext())
    td = schema._addNamedComponent(ComplexTypeDefinition.UrTypeDefinition(in_builtin_definition=True))
    assert td.isResolved()
    # Add the simple ur type
    td = schema._addNamedComponent(SimpleTypeDefinition.SimpleUrTypeDefinition(in_builtin_definition=True))
    assert td.isResolved()
    # Add definitions for all primitive and derived simple types
    pts_std_map = {}
    for dtc in datatypes._PrimitiveDatatypes:
        name = dtc.__name__.rstrip('_')
        td = schema._addNamedComponent(SimpleTypeDefinition.CreatePrimitiveInstance(name, schema, dtc))
        assert td.isResolved()
        assert dtc.SimpleTypeDefinition() == td
        pts_std_map.setdefault(dtc, td)
    for dtc in datatypes._DerivedDatatypes:
        name = dtc.__name__.rstrip('_')
        parent_std = pts_std_map[dtc.XsdSuperType()]
        td = schema._addNamedComponent(SimpleTypeDefinition.CreateDerivedInstance(name, schema, parent_std, dtc))
        assert td.isResolved()
        assert dtc.SimpleTypeDefinition() == td
        pts_std_map.setdefault(dtc, td)
    for dtc in datatypes._ListDatatypes:
        list_name = dtc.__name__.rstrip('_')
        element_name = dtc._ItemType.__name__.rstrip('_')
        element_std = schema.targetNamespace().typeDefinitions().get(element_name)
        assert element_std is not None
        td = schema._addNamedComponent(SimpleTypeDefinition.CreateListInstance(list_name, schema, element_std, dtc))
        assert td.isResolved()
    return schema

import sys
pyxb.namespace._InitializeBuiltinNamespaces(sys.modules[__name__])

## Local Variables:
## fill-column:78
## End:
