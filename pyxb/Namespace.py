from exceptions_ import *
import os
import fnmatch

# Environment variable from which default path to pre-loaded namespaces is read
PathEnvironmentVariable = 'PYXB_NAMESPACE_PATH'
import os.path
DefaultBindingPath = "%s/standard/bindings/raw" % (os.path.dirname(__file__),)

# Stuff required for pickling
import cPickle as pickle

IGNORED_ARGUMENT = 'ignored argument'

class _Resolvable_mixin (object):
    """Mix-in indicating that this component may have references to unseen named components."""
    def isResolved (self):
        """Determine whether this named component is resolved.

        Override this in the child class."""
        raise LogicError('Resolved check not implemented in %s' % (self.__class__,))
    
    def _resolve (self, ignored_parameter):
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

    def _queueForResolution (self):
        self._namespaceContext().queueForResolution(self)

class NamedObjectMap (dict):
    def namespace (self):
        return self.__namespace
    __namespace = None
    
    def category (self):
        return self.__category
    __category = None

    def __init__ (self, category, namespace, *args, **kw):
        self.__category = category
        self.__namespace = namespace
        super(NamedObjectMap, self).__init__(self, *args, **kw)

class Namespace (object):
    """Represents an XML namespace, viz. a URI.

    There is at most one Namespace class instance per namespace (URI).
    The instance also supports associating arbitrary maps from names
    to objects, in separate categories.  The default categories are
    configured externally; for example, the Schema component defines a
    category for each named component in XMLSchema, and the
    customizing subclass for WSDL definitions adds categories for the
    service bindings, messages, etc.

    Namespaces can be written to and loaded from pickled files
    file.  See LoadFromFile(path) for information.
    """

    # The URI for the namespace.  If the URI is None, this is an absent
    # namespace.
    __uri = None

    # Map from category strings to NamedObjectMap instances that
    # contain the dictionary for that category.
    __categoryMap = None

    def categories (self):
        return self.__categoryMap.keys()

    def categoryMap (self, category):
        return self.__categoryMap[category]

    # A prefix bound to this namespace by standard.  Current set known are applies to
    # xml, xmlns, and xsi.
    __boundPrefix = None

    # @todo replace with collection
    __schema = None                     # The schema in which this namespace is used

    __noSchemaAssigned = None

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

    __contextDefaultNamespace = None
    __contextInScopeNamespaces = None
    __initialNamespaceContext = None
    def initialNamespaceContext (self):
        import pyxb.utils.domutils
        if self.__initialNamespaceContext is None:
            isn = { }
            if self.__contextInScopeNamespaces is not None:
                for (k, v) in self.__contextInScopeNamespaces.items():
                    isn[k] = self.__identifyNamespace(v)
            kw = { 'target_namespace' : self
                 , 'default_namespace' : self.__identifyNamespace(self.__contextDefaultNamespace)
                 , 'in_scope_namespaces' : isn }
            self.__initialNamespaceContext = pyxb.utils.domutils.NamespaceContext(None, **kw)
        return self.__initialNamespaceContext

    def __identifyNamespace (self, nsval):
        if nsval is None:
            return self
        if isinstance(nsval, (str, unicode)):
            nsval = globals().get(nsval)
        if isinstance(nsval, Namespace):
            return nsval
        raise LogicError('Cannot identify namespace from %s' % (nsval,))

    # A set of Namespace._Resolvable_mixin instances that have yet to be
    # resolved.
    __unresolvedComponents = None

    # A set of options defining how the Python bindings for this
    # namespace were generated.
    __bindingConfiguration = None
    def bindingConfiguration (self, bc=None):
        if bc is not None:
            self.__bindingConfiguration = bc
        return self.__bindingConfiguration

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
            # Absent namespaces are not stored in the registry.
            if uri is None:
                return instance
            cls.__Registry[uri] = instance
        return cls.__Registry[uri]

    @classmethod
    def _NamespaceForURI (cls, uri):
        """If a Namespace instance for the given URI exists, return it; otherwise return None.

        Note; Absent namespaces are not stored in the registry.  If you
        use one (e.g., for a schema with no target namespace), don't
        lose hold of it."""
        assert uri is not None
        return cls.__Registry.get(uri, None)

    __inSchemaLoad = False
    def _defineSchema_overload (self):
        """Attempts to load a schema for this namespace.

        The base class implementation looks at the set of available
        pre-parsed schemas, and if one matches this namespace
        unserializes it and uses it.

        Sub-classes may choose to look elsewhere, if this version
        fails or before attempting it.

        There is no guarantee that a schema has been located when this
        returns.  Caller must check.
        """
        assert self.__schema is None
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

    def nodeIsNamed (self, node, *local_names):
        return (node.namespaceURI == self.uri()) and (node.localName in local_names)

    __didValidation = False
    __inValidation = False
    def validateSchema (self):
        """Ensure this namespace is ready for use.

        If the namespace does not have an associated schema, the
        system will attempt to load one.  If unsuccessful, an
        exception will be thrown."""
        assert not self.__inValidation
        if self.__didValidation:
            return self.__schema
        try:
            self.__inValidation = True
            if self.__schema is None:
                self._defineSchema_overload()
            if not (self.__schema or self.__noSchemaDefined):
                raise PyWXSBException('No schema available for required namespace %s' % (self.uri(),))
            self.__didValidation = True
        finally:
            self.__inValidation = False
        return self.__schema

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
        self.__initialNamespaceContext = None

        # Make sure we have namespace support loaded before use, and
        # that we're not trying to do something restricted to built-in
        # namespaces
        if not is_builtin_namespace:
            XMLSchema_instance.validateSchema()
            if bound_prefix is not None:
                raise LogicError('Only permanent Namespaces may have bound prefixes')

        # We actually set the uri when this instance was allocated;
        # see __new__().
        assert self.__uri == uri
        self.__noSchemaDefined = True
        self.__boundPrefix = bound_prefix
        self.__schemaLocation = schema_location
        self.__description = description
        self.__isBuiltinNamespace = is_builtin_namespace
        self.__isUndeclaredNamespace = is_undeclared_namespace

        self.__categoryMap = { }

        self.__unresolvedComponents = []
        self.__components = set()

        assert (self.__uri is None) or (self.__Registry[self.__uri] == self)


    __absentNamespaceID = 0

    def __defineCategoryAccessors (self):
        for category in self.categories():
            accessor_name = category + 's'
            setattr(self, accessor_name, lambda _map=self.categoryMap(category): _map)

    def configureCategories (self, categories):
        if self.__categoryMap is None:
            self.__categoryMap = { }
        for category in categories:
            if not (category in self.__categoryMap):
                self.__categoryMap[category] = NamedObjectMap(category, self)
        self.__defineCategoryAccessors()
        return self

    def queueForResolution (self, resolvable):
        """Invoked to note that a component may have unresolved references.

        Newly created named components are unresolved, as are
        components which, in the course of resolution, are found to
        depend on another unresolved component.
        """
        assert isinstance(resolvable, _Resolvable_mixin)
        self.__unresolvedComponents.append(resolvable)
        return resolvable

    def resolveDefinitions (self):
        """Loop until all components associated with a name are
        sufficiently defined."""
        num_loops = 0
        while 0 < len(self.__unresolvedComponents):
            # Save the list of unresolved TDs, reset the list to
            # capture any new TDs defined during resolution (or TDs
            # that depend on an unresolved type), and attempt the
            # resolution for everything that isn't resolved.
            unresolved = self.__unresolvedComponents
            #print 'Looping for %d unresolved definitions: %s' % (len(unresolved), ' '.join([ str(_r) for _r in unresolved]))
            num_loops += 1
            #assert num_loops < 18
            
            self.__unresolvedComponents = []
            for resolvable in unresolved:
                # This should be a top-level component, or a
                # declaration inside a given scope.
#                assert (resolvable in self.__components) \
#                    or (isinstance(resolvable, _ScopedDeclaration_mixin) \
#                        and (isinstance(resolvable.scope(), ComplexTypeDefinition)))

                resolvable._resolve(IGNORED_ARGUMENT)

                # Either we resolved it, or we queued it to try again later
                assert resolvable.isResolved() or (resolvable in self.__unresolvedComponents)

                # We only clone things that have scope None.  We never
                # resolve things that have scope None.  Therefore, we
                # should never have resolved something that has
                # clones.
                if (resolvable.isResolved() and (resolvable._clones() is not None)):
                    assert False
            if self.__unresolvedComponents == unresolved:
                # This only happens if we didn't code things right, or
                # the schema actually has a circular dependency in
                # some named component.
                failed_components = []
                for d in self.__unresolvedComponents:
                    if isinstance(d, _NamedComponent_mixin):
                        failed_components.append('%s named %s' % (d.__class__.__name__, d.name()))
                    else:
                        if isinstance(d, AttributeUse):
                            print d.attributeDeclaration()
                        failed_components.append('Anonymous %s' % (d.__class__.__name__,))
                raise LogicError('Infinite loop in resolution:\n  %s' % ("\n  ".join(failed_components),))
        self.__unresolvedComponents = None
        return self
    
    def _unresolvedComponents (self):
        return self.__unresolvedComponents

    # A set containing all components, named or unnamed, that belong
    # to this schema.
    __components = None

    def _associateComponent (self, component):
        """Record that the given component is found within this schema."""
        assert component not in self.__components
        self.__components.add(component)

    def _replaceComponent (self, existing_def, replacement_def):
        self.__components.remove(existing_def)
        self.__components.add(replacement_def)
        return replacement_def

    def components (self):
        """Return a frozenset of all components, named or unnamed, belonging to this namespace."""
        return frozenset(self.__components)

    def _orderedComponents (self, component_order):
        components = self.__components
        component_by_class = {}
        for c in components:
            component_by_class.setdefault(c.__class__, []).append(c)
        ordered_components = []
        for cc in component_order:
            if cc not in component_by_class:
                continue
            component_list = component_by_class[cc]
            orig_length = len(component_list)
            component_list = self.SortByDependency(component_list, dependent_class_filter=cc, target_namespace=self)
            ordered_components.extend(component_list)
        return ordered_components

    @classmethod
    def CreateAbsentNamespace (cls):
        """Create an absent namespace.

        Use this instead of the standard constructor, in case we need
        to augment it with a uuid or the like."""
        rv = Namespace(None)
        rv.__absentNamespaceID = cls.__absentNamespaceID
        cls.__absentNamespaceID += 1
        return rv

    def uri (self):
        """Return the URI for the namespace represented by this instance.

        If the URI is None, this is an absent namespace, used to hold
        declarations not associated with a namespace (e.g., from
        schema with no target namespace)."""
        return self.__uri

    def _overrideAbsentNamespace (self, uri):
        assert self.isAbsentNamespace()
        self.__uri = uri

    def isAbsentNamespace (self):
        """Return True iff this namespace is an absent namespace.

        Absent namespaces have no namespace URI; they exist only to
        hold components created from schemas with no target
        namespace."""
        return self.__uri is None

    def boundPrefix (self):
        """Return the standard prefix to be used for this namespace.

        Only a few namespace prefixes are bound to namespaces: xml,
        xmlns, and xsi are three.  In all other cases, this method
        should return None.  The infrastructure attempts to prevent
        user creation of Namespace instances that have bound
        prefixes."""
        return self.__boundPrefix

    def isBuiltinNamespace (self):
        """Return True iff this namespace was defined by the infrastructure.

        That is the case for all namespaces in the Namespace module."""
        return self.__isBuiltinNamespace

    def isUndeclaredNamespace (self):
        """Return True iff this namespace is always available
        regardless of whether there is a declaration for it.

        This is the case only for the
        xsi(http://www.w3.org/2001/XMLSchema-instance) and
        xml(http://www.w3.org/XML/1998/namespace) namespaces."""
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

    def _schema (self, schema, allow_override=False):
        """Associate a schema instance with this namespace.

        The schema must be not be None, and the namespace must not
        already have a schema associated with it."""
        assert (schema is not None) or allow_override
        if (self.__schema is not None) and (not allow_override):
            raise LogicError('Not allowed to change the schema associated with namespace %s' % (self.uri(),))
        self.__schema = schema
        assert (schema is None) or (schema.targetNamespace() == self)
        return self.__schema

    def schema (self):
        """Return the schema instance associated with this namespace.

        If no schema has been associated, this returns None."""
        return self.__schema

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

    def _validatedSchema (self):
        """Return a reference to the associated schema, or throw an exception if none available."""
        if self.__schema is None:
            raise PyWXSBException('Cannot resolve in namespace %s: no associated schema' % (self.uri(),))
        return self.__schema

    @classmethod
    def SortByDependency (cls, components, dependent_class_filter, target_namespace):
        """Return the components that belong to this namespace, in order of dependency.

        Specifically, components are not referenced in any component
        that precedes them in the returned sequence.  Any dependency
        that is not an instance of the dependent_class_filter is
        ignored.  Declaration components that do not have a scope are
        also ignored, as nothing can depend on them except things like
        model groups which in turn are not depended on."""
        emit_order = []
        while 0 < len(components):
            new_components = []
            ready_components = []
            for td in components:
                # Anything not in this namespace is just thrown away.
                try:
                    if (target_namespace != td.targetNamespace()) and (td.targetNamespace() is not None):
                        print 'Discarding %s: tns=%s not %s' % (td, td.targetNamespace(), target_namespace)
                        continue
                except AttributeError:
                    # Unnamed things don't get discarded this way
                    pass
                # Scoped declarations that don't have a scope are tossed out too
                try:
                    if td.scope() is None:
                        print 'Discarding %s: no scope defined' % (td.name(),)
                        continue
                except AttributeError, e:
                    pass

                dep_types = td.dependentComponents()
                #print 'Type %s depends on %s' % (td, dep_types)
                ready = True
                for dtd in dep_types:
                    # If the component depends on something that is
                    # not a type we care about, just move along
                    if (dependent_class_filter is not None) and not isinstance(dtd, dependent_class_filter):
                        continue

                    # Ignore dependencies that go outside the namespace
                    try:
                        if target_namespace != dtd.targetNamespace():
                            continue
                    except AttributeError:
                        # Ignore dependencies on unnameable things
                        continue

                    # Ignore dependencies on the ur types
                    if dtd.isUrTypeDefinition():
                        continue

                    # Ignore self-dependencies
                    if dtd == td:
                        continue

                    # Do not include components that are ready but
                    # have not been placed on emit_order yet.  Doing
                    # so might result in order violations after
                    # they've been sorted.
                    if not (dtd in emit_order):
                        #print '%s depends on %s, not emitting' % (td.name(), dtd.name())
                        ready = False
                        break
                if ready:
                    ready_components.append(td)
                else:
                    new_components.append(td)
            ready_components.sort(lambda _x, _y: cmp(_x.bestNCName(), _y.bestNCName()))
            emit_order.extend(ready_components)
            if components == new_components:
                #raise LogicError('Infinite loop in order calculation:\n  %s' % ("\n  ".join( [str(_c) for _c in components] ),))
                raise LogicError('Infinite loop in order calculation:\n  %s' % ("\n  ".join( ['%s: %s' % (_c.name(),  ' '.join([ _dtd.name() for _dtd in _c.dependentComponents()])) for _c in components] ),))
            components = new_components
        return emit_order

    def addCategoryObject (self, category, local_name, named_object):
        name_map = self.categoryMap(category)
        old_object = name_map.get(local_name)
        if (old_object is not None) and (old_object != named_object):
            raise SchemaValidationError('Name %s used for multiple values in %s' % (local_name, category))
        name_map[local_name] = named_object
        return named_object

    def __str__ (self):
        if self.__uri is None:
            return 'AbsentNamespace%d' % (self.__absentNamespaceID,)
        assert self.__uri is not None
        if self.__boundPrefix is not None:
            rv = '%s=%s' % (self.__boundPrefix, self.__uri)
        else:
            rv = self.__uri
        return rv

    __PICKLE_FORMAT = '200905041925'

    def __getstate__ (self):
        """Support pickling.

        Because namespace instances must be unique, we represent them
        as their URI and any associated (non-bound) information.  This
        way allows the unpickler to either identify an existing
        Namespace instance for the URI, or create a new one, depending
        on whether the namespace has already been encountered."""
        if self.uri() is None:
            raise LogicError('Illegal to serialize absent namespaces')
        kw = {
            'schema_location': self.__schemaLocation,
            'description':self.__description,
            # * Do not include __boundPrefix: bound namespaces should
            # have already been created by the infrastructure, so the
            # unpickler should never create one.
            '__modulePath' : self.__modulePath,
            '__bindingConfiguration': self.__bindingConfiguration
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
            raise pickle.UnpicklingError('Got Namespace pickle format %s, require %s' % (format, self.__PICKLE_FORMAT))
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

    def saveToFile (self, file_path):
        """Save this namespace, with its defining schema, to the given
        file so it can be loaded later.

        This method requires that a schema be associated with the
        namespace."""
        
        if self.uri() is None:
            raise LogicError('Illegal to serialize absent namespaces')
        output = open(file_path, 'wb')
        pickler = pickle.Pickler(output, -1)
        self._PicklingNamespace(self)
        assert Namespace.PicklingNamespace() is not None
        # Next few are read when scanning for pre-built schemas
        pickler.dump(self.uri())
        pickler.dump(self)
        # Rest is only read if the schema needs to be loaded
        pickler.dump(self.__schema)
        pickler.dump(self.__categoryMap)
        self._PicklingNamespace(None)

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

    @classmethod
    def LoadFromFile (cls, file_path):
        """Create a Namespace instance with schema contents loaded
        from the given file.
        """
        print 'Attempting to load from %s' % (file_path,)
        unpickler = pickle.Unpickler(open(file_path, 'rb'))

        # Get the URI out of the way
        uri = unpickler.load()
        assert uri is not None

        # Unpack a Namespace instance.  This is *not* everything; it's
        # a small subset.  Note that if the namespace was already
        # defined, the redefinition of __new__ above will ensure a
        # reference to the existing Namespace instance is returned and
        # updated with the new information.
        instance = unpickler.load()
        assert instance.uri() == uri
        assert cls._NamespaceForURI(instance.uri()) == instance

        # Unpack the schema instance, verify that it describes the
        # namespace, and associate it with the namespace.
        schema = unpickler.load()
        instance.__noSchemaDefined = (schema is None)
        if schema is not None:
            assert schema.targetNamespace() == instance
            instance.__schema = schema

        # Augment the categories and their contents with data from the
        # saved namespace.  Note that the category maps may be
        # defined, but if so should be empty.
        assert instance.__checkCategoriesEmpty
        new_category_map = unpickler.load()
        instance.configureCategories(new_category_map.keys())
        for category in new_category_map.keys():
            instance.categoryMap(category).update(new_category_map[category])
        instance.__defineCategoryAccessors()

        #print 'Completed load of %s from %s: %s' % (instance.uri(), file_path, " ".join(instance.categories()))
        return instance

def NamespaceForURI (uri, create_if_missing=False):
    """Given a URI, provide the Namespace instance corresponding to
    it.

    If no Namespace instance exists for the URI, the None value is
    returned, unless create_is_missing is True in which case a new
    Namespace instance for the given URI is returned."""
    if uri is None:
        raise LogicError('Cannot lookup absent namespaces')
    rv = Namespace._NamespaceForURI(uri)
    if (rv is None) and create_if_missing:
        rv = Namespace(uri)
    return rv

def CreateAbsentNamespace ():
    """Create an absent namespace.

    Use this when you need a namespace for declarations in a schema
    with no target namespace.  Absent namespaces are not stored in the
    infrastructure; it is your responsibility to hold on to the
    reference you get from this."""
    return Namespace.CreateAbsentNamespace()

# The XMLSchema module used to represent namespace schemas.  This must
# be set, by invoking SetStructureModule, prior to attempting to use
# any namespace.  This is configurable since we may use different
# implementations for different purposes.
_XMLSchemaModule = None

# A mapping from namespace URIs to names of files which appear to
# provide a serialized version of the namespace with schema.
__LoadableNamespaces = None

def _LoadableNamespaceMap ():
    """Get the map from URIs to files from which the namespace data
    can be loaded."""
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

def XMLSchemaModule ():
    """Return the Python module used for XMLSchema support.

    See SetXMLSchemaModule.  If SetXMLSchemaModule has not been
    invoked, this will return the default schema module
    (PyWXSB.XMLSchema)."""
    global _XMLSchemaModule
    if _XMLSchemaModule is None:
        import pyxb.xmlschema
        SetXMLSchemaModule(pyxb.xmlschema)
    return _XMLSchemaModule

def SetXMLSchemaModule (xs_module):
    """Provide the XMLSchema module that will be used for processing.

    xs_module must contain an element "structures" which includes
    class definitions for the XMLSchema structure components; an
    element "datatypes" which contains support for the built-in
    XMLSchema data types; and a class "schema" that will be used to
    create the schema instance used for in built-in namespaces.
    """
    global _XMLSchemaModule
    if _XMLSchemaModule is not None:
        raise LogicError('Cannot SetXMLSchemaModule multiple times')
    if xs_module is None:
        raise LogicError('Cannot SetXMLSchemaModule without a valid schema module')
    if not issubclass(xs_module.schema, xs_module.structures.Schema):
        raise LogicError('SetXMLSchemaModule: Module does not provide a valid schema class')
    _XMLSchemaModule = xs_module
    # Load built-ins after setting the schema module, to avoid
    # infinite loop
    XMLSchema._loadBuiltins()

class _XMLSchema_instance (Namespace):
    """Extension of Namespace that pre-defines types available in the
    XMLSchema Instance (xsi) namespace."""

    def _defineSchema_overload (self):
        """Ensure this namespace is ready for use.

        Overrides base class implementation, since there is no schema
        for this namespace. """
        
        import pyxb.utils.domutils
        if self.schema() is None:
            if not XMLSchemaModule():
                raise LogicError('Must invoke SetXMLSchemaModule from Namespace module prior to using system.')
            schema = XMLSchemaModule().schema(namespace_context=self.initialNamespaceContext())
            self._schema(schema)
            xsc = XMLSchemaModule().structures
            schema._addNamedComponent(xsc.AttributeDeclaration.CreateBaseInstance('type', self))
            schema._addNamedComponent(xsc.AttributeDeclaration.CreateBaseInstance('nil', self))
            schema._addNamedComponent(xsc.AttributeDeclaration.CreateBaseInstance('schemaLocation', self))
            schema._addNamedComponent(xsc.AttributeDeclaration.CreateBaseInstance('noNamespaceSchemaLocation', self))
        return self

class _XML (Namespace):
    """Extension of Namespace that pre-defines types available in the
    XML (xml) namespace."""

    def _defineSchema_overload (self):
        """Ensure this namespace is ready for use.

        Overrides base class implementation, since there is no schema
        for this namespace. """
        
        if self.schema() is None:
            if not XMLSchemaModule():
                raise LogicError('Must invoke SetXMLSchemaModule from Namespace module prior to using system.')
            schema = XMLSchemaModule().schema(namespace_context=self.initialNamespaceContext())
            self._schema(schema)
            xsc = XMLSchemaModule().structures
            schema._addNamedComponent(xsc.AttributeDeclaration.CreateBaseInstance('base', self))
            schema._addNamedComponent(xsc.AttributeDeclaration.CreateBaseInstance('id', self))
            schema._addNamedComponent(xsc.AttributeDeclaration.CreateBaseInstance('space', self))
            schema._addNamedComponent(xsc.AttributeDeclaration.CreateBaseInstance('lang', self))
        return self

class _XHTML (Namespace):
    """Extension of Namespace that pre-defines types available in the
    XHTML namespace."""

    def _defineSchema_overload (self):
        """Ensure this namespace is ready for use.

        Overrides base class implementation, since there is no schema
        for this namespace.  In fact, there's nothing at all in it
        that we plan to use, so this doesn't do anything."""
        
        if self.schema() is None:
            if not XMLSchemaModule():
                raise LogicError('Must invoke SetXMLSchemaModule from Namespace module prior to using system.')
            schema = XMLSchemaModule().schema(namespace_context=self.initialNamespaceContext())
            self._schema(schema)
            # @todo Define a wildcard element declaration 'p' that takes anything.
        return self

class _XMLSchema (Namespace):
    """Extension of Namespace that pre-defines types available in the
    XMLSchema namespace.

    The types are defined when the XMLSchemaModule is set.
    """

    # No default namespace for XMLSchema

    def _loadBuiltins (self):
        """Register the built-in types into the XMLSchema namespace."""

        if self.schema() is None:
            self._schema(XMLSchemaModule().schema(namespace_context=self.initialNamespaceContext()))
        
        # Defer the definitions to the structures module
        XMLSchemaModule().structures._AddSimpleTypes(self)

        # A little validation here
        xsc = XMLSchemaModule().structures
        assert xsc.ComplexTypeDefinition.UrTypeDefinition() == self.typeDefinitions()['anyType']
        assert xsc.SimpleTypeDefinition.SimpleUrTypeDefinition() == self.typeDefinitions()['anySimpleType']

    def _defineSchema_overload (self):
        """Ensure this namespace is ready for use.

        Overrides base class implementation, since there is no
        serialized schema for this namespace."""
        
        xsc = XMLSchemaModule().structures
        return self


def AvailableForLoad ():
    """Return a list of namespace URIs for which we may be able to
    load the namespace contents from a pre-parsed file.

    Note that success of the load is not guaranteed if the packed file
    is not compatible with the schema class being used."""
    # Invoke this to ensure we have searched for loadable namespaces
    return _LoadableNamespaceMap().keys()

# Namespace and URI for the XMLSchema Instance namespace (always xsi).
# This is always built-in, and cannot have an associated schema.  We
# use it as an indicator that the namespace system has been
# initialized.  See http://www.w3.org/TR/xmlschema-1/#no-xsi
XMLSchema_instance = _XMLSchema_instance('http://www.w3.org/2001/XMLSchema-instance',
                                         description='XML Schema Instance',
                                         is_builtin_namespace=True,
                                         is_undeclared_namespace=True,
                                         bound_prefix='xsi')

# Namespaces in XML.  Not really a namespace, but is always available as xmlns.
XMLNamespaces = Namespace('http://www.w3.org/2000/xmlns/',
                          description='Namespaces in XML',
                          is_builtin_namespace=True,
#                          is_undeclared_namespace = True,
                          bound_prefix='xmlns')

# Namespace and URI for XML itself (always xml)
XML = _XML('http://www.w3.org/XML/1998/namespace',
           description='XML namespace',
           schema_location='http://www.w3.org/2001/xml.xsd',
           is_builtin_namespace=True,
           is_undeclared_namespace=True,
           bound_prefix='xml',
           default_namespace='XHTML')


## Namespace and URI for the XMLSchema namespace (often xs, or xsd)
XMLSchema = _XMLSchema('http://www.w3.org/2001/XMLSchema',
                       schema_location='http://www.w3.org/2001/XMLSchema.xsd',
                       description='XML Schema',
                       is_builtin_namespace=True,
                       in_scope_namespaces = { 'xs' : None })

# There really isn't a schema for this, but it's used as the default
# namespace in the XML schema, so define it.
XHTML = _XHTML('http://www.w3.org/1999/xhtml',
               description='Family of document types that extend HTML',
               schema_location='http://www.w3.org/1999/xhtml.xsd',
               is_builtin_namespace=True,
               default_namespace=XMLSchema)


# Elements appearing in appinfo elements to support data types
XMLSchema_hfp = Namespace('http://www.w3.org/2001/XMLSchema-hasFacetAndProperty',
                          description='Facets appearing in appinfo section',
                          schema_location='http://www.w3.org/2001/XMLSchema-hasFacetAndProperty',
                          is_builtin_namespace=True,
                          default_namespace='XMLSchema',
                          in_scope_namespaces = { 'hfp' : None
                                                , 'xhtml' : XHTML })

# List of pre-defined namespaces.  NB: XMLSchema_instance must be first.
PredefinedNamespaces = [
  XMLSchema_instance,
  XMLSchema_hfp,
  XMLSchema,
  XMLNamespaces,
  XML,
  XHTML
]

# Set up the prefixes for xml, xsi, etc.
_UndeclaredNamespaceMap = { }
[ _UndeclaredNamespaceMap.setdefault(_ns.boundPrefix(), _ns) for _ns in PredefinedNamespaces if _ns.isUndeclaredNamespace() ]

class NamespaceContext (object):

    def defaultNamespace (self):
        return self.__defaultNamespace
    __defaultNamespace = None

    def targetNamespace (self):
        return self.__targetNamespace
    __targetNamespace = None

    def inScopeNamespaces (self):
        return self.__inScopeNamespaces
    __inScopeNamespaces = None

    def attributeMap (self):
        return self.__attributeMap
    __attributeMap = None

    @classmethod
    def GetNodeContext (cls, node):
        return node.__namespaceContext

    def __init__ (self, dom_node, parent_context=None, recurse=True, default_namespace=None, target_namespace=None, in_scope_namespaces=None):
        if dom_node is not None:
            dom_node.__namespaceContext = self
        self.__defaultNamespace = default_namespace
        self.__targetNamespace = target_namespace
        self.__attributeMap = { }
        self.__inScopeNamespaces = _UndeclaredNamespaceMap
        self.__mutableInScopeNamespaces = False
        if in_scope_namespaces is not None:
            self.__inScopeNamespaces = _UndeclaredNamespaceMap.copy().update(in_scope_namespaces)
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
                            self.__inScopeNamespaces[attr.localName] = NamespaceForURI(attr.value, create_if_missing=True)
                    else:
                        # NB: XMLNS 6.2 says that you can undefine a default
                        # namespace, but does not say anything explicitly about
                        # undefining a prefixed namespace.  XML-Infoset 2.2
                        # paragraph 6 implies you can do this, but expat blows up
                        # if you try it.  Nonetheless, we'll pretend that it's
                        # legal.
                        if 'xmlns' == attr.localName:
                            self.__defaultNamespace = None
                            self.__inScopeNamespaces.pop(None, None)
                        else:
                            self.__inScopeNamespaces.pop(attr.localName, None)
                else:
                    self.__attributeMap[(attr.namespaceURI, attr.localName)] = attr.value
        
        had_target_namespace = True
        tns_uri = self.attributeMap().get((None, 'targetNamespace'), None)
        if tns_uri is not None:
            assert 0 < len(tns_uri)
            self.__targetNamespace = NamespaceForURI(tns_uri, create_if_missing=True)
        elif self.__targetNamespace is None:
            if tns_uri is None:
                self.__targetNamespace = CreateAbsentNamespace()
            else:
                self.__targetNamespace = NamespaceForURI(tns_uri, create_if_missing=True)
            if self.__defaultNamespace is None:
                self.__defaultNamespace = self.__targetNamespace

        # Store in each node the in-scope namespaces at that node;
        # we'll need them for QName interpretation of attribute
        # values.
        from xml.dom import Node
        if recurse and (dom_node is not None):
            assert Node.ELEMENT_NODE == dom_node.nodeType
            for cn in dom_node.childNodes:
                if Node.ELEMENT_NODE == cn.nodeType:
                    NamespaceContext(cn, self, True)

    def interpretQName (self, name, is_definition=False):
        assert isinstance(name, (str, unicode))
        if 0 <= name.find(':'):
            assert not is_definition
            (prefix, local_name) = name.split(':', 1)
            namespace = self.inScopeNamespaces().get(prefix, None)
            if namespace is None:
                raise SchemaValidationError('QName %s prefix is not declared' % (name,))
        else:
            local_name = name
            # Get the default namespace, or denote an absent namespace
            if is_definition:
                namespace = self.targetNamespace()
            else:
                namespace = self.defaultNamespace()
        return (namespace, local_name)

    def queueForResolution (self, component):
        assert isinstance(component, _Resolvable_mixin)
        return self.targetNamespace().queueForResolution(component)
