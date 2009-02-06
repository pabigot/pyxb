from exceptions_ import *
import os

# Environment variable from which default path to pre-loaded namespaces is read
PathEnvironmentVariable = 'PYWXSB_NAMESPACE_PATH'

# Stuff required for pickling
import cPickle as pickle
import new
from types import MethodType

class Namespace (object):
    """Represents an XML namespace, viz. a URI.

    This may be an object, or it can be an instance that does nothing
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

    @classmethod
    def NamespaceForURI (cls, uri):
        return cls.__Registry.get(uri, None)

    def checkInitialized (self):
        pass

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

    def lookupType (self, local_name):
        return self._validatedSchema().lookupType(local_name)

    def lookupAttributeGroup (self, local_name):
        return self._validatedSchema().lookupAttributeGroup(local_name)
        
    def lookupAttributeDeclaration (self, local_name):
        print 'Lookup attribute declaration %s in %s' % (local_name, self)
        return self._validatedSchema().lookupAttributeDeclaration(local_name)

    def lookupGroup (self, local_name):
        return self._validatedSchema().lookupGroup(local_name)

    def lookupElement (self, local_name):
        return self._validatedSchema().lookupElement(local_name)

    def __str__ (self):
        assert self.__uri is not None
        if self.__boundPrefix is not None:
            rv = '%s=%s' % (self.__boundPrefix, self.__uri)
        else:
            rv = self.__uri
        if self.__proxyFor is not None:
            rv = '%s[proxy]' % (rv,)
        return rv

    def __getstate__ (self):
        state = (self.__uri,)
        return state

    def __setstate__ (self, state):
        (uri,) = state
        self.__proxyFor = self.NamespaceForURI(uri)
        if self.__proxyFor is None:
            Namespace.__init__(self, *state)
        else:
            print 'Initialized proxy for %s' % (self.__proxyFor,)
            print 'Stringized proxy %s' % (self,)

    def saveToFile (self, file_path):
        if self.__schema is None:
            raise LogicError('Cannot save namespace that does not have associated schema')
        pickler = pickle.Pickler(open(file_path, 'wb'), -1)
        pickler.dump(self)
        pickler.dump(self.__schema)

    @classmethod
    def LoadFromFile (cls, file_path):
        unpickler = pickle.Unpickler(open(file_path, 'rb'))
        
        instance = unpickler.load()
        print 'Got URI %s' % (instance.uri(),)
        rv = cls.NamespaceForURI(instance.uri())
        assert rv is not None
        schema = unpickler.load()
        print 'Got schema %s' % (schema,)
        print 'Target namespace of schema: %s' % (schema.getTargetNamespace(),)
        assert schema.getTargetNamespace().uri() == rv.uri()
        rv.__schema = schema
        return rv

# The XMLSchema structures module used to represent namespace schemas.  This
# must be set, by invoking SetStructureModule, prior to attempting to use any
# namespace.
_StructuresModule = None
_SchemaClass = None

def SetStructuresModule (xsc, schema_cls):
    """Use xsc as the module containing the classes that represent XMLSchema components.

    Also use schema_cls, which must be a subclass of xsc.Schema, to
    create the schema instance used for in built-in namespaces.
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

    for ns in PredefinedNamespaces:
        ns.checkInitialized()

class __XMLSchema_instance (Namespace):
    __initialized = False

    def checkInitialized (self):
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

# Namespace and URI for the XMLSchema Instance namespace (always xsi).
# This is always built-in, and cannot have an associated schema.  We
# use it as an indicator that the namespace system has been
# initialized.  See http://www.w3.org/TR/xmlschema-1/#no-xsi
XMLSchema_instance = __XMLSchema_instance('http://www.w3.org/2001/XMLSchema-instance',
                                          description='XML Schema Instance',
                                          is_builtin_namespace=True,
                                          bound_prefix='xsi')

# Namespace and URI for the XMLSchema namespace (often xs, or xsd)
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

