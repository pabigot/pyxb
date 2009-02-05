from exceptions_ import *
import os

# Namespace and URI for the XMLSchema namespace (often xs, or xsd)
XMLSchema = None
XMLSchema_uri = 'http://www.w3.org/2001/XMLSchema'

# Namespace and URI for the XMLSchema Instance namespace (always xsi).
# This is always built-in, and cannot have an associated schema.  We
# use it as an indicator that the namespace system has been
# initialized.  See http://www.w3.org/TR/xmlschema-1/#no-xsi
XMLSchema_instance = None
XMLSchema_instance_uri = 'http://www.w3.org/2001/XMLSchema-instance'
XMLSchema_instance_prefix = 'xsi'

# Namespace and URI for XML namespaces (always xmlns)
XMLNamespaces = None
XMLNamespaces_uri = 'http://www.w3.org/2000/xmlns/'
XMLNamespaces_prefix = 'xmlns'

# Namespace and URI for XML itself (always xml)
XML = None
XML_uri = 'http://www.w3.org/XML/1998/namespace'
XML_prefix = 'xml'

# Environment variable from which default path to pre-loaded namespaces is read
PathEnvironmentVariable = 'PYWXSB_NAMESPACE_PATH'

class Namespace:
    """Represents an XML namespace, viz. a URI.

    @todo A namespace can be targeted by multiple schema; currently we
    assume only one.

    @todo A namespace should not be coupled with the prefix by which
    it is known in a particular schema.
    """
    
    __uri = None                        # The URI for the namespace
    __boundPrefix = None                     # The prefix by which the namespace is known
    __schema = None                     # The schema in which this namespace is used

    __Preloaded = [ ]
    __xs = None
    __xsi = None
    __xml = None
    __xmlns = None

    @classmethod
    def __MaybePreload (cls):
        if XML is None:
            import XMLSchema.structures as xsc
            cls.Preload(xsc)

    @classmethod
    def XML (cls):
        cls.__MaybePreload()
        return XML

    @classmethod
    def XMLSchema (cls):
        cls.__MaybePreload()
        return XMLSchema

    @classmethod
    def XMLSchema_uri (cls):
        return XMLSchema_uri

    @classmethod
    def Preload (cls, xsc, pywxsb_schema_path=None, ignore_prefix=None):
        if pywxsb_schema_path is None:
            if PathEnvironmentVariable in os.environ:
                pywxsb_schema_path = os.environ.get(PathEnvironmentVariable)
            else:
                pywxsb_schema_path = '.'

        # xsi is ultra-special, in that it can't even be expressed in
        # a schema.  Its elements must be built-in.  See
        # http://www.w3.org/TR/xmlschema-1/#no-xsi
        global XMLSchema_instance
        assert XMLSchema_instance is None
        XMLSchema_instance = cls(XMLSchema_instance_uri, XMLSchema_instance_prefix, in_static_constructor=True)
        xsc.AttributeDeclaration.CreateBaseInstance('type', XMLSchema_instance)
        xsc.AttributeDeclaration.CreateBaseInstance('nil', XMLSchema_instance)
        xsc.AttributeDeclaration.CreateBaseInstance('schemaLocation', XMLSchema_instance)
        xsc.AttributeDeclaration.CreateBaseInstance('noNamespaceSchemaLocation', XMLSchema_instance)

        if ignore_prefix is not None:
            raise IncompleteImplementationError('Need to support ignore_prefix in Namespace.Preload')

        global XML
        XML = cls(XML_uri, XML_prefix, in_static_constructor=True)
        
        global XMLSchema
        # NB: No default prefix for this one
        XMLSchema = cls(XMLSchema_uri, in_static_constructor=True)
        
        global XMLNamespaces
        XMLNamespaces = cls(XMLNamespaces_uri, XMLNamespaces_prefix, in_static_constructor=True)

    def __init__ (self, uri=None, prefix=None, schema=None, in_static_constructor=False):
        # Make sure we have namespace support loaded before use
        if (XMLSchema_instance is None) and not in_static_constructor:
            self.__MaybePreload()
        self.__uri = uri
        if prefix is not None:
            if not in_static_constructor:
                raise LogicError('Only permanent Namespaces have bound prefixes')
            self.__boundPrefix = prefix
        self.__schema = schema

    def boundPrefix (self):
        return self.__boundPrefix
    
    def uri (self):
        return self.__uri

    def schema (self, schema=None):
        if schema is not None:
            self.__schema = schema
        return self.__schema

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

class XMLName:
    """This class represents an XML name, optionally including a
    namespace prefix.

    See: http://www.w3.org/TR/REC-xml-names/
    """
    # 

    # Prefix used to identify the namespace.
    __xmlNamePrefix = None

    # The namespace (which is NOT the prefix; it's the URI associated
    # with the prefix).
    __xmlNamespace = None

    # The name of the entity within its namespace.
    __xmlNameLocalPart = None

    # The entity name consisting of prefix (if present) and localname,
    # separated by a colon.
    __xmlQualifiedName = None

    def __init__ (self, qualified_name=None):
        if qualified_name is not None:
            self.setXMLName(qualified_name)

    def getNameComponents (self):
        return ( self.__xmlNamePrefix, self.__xmlNameLocalPart )

    def __unparseXMLName (cls, qualified_name):
        '''Return a pair consisting of the namespace (if any) and the unqualified name.'''
        if qualified_name is None:
            return (None, None)
        if 0 <= qualified_name.find(':'):
            return tuple(qualified_name.split(':', 1))
        return (Namespace.TargetPrefix(), qualified_name)
    __unparseXMLName = classmethod(__unparseXMLName)

    def setXMLName (self, qualified_name):
        '''Initializes entity's name components from a qualified name.'''
        (self.__xmlNamePrefix, self.__xmlNameLocalPart) = self.__unparseXMLName(qualified_name)
        if self.__xmlNamePrefix is not None:
            self.__xmlQualifiedName = '%s:%s' % (self.__xmlNamePrefix, self.__xmlNameLocalPart)
            self.__xmlNamespace = Namespace.NamespaceForPrefix(self.__xmlNamePrefix)
        else:
            self.__xmlQualifiedName = self.__xmlNameLocalPart

    def getXMLName (self, force_qualified=False):
        '''Return the identifier used to look up the entity.

        If this name is in the default namespace, and the
        force_qualified parameter is False, only the local part of the
        name is returned.'''
        if self.__xmlNamespace == Namespace.GetTargetNamespace():
            return self.__xmlNameLocalPart
        return self.__xmlQualifiedName

    def __str__ (self):
        return self.getXMLName()


