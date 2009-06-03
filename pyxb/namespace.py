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

"""Classes and global objects related to U{XML Namespaces<http://www.w3.org/TR/2006/REC-xml-names-20060816/index.html>}.

Since namespaces hold all referenceable objects, this module also defines the
infrastructure for resolving schema component references.

@group Resolution: _Resolvable_mixin, _NamespaceResolution_mixin
@group Component Management: _ComponentDependency_mixin, _NamespaceComponentAssociation_mixin
@group Schema Specializations: _XML, _XHTML, _XMLSchema, _XMLSchema_instance
@group Named Object Management: _NamespaceCategory_mixin, NamedObjectMap
"""

import pyxb
import os
import fnmatch

PathEnvironmentVariable = 'PYXB_NAMESPACE_PATH'
"""Environment variable from which default path to pre-loaded namespaces is
read.  The value should be a colon-separated list of absolute paths.  A path
of C{+} will be replaced by the system default path (normally
C{pyxb/standard/bindings/raw})."""

import os.path
DefaultBindingPath = "%s/standard/bindings/raw" % (os.path.dirname(__file__),)
"""Default location for reading C{.wxs} files"""

# Stuff required for pickling
import cPickle as pickle

class ExpandedName (pyxb.cscRoot):
    """Represent an extended name
    U{http://www.w3.org/TR/REC-xml-names/#dt-expname}, which pairs a namespace
    with a local name.

    Because a large number of local elements, and most attributes, have no
    namespace associated with them, this is optimized for representing names
    with an absent namespace.  The hash and equality test methods are set so
    that a plain string is equivalent to a tuple of None and that string.

    Note that absent namespaces can be represented in two ways: with a
    namespace of None, and with a namespace that is an absent namespace.  Hash
    code calculations are done so that the two alternatives produce the same
    hash; however, comparison is done so that the two are distinguished.  The
    latter is the intended behavior; the former should not be counted upon.

    This class allows direct lookup of the named object within a category by
    using the category name as an accessor function.  That is, if the
    namespace of the expanded name C{en} has a category 'typeDefinition', then
    the following two expressions are equivalent::
    
      en.typeDefinition()
      en.namespace().categoryMap('typeDefinition').get(en.localName())

    This class descends from C{tuple} so that its values can be used as
    dictionary keys without concern for pointer equivalence.
    """
    def namespace (self):
        """The L{Namespace} part of the expanded name."""
        return self.__namespace
    __namespace = None

    def namespaceURI (self):
        """Return the URI of the namespace, or C{None} if the namespace is absent."""
        return self.__namespaceURI
    __namespaceURI = None

    def localName (self):
        """The local part of the expanded name."""
        return self.__localName
    __localName = None

    # Cached tuple representation
    __expandedName = None

    def validateComponentModel (self):
        """Pass model validation through to namespace part."""
        return self.namespace().validateComponentModel()

    def uriTuple (self):
        """Return a tuple consisting of the namespace URI and the local name.

        This presents the expanded name as base Python types for persistent
        storage.  Be aware, though, that it will lose the association of the
        name with an absent namespace, if that matters to you."""
        return ( self.__namespaceURI, self.__localName )

    # Treat unrecognized attributes as potential accessor functions
    def __getattr__ (self, name):
        # Don't try to recognize private names (like __setstate__)
        if name.startswith('__'):
            return super(ExpandedName, self).__getattr__(name)
        if self.namespace() is None:
            return lambda: None
        return lambda _value=self.namespace().categoryMap(name).get(self.localName()): _value

    def createName (self, local_name):
        """Return a new expanded name that pairs the namespace of this name
        with the given local name."""
        return ExpandedName(self.namespace(), local_name)

    def __init__ (self, *args, **kw):
        """Create an expanded name.

        Expected argument patterns are:

        ( C{str} ) -- the local name in an absent namespace
        ( L{ExpandedName} ) -- a copy of the given expanded name
        ( C{xml.dom.Node} ) -- The name extracted from node.namespaceURI and node.localName
        ( C{str}, C{str} ) -- the namespace URI and the local name
        ( L{Namespace}, C{str} ) -- the namespace and the local name
        ( L{ExpandedName}, C{str}) -- the namespace from the expanded name, and the local name

        Wherever C{str} occurs C{unicode} is also permitted.
        
        @keyword fallback_namespace: Optional Namespace instance to use if the
        namespace would otherwise be None.  This is only used if it is an
        absent namespace.

        """
        fallback_namespace = kw.get('fallback_namespace')
        if 0 == len(args):
            raise pyxb.LogicError('Too few arguments to ExpandedName constructor')
        if 2 < len(args):
            raise pyxb.LogicError('Too many arguments to ExpandedName constructor')
        if 2 == len(args):
            # Namespace(str, unicode, Namespace) and local name (str, unicode)
            ( ns, ln ) = args
        else:
            # Local name (str, unicode) or ExpandedName or Node
            assert 1 == len(args)
            ln = args[0]
            ns = None
            if isinstance(ln, (str, unicode)):
                pass
            elif isinstance(ln, ExpandedName):
                ns = ln.namespace()
                ln = ln.localName()
            else:
                try:
                    ns = ln.namespaceURI
                    ln = ln.localName
                except AttributeError:
                    pass
        if (ns is None) and (fallback_namespace is not None):
            if fallback_namespace.isAbsentNamespace():
                ns = fallback_namespace
        if isinstance(ns, (str, unicode)):
            ns = NamespaceForURI(ns, create_if_missing=True)
        if isinstance(ns, ExpandedName):
            ns = ns.namespace()
        if (ns is not None) and not isinstance(ns, Namespace):
            raise pyxb.LogicError('ExpandedName must include a valid (perhaps absent) namespace, or None.')
        self.__namespace = ns
        if self.__namespace is not None:
            self.__namespaceURI = self.__namespace.uri()
        self.__localName = ln
        self.__expandedName = ( self.__namespace, self.__localName )
        self.__uriTuple = ( self.__namespaceURI, self.__localName )


    def __str__ (self):
        if self.__namespaceURI is not None:
            return '{%s}%s' % (self.__namespaceURI, self.__localName)
        return self.localName()

    def __hash__ (self):
        if self.__namespaceURI is None:
            # Handle both str and unicode hashes
            return type(self.__localName).__hash__(self.__localName)
        return tuple.__hash__(self.__expandedName)

    def __cmp__ (self, other):
        if isinstance(other, (str, unicode)):
            other = ( None, other )
        if not isinstance(other, tuple):
            other = other.__uriTuple
        if isinstance(other[0], Namespace):
            other = ( other[0].uri(), other[1] )
        return cmp(self.__uriTuple, other)

    def getAttribute (self, dom_node):
        """Return the value of the attribute identified by this name in the given node."""
        if dom_node.hasAttributeNS(self.__namespaceURI, self.__localName):
            return dom_node.getAttributeNS(self.__namespaceURI, self.__localName)
        return None

    def nodeMatches (self, dom_node):
        """Return True iff the dom node expanded name matches this expanded name."""
        return (dom_node.localName == self.__localName) and (dom_node.namespaceURI == self.__namespaceURI)

class _Resolvable_mixin (pyxb.cscRoot):
    """Mix-in indicating that this object may have references to unseen named components.

    This class is mixed-in to those XMLSchema components that have a reference
    to another component that is identified by a QName.  Resolution of that
    component may need to be delayed if the definition of the component has
    not yet been read.
    """
    def isResolved (self):
        """Determine whether this named component is resolved.

        Override this in the child class."""
        raise pyxb.LogicError('Resolved check not implemented in %s' % (self.__class__,))
    
    def _resolve (self):
        """Perform whatever steps are required to resolve this component.

        Resolution is performed in the context of the namespace to which the
        component belongs.  Invoking this method may fail to complete the
        resolution process if the component itself depends on unresolved
        components.  The sole caller of this should be
        L{Namespace.resolveDefinitions}.
        
        This method is permitted (nay, encouraged) to raise an exception if
        resolution requires interpreting a QName and the named component
        cannot be found.

        Override this in the child class.  In the prefix, if L{isResolved} is
        true, return right away.  If something prevents you from completing
        resolution, invoke L{self._queueForResolution()} (so it is retried
        later) and immediately return self.  Prior to leaving after successful
        resolution discard any cached dom node by setting C{self.__domNode=None}.

        @return: C{self}, whether or not resolution succeeds.
        @raise pyxb.SchemaValidationError: if resolution requlres a reference to an unknown component
        """
        raise pyxb.LogicError('Resolution not implemented in %s' % (self.__class__,))

    def _queueForResolution (self):
        """Short-hand to requeue an object if the class implements _namespaceContext().
        """
        self._namespaceContext().queueForResolution(self)

    __ResolvingSchema = None
    @classmethod
    def _SetResolvingSchema (cls, schema):
        """Record the schema that is currently being resolved."""
        cls.__ResolvingSchema = schema

    @classmethod
    def _ResolvingSchema (cls):
        """Return the schema currently being resolved.

        We need this so that we can reference the schema
        C{attributeFormDefault} and C{elementFormDefault} attributes when
        determining the target namespace for local declarations.  Normally,
        components are not associated with schemas, only with namespaces, so
        the component model doesn't provide what's needed to get this
        information."""
        return cls.__ResolvingSchema

    def _resolvingSchema (self):
        """Pass to class-level L{_ResolvingSchema}"""
        return self._ResolvingSchema()

class NamedObjectMap (dict):
    """An extended dictionary intended to assist with QName resolution.

    These dictionaries have an attribute that identifies a category of named
    objects within a Namespace; the specifications for various documents
    require that certain groups of objects must be unique, while uniqueness is
    not required between groups.  The dictionary also retains a pointer to the
    Namespace instance for which it holds objects."""
    def namespace (self):
        """The namespace to which the object map belongs."""
        return self.__namespace
    __namespace = None
    
    def category (self):
        """The category of objects (e.g., typeDefinition, elementDeclaration)."""
        return self.__category
    __category = None

    def __init__ (self, category, namespace, *args, **kw):
        self.__category = category
        self.__namespace = namespace
        super(NamedObjectMap, self).__init__(self, *args, **kw)

class _NamespaceCategory_mixin (pyxb.cscRoot):
    """Mix-in that aggregates those aspects of XMLNamespaces that hold
    references to categories of named objects.

    Arbitrary groups of named objects, each requiring unique names within
    themselves, can be saved.  Unless configured otherwise, the Namespace
    instance is extended with accessors that provide direct access to
    individual category maps.  The name of the method is the category name
    with a suffix of "s"; e.g., if a category "typeDefinition" exists, it can
    be accessed from the namespace using the syntax C{ns.typeDefinitions()}.

    Note that the returned value from the accessor is a live reference to
    the category map; changes made to the map are reflected in the
    namespace.
    """
    
    # Map from category strings to NamedObjectMap instances that
    # contain the dictionary for that category.
    __categoryMap = None

    def _reset (self):
        """CSC extension to reset fields of a Namespace.

        This one handles category-related data."""
        getattr(super(_NamespaceCategory_mixin, self), '_reset', lambda *args, **kw: None)()
        self.__categoryMap = { }

    def categories (self):
        """The list of individual categories held in this namespace."""
        return self.__categoryMap.keys()

    def categoryMap (self, category):
        """Map from category names to NamedObjectMap instances."""
        return self.__categoryMap[category]

    def __defineCategoryAccessors (self):
        """Define public methods on the Namespace which provide access to
        individual NamedObjectMaps based on their category.

        """
        for category in self.categories():
            accessor_name = category + 's'
            setattr(self, accessor_name, lambda _map=self.categoryMap(category): _map)

    def configureCategories (self, categories):
        """Ensure there is a map for each of the given categories.

        Existing maps are not affected."""
        if self.__categoryMap is None:
            self.__categoryMap = { }
        for category in categories:
            if not (category in self.__categoryMap):
                self.__categoryMap[category] = NamedObjectMap(category, self)
        self.__defineCategoryAccessors()
        return self

    def addCategoryObject (self, category, local_name, named_object):
        """Allow access to the named_object by looking up the local_name in
        the given category.

        Raises pyxb.NamespaceUniquenessError if an object with the same name
        already exists in the category."""
        name_map = self.categoryMap(category)
        old_object = name_map.get(local_name)
        if (old_object is not None) and (old_object != named_object):
            raise pyxb.NamespaceUniquenessError('Name %s used for multiple values in %s' % (local_name, category))
        name_map[local_name] = named_object
        return named_object

    def replaceCategoryObject (self, category, local_name, old_object, new_object):
        """Replace the referenced object in the category.

        The new object will be added only if the old_object matches the
        current entry for local_name in the category."""
        name_map = self.categoryMap(category)
        if old_object == name_map.get(local_name):
            name_map[local_name] = new_object
        return name_map[local_name]

    # Verify that the namespace category map has no components recorded.  This
    # is the state that should hold prior to loading a saved namespace; at
    # tthe moment, we do not support aggregating components defined separately
    # into the same namespace.  That should be done at the schema level using
    # the "include" element.
    def __checkCategoriesEmpty (self):
        if self.__categoryMap is None:
            return True
        assert isinstance(self.__categoryMap, dict)
        if 0 == len(self.__categoryMap):
            return True
        for k in self.categories():
            if 0 < len(self.categoryMap(k)):
                return False
        return True

    def _saveToFile_csc (self, pickler):
        """CSC function to save Namespace state to a file.

        This one saves the category map, including all objects held in the categories."""
        pickler.dump(self.__categoryMap)
        return getattr(super(_NamespaceCategory_mixin, self), '_saveToFile_csc', lambda _pickler: _pickler)(pickler)

    @classmethod
    def _LoadFromFile_csc (cls, instance, unpickler):
        """CSC function to load Namespace state from a file.
        
        This one reads the saved category map, then incorporates its
        information into the existing maps. and their contents with data from
        the saved namespace.

        @todo: For now, we do not allow aggregation of named object maps from
        different sources (e.g., schema and one or more saved files).  However,
        it may be useful to do so in the future, especially if the categories
        are disjoint.
        """
        assert instance.__checkCategoriesEmpty
        new_category_map = unpickler.load()
        instance.configureCategories(new_category_map.keys())
        for category in new_category_map.keys():
            instance.categoryMap(category).update(new_category_map[category])
        instance.__defineCategoryAccessors()
        return getattr(super(_NamespaceCategory_mixin, cls), '_LoadFromFile_csc', lambda *args, **kw: None)(unpickler)

class _NamespaceResolution_mixin (pyxb.cscRoot):
    """Mix-in that aggregates those aspects of XMLNamespaces relevant to
    resolving component references.
    """

    # A set of Namespace._Resolvable_mixin instances that have yet to be
    # resolved.
    __unresolvedComponents = None

    def _reset (self):
        """CSC extension to reset fields of a Namespace.

        This one handles component-resolution--related data."""
        getattr(super(_NamespaceResolution_mixin, self), '_reset', lambda *args, **kw: None)()
        self.__unresolvedComponents = []

    def queueForResolution (self, resolvable):
        """Invoked to note that a component may have references that will need
        to be resolved.

        Newly created named components are often unresolved, as are components
        which, in the course of resolution, are found to depend on another
        unresolved component.

        The provided object must be an instance of _Resolvable_mixin.  This
        method returns the resolvable object.
        """
        assert isinstance(resolvable, _Resolvable_mixin)
        if not resolvable.isResolved():
            self.__unresolvedComponents.append(resolvable)
        return resolvable

    def resolveDefinitions (self, schema):
        """Loop until all references within the associated resolvable objects
        have been resolved.

        This method iterates through all components on the unresolved list,
        invoking the _resolve method of each.  If the component could not be
        resolved in this pass, it iis placed back on the list for the next
        iteration.  If an iteration completes without resolving any of the
        unresolved components, a pyxb.NotInNamespaceError exception is raised.

        @note: Do not invoke this until all top-level definitions for the
        namespace have been provided.  The resolution routines are entitled to
        raise a validation exception if a reference to an unrecognized
        component is encountered.

        @param schema: The schema for which resolution is being performed.
        @type schema: L{pyxb.xmlschema.structures.Schema}
        """
        assert _Resolvable_mixin._ResolvingSchema() is None
        assert schema is not None
        _Resolvable_mixin._SetResolvingSchema(schema)
        num_loops = 0
        while 0 < len(self.__unresolvedComponents):
            # Save the list of unresolved objects, reset the list to capture
            # any new objects defined during resolution, and attempt the
            # resolution for everything that isn't resolved.
            unresolved = self.__unresolvedComponents
            #print 'Looping for %d unresolved definitions: %s' % (len(unresolved), ' '.join([ str(_r) for _r in unresolved]))
            num_loops += 1
            #assert num_loops < 18
            
            self.__unresolvedComponents = []
            for resolvable in unresolved:
                # Attempt the resolution.
                resolvable._resolve()

                # Either we resolved it, or we queued it to try again later
                assert resolvable.isResolved() or (resolvable in self.__unresolvedComponents)

                # We only clone things that have scope None.  We never
                # resolve things that have scope None.  Therefore, we
                # should never have resolved something that has
                # clones.
                if (resolvable.isResolved() and (resolvable._clones() is not None)):
                    assert False
            if self.__unresolvedComponents == unresolved:
                # This only happens if we didn't code things right, or the
                # schema actually has a circular dependency in some named
                # component.
                failed_components = []
                import pyxb.xmlschema.structures
                for d in self.__unresolvedComponents:
                    if isinstance(d, pyxb.xmlschema.structures._NamedComponent_mixin):
                        failed_components.append('%s named %s' % (d.__class__.__name__, d.name()))
                    else:
                        if isinstance(d, pyxb.xmlschema.structures.AttributeUse):
                            print d.attributeDeclaration()
                        failed_components.append('Anonymous %s' % (d.__class__.__name__,))
                raise pyxb.NotInNamespaceError('Infinite loop in resolution:\n  %s' % ("\n  ".join(failed_components),))

        # Replace the list of unresolved components with None, so that
        # attempts to subsequently add another component fail.
        self.__unresolvedComponents = None
        _Resolvable_mixin._SetResolvingSchema(None)
        return self
    
    def _unresolvedComponents (self):
        """Returns a reference to the list of unresolved components."""
        return self.__unresolvedComponents

class _ComponentDependency_mixin (pyxb.cscRoot):
    """Mix-in for components that can depend on other components."""
    # Cached frozenset of components on which this component depends.
    __dependentComponents = None

    def _resetClone_csc (self):
        """CSC extension to reset fields of a component.  This one clears
        dependency-related data, since the clone will have to revise its
        dependencies.
        @rtype: C{None}"""
        getattr(super(_ComponentDependency_mixin, self), '_resetClone_csc', lambda *args, **kw: None)()
        self.__dependentComponents = None

    def dependentComponents (self):
        """Return a set of components upon which this component depends.  This
        is essentially those components to which a reference was resolved,
        plus those that are sub-component (e.g., the particles in a model
        group).

        @rtype: C{set(L{pyxb.xmlschema.structures._SchemaComponent_mixin})}"""
        if self.__dependentComponents is None:
            if isinstance(self, _Resolvable_mixin) and not (self.isResolved()):
                raise pyxb.LogicError('Unresolved %s in %s: %s' % (self.__class__.__name__, self.namespaceContext().targetNamespace(), self.name()))
            self.__dependentComponents = self._dependentComponents_vx()
            if self in self.__dependentComponents:
                raise pyxb.LogicError('Self-dependency with %s %s' % (self.__class__.__name__, self))
        return self.__dependentComponents

    def _dependentComponents_vx (self):
        """Placeholder for subclass method that identifies the necessary components.

        @note: Override in subclasses.

        @return: The component instances on which this component depends
        @rtype: C{frozenset}
        @raise LogicError: A subclass failed to implement this method
        """
        raise LogicError('%s does not implement _dependentComponents_vx' % (self.__class__,))

class _NamespaceComponentAssociation_mixin (pyxb.cscRoot):
    """Mix-in for managing components defined within this namespace.

    The component set includes not only top-level named components (such as
    those accessible through category maps), but internal anonymous
    components, such as those involved in representing the content model of a
    complex type definition..  We need to be able to get a list of these
    components, sorted in dependency order, so that generated bindings do not
    attempt to refer to a binding that has not yet been generated."""

    # A set containing all components, named or unnamed, that belong to this
    # namespace.
    __components = None

    def _reset (self):
        """CSC extension to reset fields of a Namespace.

        This one handles data related to component association with a
        namespace."""
        getattr(super(_NamespaceComponentAssociation_mixin, self), '_reset', lambda *args, **kw: None)()
        self.__components = set()

    def _associateComponent (self, component):
        """Record that the responsibility for the component belongs to this namespace."""
        assert self.__components is not None
        assert isinstance(component, _ComponentDependency_mixin)
        assert component not in self.__components
        self.__components.add(component)

    def _replaceComponent (self, existing_def, replacement_def):
        """Replace the existing definition with another.

        This is used in a situation where building the component model
        resulted in a new component instance being created and registered, but
        for which an existing component is to be preferred.  An example is
        when parsing the schema for XMLSchema itself: the built-in datatype
        components should be retained instead of the simple type definition
        components dynamically created from the schema.

        By providing the value C{None} as the replacement definition, this can
        also be used to remove components.
        """
        self.__components.remove(existing_def)
        if replacement_def is not None:
            self.__components.add(replacement_def)
        return replacement_def

    def components (self):
        """Return a frozenset of all components, named or unnamed, belonging
        to this namespace."""
        return frozenset(self.__components)

    def orderedComponents (self, component_order):
        """Return a list of all associated components, ordered by dependency.

        component_order is a list specifying the categories of components in
        their preferred order.  For example, in the component model complex
        types should be generated before elements, so that the element
        declaration can include a reference to the complex type that holds its
        state.  For cases where a reverse dependency exists (e.g., a complex
        type that holds an element), the code generator must provide a second
        stage that inserts those dependencies.
        """
        components = self.__components

        # Segregate the components by type, ensuring each is listed only once.
        component_by_class = {}
        for c in components:
            component_by_class.setdefault(c.__class__, []).append(c)
        ordered_components = []

        # For each component type, add the matching components in order of
        # dependency.  Some of the provided components may be dropped from the
        # list (@todo is this true?)
        for cc in component_order:
            if cc not in component_by_class:
                continue
            component_list = component_by_class[cc]
            component_list = self.__sortByDependency(component_list, dependent_class_filter=cc)
            ordered_components.extend(component_list)
        return ordered_components
    
    def __sortByDependency (self, components, dependent_class_filter):
        """Return a list of components sorted by dependency.

        Specifically, if the resultting list is processed in order components
        will not be referenced in any component that precedes them in the
        returned sequence.

        dependent_class_filter is an optional class that specifies that
        dependencies on components not of that class should be ignored."""
        emit_order = []
        while 0 < len(components):
            new_components = []
            ready_components = []
            for td in components:
                # There should be no components that do not belong to this
                # namespace.  Components that belong to no namespace are
                # presumably local to a type in this namespace.
                try:
                    assert (td.targetNamespace() == self) or (td.targetNamespace() is None)
                except AttributeError:
                    # Unnamed things don't get discarded this way
                    pass
                # Scoped declarations that don't have a scope are tossed out
                # too: those exist only in model and attribute groups that
                # have not been cloned into a specific scope, so are never
                # referenced in the bindings.
                try:
                    if td.scope() is None:
                        print 'Discarding %s: no scope defined' % (td.name(),)
                        continue
                    # @todo: Eliminate indeterminate objects.  Can't do this
                    # until we clean up the generation content model, because
                    # it references these things.
                    #if td._scopeIsIndeterminate():
                    #    print 'Discarding %s: indeterminate scope' % (td.name(),)
                    #    continue
                except AttributeError, e:
                    # Some components don't have a scope.
                    pass

                dep_types = td.dependentComponents()
                #print 'Type %s depends on %s' % (td, dep_types)
                ready = True
                for dtd in dep_types:
                    # If the component depends on something that is not a type
                    # we care about, just move along; those are handled in
                    # another group.
                    if (dependent_class_filter is not None) and not isinstance(dtd, dependent_class_filter):
                        continue

                    # Ignore dependencies that go outside the namespace
                    try:
                        if dtd.targetNamespace() != self:
                            continue
                    except AttributeError:
                        # Ignore dependencies on unnamable things
                        continue

                    # Better not be a dependency loop
                    assert dtd != td

                    # Ignore dependencies on the ur types
                    if dtd.isUrTypeDefinition():
                        continue

                    # Do not include components that are ready but
                    # have not been placed on emit_order yet.  Doing
                    # so might result in order violations after
                    # they've been sorted by name.
                    if not (dtd in emit_order):
                        #print '%s depends on %s, not emitting' % (td.name(), dtd.name())
                        ready = False
                        break
                if ready:
                    ready_components.append(td)
                else:
                    new_components.append(td)
            # Sort the components within the ready subsequence by name, to
            # make it easier to locate specific ones in the generated
            # bindings.
            ready_components.sort(lambda _x, _y: cmp(_x.bestNCName(), _y.bestNCName()))
            emit_order.extend(ready_components)
            if components == new_components:
                raise pyxb.LogicError('Infinite loop in order calculation:\n  %s' % ("\n  ".join( ['%s: %s' % (_c.name(),  ' '.join([ _dtd.name() for _dtd in _c.dependentComponents()])) for _c in components] ),))
            components = new_components
        return emit_order

class Namespace (_NamespaceCategory_mixin, _NamespaceResolution_mixin, _NamespaceComponentAssociation_mixin):
    """Represents an XML namespace (a URI).

    There is at most one L{Namespace} class instance per namespace (URI).  The
    instance also supports associating arbitrary L{maps<NamedObjectMap>} from
    names to objects, in separate categories.  The default categories are
    configured externally; for example, the
    L{Schema<pyxb.xmlschema.structures.Schema>} component defines a category
    for each named component in XMLSchema, and the customizing subclass for
    WSDL definitions adds categories for the service bindings, messages, etc.

    Namespaces can be written to and loaded from pickled files.  See
    L{LoadFromFile} for information.
    """

    # The URI for the namespace.  If the URI is None, this is an absent
    # namespace.
    __uri = None

    # An identifier, unique within a program using PyXB, used to distinguish
    # absent namespaces.  Currently this value is not accessible to the user,
    # and exists solely to provide a unique identifier when printing the
    # namespace as a string.  The class variable is used as a one-up counter,
    # which is assigned to the instance variable when an absent namespace
    # instance is created.
    __absentNamespaceID = 0

    # A prefix bound to this namespace by standard.  Current set known are applies to
    # xml and xmlns.
    __boundPrefix = None

    # A map from URIs to Namespace instances.  Namespaces instances
    # must be unique for their URI.  See __new__().
    __Registry = { }

    # Optional URI specifying the source for the schema for this namespace
    __schemaLocation = None

    # Optional description of the namespace
    __description = None

    # Indicates whether this namespace is built-in to the system
    __isBuiltinNamespace = False

    # Indicates whether this namespace is undeclared (available always)
    __isUndeclaredNamespace = False

    # A string denoting the path by which this namespace is imported into
    # generated Python modules
    __modulePath = None

    # A set of options defining how the Python bindings for this namespace
    # were generated.  Not currently used, since we don't have different
    # binding configurations yet.
    __bindingConfiguration = None
 
    # The namespace to use as the default namespace when constructing the
    # The namespace context used when creating built-in components that belong
    # to this namespace.  This is used to satisfy the low-level requirement
    # that all schema component have a namespace context; normally, that
    # context is built dynamically from the schema element.
    __initialNamespaceContext = None

    # The default_namespace parameter when creating the initial namespace
    # context.  Only used with built-in namespaces.
    __contextDefaultNamespace = None

    # The map from prefixes to namespaces as defined by the schema element for
    # this namespace.  Only used with built-in namespaces.
    __contextInScopeNamespaces = None

    @classmethod
    def _NamespaceForURI (cls, uri):
        """If a Namespace instance for the given URI exists, return it; otherwise return None.

        Note; Absent namespaces are not stored in the registry.  If you
        use one (e.g., for a schema with no target namespace), don't
        lose hold of it."""
        assert uri is not None
        return cls.__Registry.get(uri, None)


    def __getnewargs__ (self):
        """Pickling support.

        To ensure that unpickled Namespace instances are unique per
        URI, we ensure that the routine that creates unpickled
        instances knows what it's supposed to return."""
        return (self.uri(),)

    def __new__ (cls, *args, **kw):
        """Pickling and singleton support.

        This ensures that no more than one Namespace instance exists
        for any given URI.  We could do this up in __init__, but that
        doesn't normally get called when unpickling instances; this
        does.  See also __getnewargs__()."""
        (uri,) = args
        if not (uri in cls.__Registry):
            instance = object.__new__(cls)
            # Do this one step of __init__ so we can do checks during unpickling
            instance.__uri = uri
            instance._reset()
            # Absent namespaces are not stored in the registry.
            if uri is None:
                return instance
            cls.__Registry[uri] = instance
        return cls.__Registry[uri]

    def __init__ (self, uri,
                  schema_location=None,
                  description=None,
                  is_builtin_namespace=False,
                  is_undeclared_namespace=False,
                  bound_prefix=None,
                  default_namespace=None,
                  in_scope_namespaces=None):
        """Create a new Namespace.

        The URI must be non-None, and must not already be assigned to
        a Namespace instance.  See NamespaceForURI().
        
        User-created Namespace instances may also provide a
        schemaLocation and a description.

        Users should never provide a is_builtin_namespace parameter.
        """
        # New-style superclass invocation
        super(Namespace, self).__init__()

        self.__contextDefaultNamespace = default_namespace
        self.__contextInScopeNamespaces = in_scope_namespaces

        # Make sure that we're not trying to do something restricted to
        # built-in namespaces
        if not is_builtin_namespace:
            if bound_prefix is not None:
                raise pyxb.LogicError('Only permanent Namespaces may have bound prefixes')

        # We actually set the uri when this instance was allocated;
        # see __new__().
        assert self.__uri == uri
        self.__boundPrefix = bound_prefix
        self.__schemaLocation = schema_location
        self.__description = description
        self.__isBuiltinNamespace = is_builtin_namespace
        self.__isUndeclaredNamespace = is_undeclared_namespace

        self._reset()

        assert (self.__uri is None) or (self.__Registry[self.__uri] == self)

    def _reset (self):
        getattr(super(Namespace, self), '_reset', lambda *args, **kw: None)()
        self.__initialNamespaceContext = None

    def uri (self):
        """Return the URI for the namespace represented by this instance.

        If the URI is None, this is an absent namespace, used to hold
        declarations not associated with a namespace (e.g., from schema with
        no target namespace)."""
        return self.__uri

    def isAbsentNamespace (self):
        """Return True iff this namespace is an absent namespace.

        Absent namespaces have no namespace URI; they exist only to
        hold components created from schemas with no target
        namespace."""
        return self.__uri is None

    @classmethod
    def CreateAbsentNamespace (cls):
        """Create an absent namespace.

        Use this instead of the standard constructor, in case we need
        to augment it with a uuid or the like."""
        rv = Namespace(None)
        rv.__absentNamespaceID = cls.__absentNamespaceID
        cls.__absentNamespaceID += 1
        return rv

    def _overrideAbsentNamespace (self, uri):
        assert self.isAbsentNamespace()
        self.__uri = uri

    def boundPrefix (self):
        """Return the standard prefix to be used for this namespace.

        Only a few namespace prefixes are bound to namespaces: xml and xmlns
        are two.  In all other cases, this method should return None.  The
        infrastructure attempts to prevent user creation of Namespace
        instances that have bound prefixes."""
        return self.__boundPrefix

    def isBuiltinNamespace (self):
        """Return True iff this namespace was defined by the infrastructure.

        That is the case for all namespaces in the Namespace module."""
        return self.__isBuiltinNamespace

    def isUndeclaredNamespace (self):
        """Return True iff this namespace is always available
        regardless of whether there is a declaration for it.

        This is the case only for the
        xml(http://www.w3.org/XML/1998/namespace) and
        xmlns(http://www.w3.org/2000/xmlns/) namespaces."""
        return self.__isUndeclaredNamespace

    def modulePath (self):
        return self.__modulePath

    def setModulePath (self, module_path):
        self.__modulePath = module_path
        return self.modulePath()

    def module (self):
        """Return a reference to the Python module that implements
        bindings for this namespace."""
        return self.__module
    def _setModule (self, module):
        """Set the module to use for Python bindings for this namespace.

        Should only be called by generated code."""
        self.__module = module
        return self
    __module = None

    def schemaLocation (self, schema_location=None):
        """Get, or set, a URI that says where the XML document defining the namespace can be found."""
        if schema_location is not None:
            self.__schemaLocation = schema_location
        return self.__schemaLocation

    def description (self, description=None):
        """Get, or set, a textual description of the namespace."""
        if description is not None:
            self.__description = description
        return self.__description

    def nodeIsNamed (self, node, *local_names):
        return (node.namespaceURI == self.uri()) and (node.localName in local_names)

    def createExpandedName (self, local_name):
        return ExpandedName(self, local_name)

    __PICKLE_FORMAT = '200905041925'

    def __getstate__ (self):
        """Support pickling.

        Because namespace instances must be unique, we represent them
        as their URI and any associated (non-bound) information.  This
        way allows the unpickler to either identify an existing
        Namespace instance for the URI, or create a new one, depending
        on whether the namespace has already been encountered."""
        if self.uri() is None:
            raise pyxb.LogicError('Illegal to serialize absent namespaces')
        kw = {
            '__schemaLocation': self.__schemaLocation,
            '__description':self.__description,
            # * Do not include __boundPrefix: bound namespaces should
            # have already been created by the infrastructure, so the
            # unpickler should never create one.
            '__modulePath' : self.__modulePath,
            '__bindingConfiguration': self.__bindingConfiguration,
            '__contextDefaultNamespace' : self.__contextDefaultNamespace,
            '__contextInScopeNamespaces' : self.__contextInScopeNamespaces,
            }
        args = ( self.__uri, )
        return ( self.__PICKLE_FORMAT, args, kw )

    def __setstate__ (self, state):
        """Support pickling.

        We used to do this to ensure uniqueness; now we just do it to
        eliminate pickling the schema.

        This will throw an exception if the state is not in a format
        recognized by this method."""
        ( format, args, kw ) = state
        if self.__PICKLE_FORMAT != format:
            raise pyxb.pickle.UnpicklingError('Got Namespace pickle format %s, require %s' % (format, self.__PICKLE_FORMAT))
        ( uri, ) = args
        assert self.__uri == uri
        # Convert private keys into proper form
        for (k, v) in kw.items():
            if k.startswith('__'):
                del kw[k]
                kw['_%s%s' % (self.__class__.__name__, k)] = v
        self.__dict__.update(kw)

    # Class variable recording the namespace that is currently being
    # pickled.  Used to prevent storing components that belong to
    # other namespaces.  Should be None unless within an invocation of
    # saveToFile.
    __PicklingNamespace = None
    @classmethod
    def _PicklingNamespace (cls, value):
        # NB: Use Namespace explicitly so do not set the variable in a
        # subclass.
        Namespace.__PicklingNamespace = value

    @classmethod
    def PicklingNamespace (cls):
        return Namespace.__PicklingNamespace

    def _saveToFile_csc (self, pickler):
        """CSC function to save Namespace state to a file.

        This one handles the base operations.  Implementers should tail-call
        the next implementation in the chain, returning the pickler at the end
        of the chain.

        If this method is implemented, the corresponding _LoadFromFile_csc
        function should also be implemented
        """

        # Next few are read when scanning for pre-built schemas
        pickler.dump(self.uri())
        pickler.dump(self)

        # Rest is only read if the schema needs to be loaded
        return getattr(super(Namespace, self), '_saveToFile_csc', lambda _pickler: _pickler)(pickler)

    def saveToFile (self, file_path):
        """Save this namespace, with its defining schema, to the given
        file so it can be loaded later.

        This method requires that a schema be associated with the
        namespace."""
        
        if self.uri() is None:
            raise pyxb.LogicError('Illegal to serialize absent namespaces')
        output = open(file_path, 'wb')
        pickler = pickle.Pickler(output, -1)
        self._PicklingNamespace(self)
        assert Namespace.PicklingNamespace() is not None

        self._saveToFile_csc(pickler)

        self._PicklingNamespace(None)

    @classmethod
    def _LoadFromFile_csc (cls, instance, unpickler):
        """CSC function to load Namespace state from a file.

        This one handles the base operation, including identifying the
        appropriate Namespace instance.  Implementers of this method should
        tail-call the next implementation in the chain, returning the instance
        if this is the last one.
        
        If this function is implemented, the corresponding _saveToFile_csc method
        should also be implemented
        """

        # Get the URI out of the way
        uri = unpickler.load()
        assert uri is not None

        # Unpack a Namespace instance.  This is *not* everything; it's a small
        # subset; see __getstate__.  Note that if the namespace was already
        # defined, the redefinition of __new__ above will ensure a reference
        # to the existing Namespace instance is returned and updated with the
        # new information.
        instance = unpickler.load()
        assert instance.uri() == uri
        assert cls._NamespaceForURI(instance.uri()) == instance

        # Handle any loading or postprocessing required by the mix-ins.
        return getattr(super(Namespace, cls), '_LoadFromFile_csc', lambda _instance, _unpickler: _instance)(instance, unpickler)

    @classmethod
    def LoadFromFile (cls, file_path):
        """Create a Namespace instance with schema contents loaded
        from the given file.

        Mix-ins should define a CSC function that performs any state loading
        required and returns the instance.
        """
        print 'Attempting to load a namespace from %s' % (file_path,)
        unpickler = pickle.Unpickler(open(file_path, 'rb'))
        return cls._LoadFromFile_csc(None, unpickler)

    __inSchemaLoad = False
    def _defineSchema_overload (self, structures_module):
        """Attempts to load a schema for this namespace.

        The base class implementation looks at the set of available pre-parsed
        schemas, and if one matches this namespace unserializes it and uses
        it.

        Sub-classes may choose to look elsewhere, if this version fails or
        before attempting it.

        There is no guarantee that a schema has been located when this
        returns.  Caller must check.
        """
        assert not self.__inSchemaLoad

        # Absent namespaces cannot load schemas
        if self.isAbsentNamespace():
            return None
        afn = _LoadableNamespaceMap().get(self.uri(), None)
        if afn is not None:
            #print 'Loading %s from %s' % (self.uri(), afn)
            try:
                self.__inSchemaLoad = True
                self.LoadFromFile(afn)
            finally:
                self.__inSchemaLoad = False

    __didValidation = False
    __inValidation = False
    def validateComponentModel (self, structures_module=None):
        """Ensure this namespace is ready for use.

        If the namespace does not have an associated schema, the system will
        attempt to load one.  If unsuccessful, an exception will be thrown."""
        if not self.__didValidation:
            assert not self.__inValidation
            if structures_module is None:
                import pyxb.xmlschema.structures as structures_module
            try:
                self.__inValidation = True
                self._defineSchema_overload(structures_module)
                self.__didValidation = True
            finally:
                self.__inValidation = False
        return

    def initialNamespaceContext (self):
        """Obtain the namespace context to be used when creating components in this namespace.

        Usually applies only to built-in namespaces, but is also used in the
        autotests when creating a namespace without a xs:schema element.  .
        Note that we must create the instance dynamically, since the
        information that goes into it has cross-dependencies that can't be
        resolved until this module has been completely loaded."""
        
        if self.__initialNamespaceContext is None:
            isn = { }
            if self.__contextInScopeNamespaces is not None:
                for (k, v) in self.__contextInScopeNamespaces.items():
                    isn[k] = self.__identifyNamespace(v)
            kw = { 'target_namespace' : self
                 , 'default_namespace' : self.__identifyNamespace(self.__contextDefaultNamespace)
                 , 'in_scope_namespaces' : isn }
            self.__initialNamespaceContext = NamespaceContext(None, **kw)
        return self.__initialNamespaceContext


    def __identifyNamespace (self, nsval):
        """Identify the specified namespace, which should be a built-in.

        Normally we can just use a reference to the Namespace module instance,
        but when creating those instances we sometimes need to refer to ones
        for which the instance has not yet been created.  In that case, we use
        the name of the instance, and resolve the namespace when we need to
        create the initial context."""
        if nsval is None:
            return self
        if isinstance(nsval, (str, unicode)):
            nsval = globals().get(nsval)
        if isinstance(nsval, Namespace):
            return nsval
        raise pyxb.LogicError('Cannot identify namespace from %s' % (nsval,))

    def __str__ (self):
        if self.__uri is None:
            return 'AbsentNamespace%d' % (self.__absentNamespaceID,)
        assert self.__uri is not None
        if self.__boundPrefix is not None:
            rv = '%s=%s' % (self.__boundPrefix, self.__uri)
        else:
            rv = self.__uri
        return rv

def NamespaceForURI (uri, create_if_missing=False):
    """Given a URI, provide the L{Namespace} instance corresponding to it.

    This can only be used to lookup or create real namespaces.  To create
    absent namespaces, use L{CreateAbsentNamespace}.

    @param uri: The URI that identifies the namespace
    @type uri: A non-empty C{str} or C{unicode} string
    @keyword create_if_missing: If C{True}, a namespace for the given URI is
    created if one has not already been registered.  Default is C{False}.
    @type create_if_missing: C{bool}
    @return: The Namespace corresponding to C{uri}, if available
    @rtype: L{Namespace} or C{None}
    @raise pyxb.LogicError: The uri is not a non-empty string
    """
    if not isinstance(uri, (str, unicode)):
        raise pyxb.LogicError('Cannot lookup absent namespaces')
    if 0 == len(uri):
        raise pyxb.LogicError('Namespace URIs must not be empty strings')
    rv = Namespace._NamespaceForURI(uri)
    if (rv is None) and create_if_missing:
        rv = Namespace(uri)
    return rv

def CreateAbsentNamespace ():
    """Create an absent namespace.

    Use this when you need a namespace for declarations in a schema with no
    target namespace.  Absent namespaces are not stored in the infrastructure;
    it is your responsibility to hold on to the reference you get from this,
    because you won't be able to look it up."""
    return Namespace.CreateAbsentNamespace()

__LoadableNamespaces = None
"""A mapping from namespace URIs to names of files which appear to
provide a serialized version of the namespace with schema."""

def _LoadableNamespaceMap ():
    """Get the map from URIs to files from which the namespace data
    can be loaded.  This looks for files with the extension C{.wxs} in any
    directory in the default binding path, which is read from the environment
    variable L{PathEnvironmentVariable}, or C{pyxb/standard/bindings/raw}."""
    global __LoadableNamespaces
    if __LoadableNamespaces is None:
        # Look for pre-existing pickled schema
        __LoadableNamespaces = { }
        bindings_path = os.environ.get(PathEnvironmentVariable, DefaultBindingPath)
        for bp in bindings_path.split(':'):
            if '+' == bp:
                bp = DefaultBindingPath
            for fn in os.listdir(bp):
                if fnmatch.fnmatch(fn, '*.wxs'):
                    afn = os.path.join(bp, fn)
                    infile = open(afn, 'rb')
                    unpickler = pickle.Unpickler(infile)
                    uri = unpickler.load()
                    # Loading the instance simply introduces the
                    # namespace into the registry, including the path
                    # to the Python binding module.  It does not
                    # incorporate any of the schema components.
                    instance = unpickler.load()
                    __LoadableNamespaces[uri] = afn
                    #print 'pre-parsed schema for %s available in %s' % (uri, afn)
    return __LoadableNamespaces

class _XMLSchema_instance (Namespace):
    """Extension of L{Namespace} that pre-defines components available in the
    XMLSchema Instance namespace."""

    __doneThis = False
    
    def _defineSchema_overload (self, structures_module):
        """Ensure this namespace is ready for use.

        Overrides base class implementation, since there is no schema
        for this namespace. """
        
        if not self.__doneThis:
            assert structures_module is not None
            schema = structures_module.Schema(namespace_context=self.initialNamespaceContext())
            schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('type', self))
            schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('nil', self))
            schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('schemaLocation', self))
            schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('noNamespaceSchemaLocation', self))
            self.__doneThis = True
        return self

class _XML (Namespace):
    """Extension of L{Namespace} that pre-defines components available in the
    XML (xml) namespace."""

    __doneThis = False

    def _defineSchema_overload (self, structures_module):
        """Ensure this namespace is ready for use.

        Overrides base class implementation, since there is no schema
        for this namespace. """
        
        if not self.__doneThis:
            assert structures_module is not None
            schema = structures_module.Schema(namespace_context=self.initialNamespaceContext())
            schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('base', self))
            schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('id', self))
            schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('space', self))
            schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('lang', self))
            self.__doneThis = True
        return self

class _XHTML (Namespace):
    """Extension of L{Namespace} that pre-defines comonents available in the
    XHTML namespace."""

    __doneThis = False

    def _defineSchema_overload (self, structures_module):
        """Ensure this namespace is ready for use.

        Overrides base class implementation, since there is no schema
        for this namespace.  In fact, there's nothing at all in it
        that we plan to use, so this doesn't do anything."""
        
        if not self.__doneThis:
            schema = structures_module.Schema(namespace_context=self.initialNamespaceContext())
            self.__doneThis = True
            # @todo Define a wildcard element declaration 'p' that takes anything.
        return self

class _XMLSchema (Namespace):
    """Extension of L{Namespace} that pre-defines components available in the
    XMLSchema namespace.

    The types are defined when L{pyxb.xmlschema.structures} is imported.
    """

    __doneThis = False
    def _loadBuiltins (self, structures_module):
        """Register the built-in types into the XMLSchema namespace."""

        if structures_module is None:
            import pyxb.xmlschema.structures as structures_module
        if not self.__doneThis:
            # Defer the definitions to the structures module
            assert structures_module is not None
            structures_module._AddSimpleTypes(self)
            self.__doneThis = True

        # A little validation here
        if structures_module is not None:
            assert structures_module.ComplexTypeDefinition.UrTypeDefinition() == self.typeDefinitions()['anyType']
            assert structures_module.SimpleTypeDefinition.SimpleUrTypeDefinition() == self.typeDefinitions()['anySimpleType']

    def _defineSchema_overload (self, structures_module):
        """Ensure this namespace is ready for use.

        Overrides base class implementation, since there is no
        serialized schema for this namespace."""
        
        self._loadBuiltins(structures_module)
        return self


def AvailableForLoad ():
    """Return a list of namespace URIs for which we may be able to load the
    namespace contents from a pre-parsed file.  The corresponding L{Namespace}
    can be retrieved using L{NamespaceForURI}, and the declared objects in
    that namespace loaded with L{Namespace.validateComponentModel}.

    Note that success of the load is not guaranteed if the packed file
    is not compatible with the schema class being used."""
    # Invoke this to ensure we have searched for loadable namespaces
    return _LoadableNamespaceMap().keys()

XMLSchema_instance = _XMLSchema_instance('http://www.w3.org/2001/XMLSchema-instance',
                                         description='XML Schema Instance',
                                         is_builtin_namespace=True)
"""Namespace and URI for the XMLSchema Instance namespace.  This is always
built-in, and does not (cannot) have an associated schema."""

XMLNamespaces = Namespace('http://www.w3.org/2000/xmlns/',
                          description='Namespaces in XML',
                          is_builtin_namespace=True,
                          bound_prefix='xmlns')
"""Namespaces in XML.  Not really a namespace, but is always available as C{xmlns}."""

XML = _XML('http://www.w3.org/XML/1998/namespace',
           description='XML namespace',
           schema_location='http://www.w3.org/2001/xml.xsd',
           is_builtin_namespace=True,
           is_undeclared_namespace=True,
           bound_prefix='xml',
           default_namespace='XHTML',
           in_scope_namespaces = { 'xs' : 'XMLSchema' })
"""Namespace and URI for XML itself (always available as C{xml})"""


XMLSchema = _XMLSchema('http://www.w3.org/2001/XMLSchema',
                       schema_location='http://www.w3.org/2001/XMLSchema.xsd',
                       description='XML Schema',
                       is_builtin_namespace=True,
                       in_scope_namespaces = { 'xs' : None })
"""Namespace and URI for the XMLSchema namespace (often C{xs}, or C{xsd})"""

XHTML = _XHTML('http://www.w3.org/1999/xhtml',
               description='Family of document types that extend HTML',
               schema_location='http://www.w3.org/1999/xhtml.xsd',
               is_builtin_namespace=True,
               default_namespace=XMLSchema)
"""There really isn't a schema for this, but it's used as the default
namespace in the XML schema, so define it."""


XMLSchema_hfp = Namespace('http://www.w3.org/2001/XMLSchema-hasFacetAndProperty',
                          description='Facets appearing in appinfo section',
                          schema_location='http://www.w3.org/2001/XMLSchema-hasFacetAndProperty',
                          is_builtin_namespace=True,
                          default_namespace='XMLSchema',
                          in_scope_namespaces = { 'hfp' : None
                                                , 'xhtml' : XHTML })
"""Elements appearing in appinfo elements to support data types."""

# List of built-in namespaces.
BuiltInNamespaces = [
  XMLSchema_instance,
  XMLSchema_hfp,
  XMLSchema,
  XMLNamespaces,
  XML,
  XHTML
]

__InitializedBuiltinNamespaces = False

def _InitializeBuiltinNamespaces (structures_module):
    """Invoked at the end of the L{pyxb.xmlschema.structures} module to
    initialize the component models of the built-in namespaces.

    @param structures_module: The L{pyxb.xmlschema.structures} module may not
    be importable by that name at the time this is invoked (because it is
    still being processed), so it gets passed in as a parameter."""
    global __InitializedBuiltinNamespaces
    if not __InitializedBuiltinNamespaces:
        __InitializedBuiltinNamespaces = True
        # Only certain namespaces must be initialized explicitly: the
        # XMLSchema one (which defines the datatypes that the code
        # references), and the undeclared ones (which have no schema but are
        # always present).
        XMLSchema._loadBuiltins(structures_module)
        for ns in BuiltInNamespaces:
            if ns.isUndeclaredNamespace():
                ns.validateComponentModel(structures_module)

# Set up the prefixes for xml, xmlns, etc.
_UndeclaredNamespaceMap = { }
[ _UndeclaredNamespaceMap.setdefault(_ns.boundPrefix(), _ns) for _ns in BuiltInNamespaces if _ns.isUndeclaredNamespace() ]

class NamespaceContext (object):
    """Records information associated with namespaces at a DOM node.
    """

    def defaultNamespace (self):
        """The default namespace in effect at this node.  E.g., C{xmlns="URN:default"}."""
        return self.__defaultNamespace
    __defaultNamespace = None

    def targetNamespace (self):
        """The target namespace in effect at this node.  Usually from the
        C{targetNamespace} attribute.  If no namespace is specified for the
        schema, an absent namespace is assigned."""
        return self.__targetNamespace
    __targetNamespace = None

    def inScopeNamespaces (self):
        """Map from prefix strings to L{Namespace} instances associated with those
        prefixes.  The prefix C{None} identifies the default namespace."""
        return self.__inScopeNamespaces
    __inScopeNamespaces = None

    def attributeMap (self):
        """Map from L{ExpandedName} instances (for non-absent namespace) or
        C{str} or C{unicode} values (for absent namespace) to the value of the
        named attribute."""
        return self.__attributeMap
    __attributeMap = None

    @classmethod
    def GetNodeContext (cls, node, **kw):
        """Get the L{NamespaceContext} instance that was assigned to the node.

        If none has been assigned, create one treating this as the root node,
        and the keyword parameters as configuration information (e.g.,
        default_namespace)."""
        try:
            return node.__namespaceContext
        except AttributeError:
            return NamespaceContext(node, **kw)

    def __init__ (self, dom_node, parent_context=None, recurse=True, default_namespace=None, target_namespace=None, in_scope_namespaces=None):
        """Determine the namespace context that should be associated with the
        given node and, optionally, its element children.

        @param dom_node: The DOM node
        @type dom_node: C{xml.dom.Element}
        @keyword parent_context: Optional value that specifies the context
        associated with C{dom_node}'s parent node.  If not provided, only the
        C{xml} namespace is in scope.
        @type parent_context: L{NamespaceContext}
        @keyword recurse: If True (default), create namespace contexts for all
        element children of C{dom_node}
        @type recurse: C{bool}
        @keyword default_namespace: Optional value to set as the default
        namespace.  Values from C{parent_context} would override this, as
        would an C{xmlns} attribute in the C{dom_node}.
        @type default_namespace: L{NamespaceContext}
        @keyword target_namespace: Optional value to set as the target
        namespace.  Values from C{parent_context} would override this, as
        would a C{targetNamespace} attribute in the C{dom_node}
        @type target_namespace: L{NamespaceContext}
        @keyword in_scope_namespaces: Optional value to set as the initial set
        of in-scope namespaces.  The always-present namespaces are added to
        this if necessary.
        @type in_scope_namespaces: C{dict} mapping C{string} to L{Namespace}.
        """
        global _UndeclaredNamespaceMap
        if dom_node is not None:
            dom_node.__namespaceContext = self

        self.__defaultNamespace = default_namespace
        self.__targetNamespace = target_namespace
        self.__attributeMap = { }
        self.__inScopeNamespaces = _UndeclaredNamespaceMap
        self.__mutableInScopeNamespaces = False

        if in_scope_namespaces is not None:
            if parent_context is not None:
                raise LogicError('Cannot provide both parent_context and in_scope_namespaces')
            self.__inScopeNamespaces = _UndeclaredNamespaceMap.copy()
            self.__inScopeNamespaces.update(in_scope_namespaces)
            self.__mutableInScopeNamespaces = True
        
        if parent_context is not None:
            self.__inScopeNamespaces = parent_context.inScopeNamespaces()
            self.__mutableInScopeNamespaces = False
            self.__defaultNamespace = parent_context.defaultNamespace()
            self.__targetNamespace = parent_context.targetNamespace()
            
        if dom_node is not None:
            for ai in range(dom_node.attributes.length):
                attr = dom_node.attributes.item(ai)
                if XMLNamespaces.uri() == attr.namespaceURI:
                    if not self.__mutableInScopeNamespaces:
                        self.__inScopeNamespaces = self.__inScopeNamespaces.copy()
                        self.__mutableInScopeNamespaces = True
                    if attr.value:
                        if 'xmlns' == attr.localName:
                            self.__defaultNamespace = NamespaceForURI(attr.value, create_if_missing=True)
                            self.__inScopeNamespaces[None] = self.__defaultNamespace
                        else:
                            uri = NamespaceForURI(attr.value, create_if_missing=True)
                            pfx = attr.localName
                            self.__inScopeNamespaces[pfx] = uri
                            # @todo record prefix in namespace so we can use
                            # it during generation?  I'd rather make the user
                            # specify what to use.
                    else:
                        # NB: XMLNS 6.2 says that you can undefine a default
                        # namespace, but does not say anything explicitly about
                        # undefining a prefixed namespace.  XML-Infoset 2.2
                        # paragraph 6 implies you can do this, but expat blows up
                        # if you try it.  I don't think it's legal.
                        if 'xmlns' != attr.localName:
                            raise pyxb.SchemaValidationError('Attempt to undefine non-default namespace %s' % (attr.localName,))
                        self.__defaultNamespace = None
                        self.__inScopeNamespaces.pop(None, None)
                else:
                    if attr.namespaceURI is not None:
                        uri = NamespaceForURI(attr.namespaceURI, create_if_missing=True)
                        key = ExpandedName(uri, attr.localName)
                    else:
                        key = attr.localName
                    self.__attributeMap[key] = attr.value
        
        had_target_namespace = True
        tns_uri = self.attributeMap().get('targetNamespace')
        if tns_uri is not None:
            assert 0 < len(tns_uri)
            self.__targetNamespace = NamespaceForURI(tns_uri, create_if_missing=True)
            #assert self.__defaultNamespace is not None
        elif self.__targetNamespace is None:
            if tns_uri is None:
                self.__targetNamespace = CreateAbsentNamespace()
            else:
                self.__targetNamespace = NamespaceForURI(tns_uri, create_if_missing=True)
            if self.__defaultNamespace is None:
                self.__defaultNamespace = self.__targetNamespace

        assert self.__targetNamespace is not None

        # Store in each node the in-scope namespaces at that node;
        # we'll need them for QName interpretation of attribute
        # values.
        from xml.dom import Node
        if recurse and (dom_node is not None):
            assert Node.ELEMENT_NODE == dom_node.nodeType
            for cn in dom_node.childNodes:
                if Node.ELEMENT_NODE == cn.nodeType:
                    NamespaceContext(cn, self, True)

    def interpretQName (self, name):
        """Convert the provided name into an L{ExpandedName}, i.e. a tuple of
        L{Namespace} and local name.

        If the name includes a prefix, that prefix must map to an in-scope
        namespace in this context.  Absence of a prefix maps to
        L{defaultNamespace()}, which must be provided (or defaults to the
        target namespace, if that is absent).
        
        @param name: A QName.
        @type name: C{str} or C{unicode}
        @return: An L{ExpandedName} tuple: ( L{Namespace}, C{str} )
        @raise pyxb.SchemaValidationError: The prefix is not in scope
        @raise pyxb.SchemaValidationError: No prefix is given and the default namespace is absent
        """
        assert isinstance(name, (str, unicode))
        if 0 <= name.find(':'):
            (prefix, local_name) = name.split(':', 1)
            assert self.inScopeNamespaces() is not None
            namespace = self.inScopeNamespaces().get(prefix)
            if namespace is None:
                raise pyxb.SchemaValidationError('No namespace declared for QName %s prefix' % (name,))
        else:
            local_name = name
            namespace = self.defaultNamespace()
            if namespace is None:
                raise pyxb.SchemaValidationError('QName %s with absent default namespace' % (local_name,))
        # Anything we're going to look stuff up in requires a component model.
        # Make sure we can load one, unless we're looking up in the thing
        # we're constructing (in which case it's being built right now).
        if (namespace != self.targetNamespace()):
            namespace.validateComponentModel()
        return ExpandedName(namespace, local_name)

    def queueForResolution (self, component):
        """Forwards to L{queueForResolution()<Namespace.queueForResolution>} in L{targetNamespace()}."""
        assert isinstance(component, _Resolvable_mixin)
        return self.targetNamespace().queueForResolution(component)

## Local Variables:
## fill-column:78
## End:
