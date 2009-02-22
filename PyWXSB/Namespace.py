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
    support module, must register the schema component module and
    schema class definition prior to using Namespace instances,
    through the SetXMLSchemaModule interface.  If no module is
    registered, a default one will be assumed.

    @todo Section 4.2.1 of Structures specifies that, indeed, one can
    have multiple schema documents that define the schema components
    for a namespace.  This is what the include element does.  On the
    other hand, I haven't found a namespace that had more than one
    schema document.  For now, this only associates namespaces with a
    single schema.

    """

    # The URI for the namespace
    __uri = None

    # A prefix bound to this namespace by standard.  Current set known are applies to
    # xml, xmlns, and xsi.
    __boundPrefix = None

    # @todo replace with collection
    __schema = None                     # The schema in which this namespace is used

    # A map from URIs to Namespace instances.  Namespaces instances
    # must be unique for their URI.  See __new__().
    __Registry = { }

    # Optional URI specifying the source for the schema for this namespace
    __schemaLocation = None

    # Optional description of the namespace
    __description = None

    # Indicates whether this namespace is built-in to the system
    __isBuiltinNamespace = False

    # A string denoting the path by which this namespace is imported into
    # generated Python modules
    __modulePath = None

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
            cls.__Registry[uri] = instance
        return cls.__Registry[uri]

    @classmethod
    def _NamespaceForURI (cls, uri):
        """If a Namespace instance for the given URI exists, return it; otherwise return None."""
        return cls.__Registry.get(uri, None)

    def _defineSchema_overload (self):
        """Attempts to load a schema for this namespace.

        The base class implementation looks at the set of available
        pre-built schemas, and if one matches this namespace
        unserializes it and uses it.

        Sub-classes may choose to look elsewhere, if this version
        fails or before attempting it.

        There is no guarantee that a schema has been located when this
        returns.  Caller must check.
        """
        assert self.__schema is None

        afn = _LoadableNamespaceMap().get(self.uri(), None)
        if afn is not None:
            self.LoadFromFile(afn)

    def validateSchema (self):
        """Ensure this namespace is ready for use.

        If the namespace does not have an associated schema, the
        system will attempt to load one.  If unsuccessful, an
        exception will be thrown."""
        if self.__schema is None:
            self._defineSchema_overload()
        if not self.__schema:
            raise PyWXSBException('No schema available for required namespace %s' % (self.uri(),))
        return self.__schema

    def __init__ (self, uri,
                  schema_location=None,
                  description=None,
                  is_builtin_namespace=False,
                  bound_prefix=None):
        """Create a new Namespace.

        The URI must be non-None, and must not already be assigned to
        a Namespace instance.  See NamespaceForURI().
        
        User-created Namespace instances may also provide a
        schemaLocation and a description.

        Users should never provide a is_builtin_namespace parameter.
        """

        # New-style superclass invocation
        super(Namespace, self).__init__()

        # Make sure we have namespace support loaded before use, and
        # that we're not trying to do something restricted to built-in
        # namespaces
        if not is_builtin_namespace:
            XMLSchema_instance.validateSchema()
            if bound_prefix is not None:
                raise LogicError('Only permanent Namespaces may have bound prefixes')

        # Make sure the URI is given and has not been given before
        if uri is None:
            raise LogicError('Namespace requires a URI')

        # We actually set the uri when this instance was allocated;
        # see __new__().
        assert self.__uri == uri
        self.__boundPrefix = bound_prefix
        self.__schemaLocation = schema_location
        self.__description = description
        self.__isBuiltinNamespace = is_builtin_namespace

        assert self.__Registry[self.__uri] == self

    def uri (self):
        """Return the URI for the namespace represented by this instance."""
        return self.__uri

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

    def modulePath (self, module_path=None):
        if module_path is not None:
            self.__modulePath = module_path
        return self.__modulePath

    def _schema (self, schema):
        """Associate a schema instance with this namespace.

        The schema must be not be None, and the namespace must not
        already have a schema associated with it."""
        assert schema is not None
        if self.__schema is not None:
            raise LogicError('Not allowed to change the schema associated with namespace %s' % (self.uri(),))
        self.__schema = schema
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

    def typeDefinitions (self):
        return self._validatedSchema()._typeDefinitions()

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
        return rv

    __PICKLE_FORMAT = '200902061410'

    def __getstate__ (self):
        """Support pickling.

        Because namespace instances must be unique, we represent them
        as their URI and any associated (non-bound) information.  This
        way allows the unpickler to either identify an existing
        Namespace instance for the URI, or create a new one, depending
        on whether the namespace has already been encountered."""
        kw = {
            'schema_location': self.__schemaLocation,
            'description':self.__description
            # Do not include __boundPrefix: bound namespaces should
            # have already been created by the infrastructure, so the
            # unpickler should never create one.
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
            raise UnpicklingError('Got Namespace pickle format %s, require %s' % (format, self.__PICKLE_FORMAT))
        ( uri, ) = args
        assert self.__uri == uri
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
        
        if self.__schema is None:
            # @todo use a better exception
            raise LogicError("Won't save namespace that does not have associated schema: %s", self.uri())
        output = open(file_path, 'wb')
        pickler = pickle.Pickler(output, -1)
        self._PicklingNamespace(self)
        assert Namespace.PicklingNamespace() is not None
        pickler.dump(self.uri())
        pickler.dump(self)
        pickler.dump(self.__schema)
        self._PicklingNamespace(None)

    @classmethod
    def LoadFromFile (cls, file_path):
        """Create a Namespace instance with schema contents loaded
        from the given file.
        """
        unpickler = pickle.Unpickler(open(file_path, 'rb'))

        # Get the URI out of the way
        uri = unpickler.load()

        # Unpack a Namespace instance.  Note that if the namespace was
        # already defined, the redefinition of __new__ above will
        # ensure a reference to the existing Namespace instance is
        # returned.
        instance = unpickler.load()
        assert instance.uri() == uri
        assert cls._NamespaceForURI(instance.uri()) == instance

        # Unpack the schema instance, verify that it describes the
        # namespace, and associate it with the namespace.
        schema = unpickler.load()
        assert schema.getTargetNamespace() == instance
        instance.__schema = schema
        print 'Completed load of %s from %s' % (instance.uri(), file_path)
        return instance

def NamespaceForURI (uri):
    """Given a URI, provide the Namespace instance corresponding to
    it.

    If no Namespace instance exists for the URI, the None value is
    returned."""
    return Namespace._NamespaceForURI(uri)

# The XMLSchema module used to represent namespace schemas.  This must
# be set, by invoking SetStructureModule, prior to attempting to use
# any namespace.  This is configurable since we may use different
# implementations for different purposes.
_XMLSchemaModule = None

# A mapping from namespace URIs to names of files which appear to
# provide a serialized version of the namespace with schema.
__LoadableNamespaces = { }

def _LoadableNamespaceMap ():
    # Force resolution of the module; invoking SetXMLSchemaModule is
    # what initializes this map.
    XMLSchemaModule()
    return __LoadableNamespaces

def XMLSchemaModule ():
    """Return the Python module used for XMLSchema support.

    See SetXMLSchemaModule."""
    global _XMLSchemaModule
    if _XMLSchemaModule is None:
        import XMLSchema
        SetXMLSchemaModule(XMLSchema)
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
        raise LogicError('Cannot SetXMLSchemaModule without a valid structures module')
    if not issubclass(xs_module.schema, xs_module.structures.Schema):
        raise LogicError('SetXMLSchemaModule: Module does not provide a valid schema class')
    _XMLSchemaModule = xs_module

    # Look for pre-existing pickled schema
    bindings_path = os.environ.get(PathEnvironmentVariable, DefaultBindingPath)
    for fn in os.listdir(bindings_path):
        if fnmatch.fnmatch(fn, '*.wxs'):
            afn = os.path.join(bindings_path, fn)
            infile = open(afn, 'rb')
            unpickler = pickle.Unpickler(infile)
            uri = unpickler.load()
            __LoadableNamespaces[uri] = afn
            print 'Pre-built schema for %s available in %s' % (uri, afn)

class _XMLSchema_instance (Namespace):
    """Extension of Namespace that pre-defines types available in the
    XMLSchema Instance (xsi) namespace."""

    def _defineSchema_overload (self):
        """Ensure this namespace is ready for use.

        Overrides base class implementation, since there is no schema
        for this namespace. """
        
        if self.schema() is None:
            if not XMLSchemaModule():
                raise LogicError('Must invoke SetXMLSchemaModule from Namespace module prior to using system.')
            schema = XMLSchemaModule().schema()
            xsc = XMLSchemaModule().structures
            schema._addNamedComponent(xsc.AttributeDeclaration.CreateBaseInstance('type', self))
            schema._addNamedComponent(xsc.AttributeDeclaration.CreateBaseInstance('nil', self))
            schema._addNamedComponent(xsc.AttributeDeclaration.CreateBaseInstance('schemaLocation', self))
            schema._addNamedComponent(xsc.AttributeDeclaration.CreateBaseInstance('noNamespaceSchemaLocation', self))
            self._schema(schema)
        return self

class _XMLSchema (Namespace):
    """Extension of Namespace that pre-defines types available in the
    XMLSchema namespace."""

    def _defineSchema_overload (self):
        # The only reason we're overloading this is to ensure that
        # unpickling preserved pointer equivalence of the ur types.
        super(_XMLSchema, self)._defineSchema_overload()
        if self.schema() is not None:
            xsc = XMLSchemaModule().structures
            assert xsc.ComplexTypeDefinition.UrTypeDefinition() == self.lookupTypeDefinition('anyType')
            assert xsc.SimpleTypeDefinition.SimpleUrTypeDefinition() == self.lookupTypeDefinition('anySimpleType')

    def requireBuiltins (self, schema):
        """Ensure we're ready to use the XMLSchema namespace while processing the given schema.

        If a pre-built schema definition is available, use it.
        Otherwise, we're bootstrapping.  If we're bootstrapping the
        XMLSchema namespace, the caller should have already associated
        the schema we're to use.  If not, we'll create a basic one
        just to make progress.
        """
        
        if self.schema() is None:
            self._defineSchema_overload()
            if self.schema() is None:
                # Bootstrapping non-XMLSchema schema.
                self._schema(XMLSchemaModule().schema()).setTargetNamespace(self)
                XMLSchemaModule().datatypes._AddSimpleTypes(self.schema())
        elif self.schema() == schema:
            # Bootstrapping XMLSchema.
            XMLSchemaModule().datatypes._AddSimpleTypes(self.schema())
        assert XMLSchema == self.schema().getTargetNamespace()
        return self.schema()

def AvailableForLoad ():
    """Return a list of namespace URIs for which we may be able to
    load the namespace contents from a pre-built file.

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
                                          bound_prefix='xsi')

## Namespace and URI for the XMLSchema namespace (often xs, or xsd)
XMLSchema = _XMLSchema('http://www.w3.org/2001/XMLSchema',
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

# Elements appearing in appinfo elements to support data types
XMLSchema_hfp = Namespace('http://www.w3.org/2001/XMLSchema-hasFacetAndProperty',
                          description='Facets appearing in appinfo section',
                          schema_location = 'http://www.w3.org/2001/XMLSchema-hasFacetAndProperty',
                          is_builtin_namespace=True)

# List of pre-defined namespaces.  NB: XMLSchema_instance must be first.
PredefinedNamespaces = [
  XMLSchema_instance,
  XMLSchema_hfp,
  XMLSchema,
  XMLNamespaces,
  XML
]
