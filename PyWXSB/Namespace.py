# URI for the XMLSchema namespace
XMLSchema = 'http://www.w3.org/2001/XMLSchema'

# URI for the XMLSchema Instance namespace
XMLSchema_instance = 'http://www.w3.org/2001/XMLSchema-instance'

class Namespace:
    """Represents an XML namespace, viz. a URI.

    @todo A namespace can be targeted by multiple schema; currently we
    assume only one."""
    
    __uri = None                        # The URI for the namespace
    __prefix = None                     # The prefix by which the namespace is known in a schema
    __schema = None                     # The schema in which this namespace is used

    def __init__ (self, uri=None, prefix=None, schema=None):
        self.__uri = uri
        self.__prefix = prefix
        self.__schema = schema

    def prefix (self, value=None):
        if value is not None:
            self.__prefix = value
        return self.__prefix
    
    def uri (self): return self.__uri

    def schema (self, schema=None):
        if schema is not None:
            self.__schema = schema
        return self.__schema

    def lookupSimpleType (self, local_name):
        if self.__schema is None:
            raise LogicError('lookupSimpleType(%s) failed: Namespace %s has no associated schema' % (local_name, self.uri()))
        return self.__schema.lookupSimpleType(local_name)

    def qualifiedName (self, local_name, default_namespace=None):
        """Return a namespace-qualified name for the given local name
        in this namespace.

        If a default namespace is provided, and it is this namespace,
        the local name is returned without qualifying it."""
        if default_namespace == self:
            return local_name
        if self.__prefix is None:
            raise LogicError('Namespace %s has no prefix to qualify name "%s"; default %s' % (self.__uri, local_name, default_namespace))
        return '%s:%s' % (self.__prefix, local_name)

    def __str__ (self):
        return 'xmlns:%s=%s' % (self.__prefix, self.__uri)

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


