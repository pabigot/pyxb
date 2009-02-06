from exceptions_ import *
import os

# Environment variable from which default path to pre-loaded namespaces is read
PathEnvironmentVariable = 'PYWXSB_NAMESPACE_PATH'

class Namespace:
    """Represents an XML namespace, viz. a URI.

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
    
    def checkInitialized (self):
        pass

    def __init__ (self, uri,
                  schema=None,
                  schema_location=None,
                  description=None,
                  is_builtin_namespace=False,
                  bound_prefix=None):
        # Make sure we have namespace support loaded before use, and
        # that we're not trying to do something restricted to built-in
        # namespaces
        if not is_builtin_namespace:
            XMLSchema_instance.checkInitialized()
            
            if bound_prefix is not None:
                raise LogicError('Only permanent Namespaces may have bound prefixes')

        # Make sure the URI is given and has not been given before
        if uri is None:
            raise LogicException('Namespace requires a URI')
        if uri in self.__Registry:
            raise LogicException('Cannot create multiple namespace instances for %s' % (uri,))

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
        if self.__boundPrefix is not None:
            return '%s=%s' % (self.__boundPrefix, self.__uri)
        return self.__uri

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

