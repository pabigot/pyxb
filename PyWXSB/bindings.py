from PyWXSB.exceptions_ import *
import XMLSchema as xs
import domutils

class PyWXSB_element (object):
    __content = None
    
    def __setContent (self, content):
        self.__content = content
        if content is not None:
            if issubclass(self._TypeDefinition, PyWXSB_CTD_simple):
                self.__content = self.content().content()
        return self

    def __init__ (self, *args, **kw):
        """Create a new element.

        If the element is a complex type with simple content, the
        value of the content is dereferenced once.
        """
        if hasattr(self._TypeDefinition, 'Factory'):
            self.__setContent(self._TypeDefinition.Factory(*args, **kw))
        

    # Delegate
    def __getattr__ (self, name):
        return getattr(self.__content, name)

    def content (self): return self.__content
    
    def _content (self, content):
        self.__content = content
        return self
 
    @classmethod
    def CreateFromDOM (cls, node):
        rv = cls()
        rv.__setContent(cls._TypeDefinition.CreateFromDOM(node))
        return rv

class AttributeUse (object):
    __field = None     # Python class field
    __tag = None       # Unicode XML tag @todo not including namespace
    __dataType = None # PST datatype
    __defaultValue = None       # Unicode default value, or None
    __required = False          # If True, attribute must appear
    __prohibited = False        # If True, attribute must not appear

    def __init__ (self, field, tag, data_type, default_value=None, required=False, prohibited=False):
        self.__field = field
        self.__tag = tag
        self.__dataType = data_type
        self.__defaultValue = default_value
        self.__required = required
        self.__prohibited = prohibited

    def setFromDOM (self, ctd_instance, node):
        unicode_value = self.__defaultValue
        if node.hasAttribute(self.__tag):
            if self.__prohibited:
                raise ProhibitedAttributeError('Prohibited attribute %s found' % (self.__tag,))
            unicode_value = node.getAttribute(self.__tag)
        else:
            if self.__required:
                raise MissingAttributeError('Required attribute %s not found' % (self.__tag,))
        if unicode_value is None:
            raise LogicError('No default value available for attribute %s' % (self.__tag,))
        value = self.__dataType(unicode_value)
        setattr(ctd_instance, self.__field, value)

class PyWXSB_enumeration_mixin (object):
    pass

class PyWXSB_complexTypeDefinition (object):
    def _setAttributesFromDOM (self, node):
        for au in self._Attributes:
            au.setFromDOM(self, node)
        return self

class PyWXSB_CTD_empty (PyWXSB_complexTypeDefinition):

    @classmethod
    def CreateFromDOM (cls, node):
        return cls()._setAttributesFromDOM(node)

class PyWXSB_CTD_simple (PyWXSB_complexTypeDefinition):
    __content = None
    def content (self):
        return self.__content

    def __init__ (self, *args, **kw):
        self.__content = self._TypeDefinition.Factory(*args, **kw)

    @classmethod
    def Factory (cls, *args, **kw):
        rv = cls(*args, **kw)
        return rv

    @classmethod
    def CreateFromDOM (cls, node):
        return cls(domutils.ExtractTextContent(node))._setAttributesFromDOM(node)

class PyWXSB_CTD_mixed (PyWXSB_complexTypeDefinition):
    pass

class PyWXSB_CTD_element (PyWXSB_complexTypeDefinition):
    pass

class PyWXSB_CTD_empty_mixin (object):
    pass
