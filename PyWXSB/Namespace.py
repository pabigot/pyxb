from exceptions_ import *
import os
import fnmatch

# Environment variable from which default path to pre-loaded namespaces is read
PathEnvironmentVariable = 'PYWXSB_NAMESPACE_PATH'
DefaultBindingPath = "/home/pab/pywxsb/dev/bindings"

# Stuff required for pickling
import cPickle as pickle
import new
from types import MethodType

class Namespace (object):
    """Represents an XML namespace, viz. a URI.

    There is at most one Namespace class instance per namespace (URI).
    The instance also supports associating XMLSchema structure
    components such as groups, complexTypes, etc. with the namespace.
    If an XML schema is not available, these types can be loaded from
    a pre-built file.  See LoadFromFile(path) for information.

    The PyWXSB system permits variant implementations of the
    underlying XML schema components and namespace-specific
    constructs.  To support this, you, or whoever wrote your XMLSchema
    support moodule, must register the schema component module and
    schema class definition prior to using Namespace instances.  This
    pre-loads standard namespaces including the one for XML schema.

    @note This may be an object, or it can be an instance that does nothing
    but delegate to another instance.  You probably don't need to know
    that.

    @todo I haven't encountered specifications that state a namespace
    cannot be defined by an aggregation of multiple schemas.  On the
    other hand, I haven't found a namespace that had more than one
    schema.  For now, this only associates namespaces with a single
    schema.

    """

    # The URI for the namespace
    __uri = None

    # A prefix bound to this namespace by standard.  Current set known are applies to
    # xml, xmlns, and xsi.
    __boundPrefix = None

    # @todo replace with collection
    __schema = None                     # The schema in which this namespace is used

    # A map from URIs to Namespace instances.  Namespaces instances
    # must be unique for their URI.
    __Registry = { }

    # Optional URI specifying the source for the schema for this namespace
    __schemaLocation = None

    # Optional description of the namespace
    __description = None

    # Indicates whether this namespace is built-in to the system
    __isBuiltinNamespace = False

    # Indicates that this class is a proxy for the given namespace.
    # This is required to support pickling: we represent pickled
    # namespaces as their URIs, and nested references to built-in
    # namespaces inside pickled schemas need to be proxies for the
    # real built-in, since we can't force pickle to instead substitute
    # the real one.
    __proxyFor = None

    # This trick (which requires new-style classes) allows us to
    # convert a raw Namespace instance, as created by the pickling
    # subsystem, into a proxy for a different Namespace instance,
    # e.g. one that was built-in.
    def __getattribute__ (self, aname):
        pf_aname = '_Namespace__proxyFor'
        proxy_for = object.__getattribute__(self, pf_aname)
        if pf_aname == aname:
            # Do not delegate lookups of the __proxyFor field
            return proxy_for
        # If this instance is a proxy for something else, return it or
        # invoke it.  See http://code.activestate.com/recipes/519639/
        if proxy_for is not None:
            aval = object.__getattribute__(proxy_for, aname)
            if isinstance(aval, MethodType):
                return new.instancemethod(aval.im_func, self, self.__proxyFor.__class__)
            return aval
        # Not a proxy: return the actual attribute
        return object.__getattribute__(self, aname)

    def stripProxies (self):
        pf_aname = '_Namespace__proxyFor'
        proxy_for = object.__getattribute__(self, pf_aname)
        if proxy_for is not None:
            return proxy_for.stripProxies()
        return self

    @classmethod
    def _NamespaceForURI (cls, uri):
        return cls.__Registry.get(uri, None)

    def checkInitialized (self):
        afn = _LoadedSchemas.get(self.uri(), None)
        if afn is not None:
            self.LoadFromFile(afn)
        return self

    def __init__ (self, uri,
                  schema=None,
                  schema_location=None,
                  description=None,
                  is_builtin_namespace=False,
                  bound_prefix=None):
        super(Namespace, self).__init__()
        # Make sure we have namespace support loaded before use, and
        # that we're not trying to do something restricted to built-in
        # namespaces
        if not is_builtin_namespace:
            XMLSchema_instance.checkInitialized()
            
            if bound_prefix is not None:
                raise LogicError('Only permanent Namespaces may have bound prefixes')

        # Make sure the URI is given and has not been given before
        if uri is None:
            raise LogicError('Namespace requires a URI')
        if uri in self.__Registry:
            raise LogicError('Cannot create multiple namespace instances for %s' % (uri,))

        self.__uri = uri
        self.__boundPrefix = bound_prefix
        self.__schema = schema
        self.__schemaLocation = schema_location
        self.__description = description
        self.__isBuiltinNamespace = is_builtin_namespace

        self.__Registry[self.__uri] = self

    def uri (self): return self.__uri
    def boundPrefix (self): return self.__boundPrefix
    def isBuiltinNamespace (Self): return self.__isBuiltinNamespace

    def schema (self, schema=None):
        if schema is not None:
            self.__schema = schema
        return self.__schema

    def schemaLocation (self, schema_location=None):
        if schema_location is not None:
            self.__schemaLocation = schema_location
        return self.__schemaLocation

    def description (self, description=None):
        if description is not None:
            self.__description = description
        return self.__description

    def _validatedSchema (self):
        if self.__schema is None:
            raise PyWXSBException('Cannot resolve in namespace %s: no associated schema' % (self.uri(),))
        return self.__schema

    def lookupTypeDefinition (self, local_name):
        """Look up a named type in the namespace.

        This delegates to the associated schema.  It returns a
        SimpleTypeDefnition or ComplexTypeDefinition instance, or None
        if the name does not denote a type."""
        return self._validatedSchema()._lookupTypeDefinition(local_name)

    def lookupAttributeGroupDefinition (self, local_name):
        """Look up a named attribute group in the namespace.

        This delegates to the associated schema.  It returns an
        AttributeGroupDefinition, or None if the name does not denote
        an attribute group."""
        return self._validatedSchema()._lookupAttributeGroupDefinition(local_name)
        
    def lookupModelGroupDefinition (self, local_name):
        """Look up a named model group in the namespace.

        This delegates to the associated schema.  It returns a
        ModelGroupDefinition, or None if the name does not denote a
        model group."""
        return self._validatedSchema()._lookupModelGroupDefinition(local_name)

    def lookupAttributeDeclaration (self, local_name):
        """Look up a named attribute in the namespace.

        This delegates to the associated schema.  It returns an
        AttributeDeclaration, or None if the name does not denote an
        attribute."""
        return self._validatedSchema()._lookupAttributeDeclaration(local_name)

    def lookupElementDeclaration (self, local_name):
        """Look up a named element in the namespace.

        This delegates to the associated schema.  It returns an
        ElementDeclaration, or None if the name does not denote an
        element."""
        return self._validatedSchema()._lookupElementDeclaration(local_name)

    def __str__ (self):
        assert self.__uri is not None
        if self.__boundPrefix is not None:
            rv = '%s=%s' % (self.__boundPrefix, self.__uri)
        else:
            rv = self.__uri
        if self.__proxyFor is not None:
            rv = '%s[proxy]' % (rv,)
        return rv

    __PICKLE_FORMAT = '200902061410'

    def __getstate__ (self):
        """Support pickling.

        Because namespace instances must be unique, we represent them
        as their URI and any associated (non-bound) information.  This
        way an unpickled instance that conflicts with a built-in or
        other pre-loaded instance can be configured to proxy for the
        real one."""
        kw = {
            'schema_location': self.__schemaLocation,
            'description':self.__description
            # Do not include __boundPrefix: bound namespaces should
            # have already been created by the infrastructure.
            }
        args = ( self.__uri, )
        return ( self.__PICKLE_FORMAT, args, kw )

    def __setstate__ (self, state):
        """Initialize the instance from the packed state.

        Because we can't determine what insteance is returned, if the
        namespace already has an instance, we'll proxy for it.
        Otherwise, we call the __init__ method and register this as
        the official implementation for the namespace.

        This will throw an exception if the state is not inn a format
        recognized by this method."""
        ( format, args, kw ) = state
        if self.__PICKLE_FORMAT != format:
            raise UnpicklingError('Got Namespace pickle format %s, require %s' % (format, self.__PICKLE_FORMAT))
        ( uri, ) = args
        self.__proxyFor = self._NamespaceForURI(uri)
        if self.__proxyFor is None:
            Namespace.__init__(self, *args, **kw)

    def saveToFile (self, file_path):
        """Save this namespace, with its defining schema, to the given
        file so it can be loaded later.

        This method requires that a schema be associated with the
        namespace."""
        
        if self.__schema is None:
            # @todo use a better exception
            raise LogicError("Won't save namespace that does not have associated schema: %s", self.uri())
        output = open(file_path, 'wb')
        pickler = pickle.Pickler(output, -1)
        pickler.dump(self.uri())
        pickler.dump(self)
        pickler.dump(self.__schema)

    @classmethod
    def LoadFromFile (cls, file_path):
        """Create a Namespace instance with schema contents loaded
        from the given file.
        """
        unpickler = pickle.Unpickler(open(file_path, 'rb'))

        # Get the URI out of the way
        uri = unpickler.load()

        # Unpack a Namespace instance.  Note that if the namespace was
        # already defined, this instance will be a proxy that
        # delegates to the original.
        instance = unpickler.load()
        assert instance.uri() == uri

        # Get the real Namespace instance (never mind the proxy).
        rv = cls._NamespaceForURI(instance.uri())
        assert rv is not None
        assert instance.stripProxies() == rv

        # Unpack the schema instance, verify that it describes the
        # namespace, and associate it with the namespace.
        schema = unpickler.load()
        assert schema.getTargetNamespace().uri() == rv.uri()
        rv.__schema = schema
        return rv

def NamespaceForURI (uri):
    """Given a URI, provide the Namespace instance corresponding to
    it.

    If no Namespace instance exists for the URI, the None value is
    returned."""
    return Namespace._NamespaceForURI(uri)

# The XMLSchema structures module used to represent namespace schemas.  This
# must be set, by invoking SetStructureModule, prior to attempting to use any
# namespace.
_StructuresModule = None

# The Python class that implements the XMLSchema schema component.
# This is not necessarily the same as _SchemaClass.schema, though it
# must be a subclass of that class.
_SchemaClass = None

# A mapping from namespace URIs to instances of Namespace that we have
# loaded.
# @todo Fix this anomaly: is it schemas available, schemas read from
# files, or just namespaces?
_LoadedSchemas = { }

def SetStructuresModule (xsc, schema_cls):
    """Use xsc as the module containing the classes that represent XMLSchema components.

    Also requires schema_cls, which must be a subclass of xsc.Schema,
    and is used to create the schema instance used for in built-in
    namespaces.
    """
    global _StructuresModule
    global _SchemaClass
    if _StructuresModule is not None:
        raise LogicError('Cannot SetStructuresModule multiple times')
    if xsc is None:
        raise LogicError('Cannot SetStructuresModule without a valid structures module')
    if not issubclass(schema_cls, xsc.Schema):
        raise LogicError('Cannot SetStructuresModule without a valid class to represent schemas [%s]', schema_cls)
    _StructuresModule = xsc
    _SchemaClass = schema_cls

    bindings_path = os.environ.get(PathEnvironmentVariable, DefaultBindingPath)
    print bindings_path
    for fn in os.listdir(bindings_path):
        if fnmatch.fnmatch(fn, '*.wxs'):
            afn = os.path.join(bindings_path, fn)
            infile = open(afn, 'rb')
            unpickler = pickle.Unpickler(infile)
            uri = unpickler.load()
            _LoadedSchemas[uri] = afn
            print 'Pre-built schema for %s available in %s' % (uri, afn)

class __XMLSchema_instance (Namespace):
    """Extension of Namespace that pre-defines types available in the
    XMLSchema Instance (xsi) namespace.."""

    __initialized = False

    def checkInitialized (self):
        """Ensure this namespace is ready for use.

        Overrides base clsas implementation."""
        
        global _StructuresModule
        global _SchemaClass
        if not self.__initialized:
            if not _StructuresModule or not _SchemaClass:
                raise LogicError('Must invoke SetStructuresModule from Namespace module prior to using system.')
            self.__initialized = True
        xsi = _SchemaClass()
        xsi._addNamedComponent(_StructuresModule.AttributeDeclaration.CreateBaseInstance('type', self))
        xsi._addNamedComponent(_StructuresModule.AttributeDeclaration.CreateBaseInstance('nil', self))
        xsi._addNamedComponent(_StructuresModule.AttributeDeclaration.CreateBaseInstance('schemaLocation', self))
        xsi._addNamedComponent(_StructuresModule.AttributeDeclaration.CreateBaseInstance('noNamespaceSchemaLocation', self))
        self.__schema = xsi
        return self

def AvailableForLoad ():
    """Return a list of namespace URIs for which we are able to load
    the namespace contents from a pre-built file.

    Note that success of the load is not guaranteed if the packed file
    is not compatible with the schema class being used."""
    return _LoadedSchemas.keys()

# Namespace and URI for the XMLSchema Instance namespace (always xsi).
# This is always built-in, and cannot have an associated schema.  We
# use it as an indicator that the namespace system has been
# initialized.  See http://www.w3.org/TR/xmlschema-1/#no-xsi
XMLSchema_instance = __XMLSchema_instance('http://www.w3.org/2001/XMLSchema-instance',
                                          description='XML Schema Instance',
                                          is_builtin_namespace=True,
                                          bound_prefix='xsi')

## Namespace and URI for the XMLSchema namespace (often xs, or xsd)
XMLSchema = Namespace('http://www.w3.org/2001/XMLSchema',
                      schema_location='http://www.w3.org/2001/XMLSchema.xsd',
                      description='XML Schema',
                      is_builtin_namespace=True)

# Namespaces in XML
XMLNamespaces = Namespace('http://www.w3.org/2000/xmlns/',
                          description='Namespaces in XML',
                          is_builtin_namespace=True,
                          bound_prefix='xmlns')

# Namespace and URI for XML itself (always xml)
XML = Namespace('http://www.w3.org/XML/1998/namespace',
                description='XML namespace',
                schema_location='http://www.w3.org/2001/xml.xsd',
                is_builtin_namespace=True,
                bound_prefix='xml')

# List of pre-defined namespaces.  NB: XMLSchema_instance must be first.
PredefinedNamespaces = [
  XMLSchema_instance, XMLSchema, XMLNamespaces, XML
]

