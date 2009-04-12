import XMLSchema as xs
import domutils

class PyWXSB_element (object):
    __content = None
    
    def __init__ (self, *args, **kw):
        """Create a new element.

        If the element is a complex type with simple content, the
        value of the content is dereferenced once.
        """
        self.__content = self._TypeDefinition.Factory(*args, **kw)
        if issubclass(self._TypeDefinition, PyWXSB_CTD_simple):
            self.__content = self.content().content()

    def content (self):
        return self.__content

    def _content (self, content):
        self.__content = content
        return self
 
    @classmethod
    def CreateFromDOM (cls, node):
        return cls(domutils.ExtractTextContent(node))

class PyWXSB_enumeration_mixin (object):
    pass

class PyWXSB_complexTypeDefinition (object):
    __content = None
    def content (self):
        return self.__content

    def __init__ (self, *args, **kw):
        self.__content = self._TypeDefinition.Factory(*args, **kw)

class PyWXSB_CTD_empty (PyWXSB_complexTypeDefinition):
    pass

class PyWXSB_CTD_simple (PyWXSB_complexTypeDefinition):
    @classmethod
    def Factory (cls, *args, **kw):
        return cls(*args, **kw)

    @classmethod
    def CreateFromDOM (cls, node):
        # @todo handle attributes
        return cls(domutils.ExtractTextContent(node))

class PyWXSB_CTD_mixed (PyWXSB_complexTypeDefinition):
    pass

class PyWXSB_CTD_element (PyWXSB_complexTypeDefinition):
    pass

class PyWXSB_CTD_empty_mixin (object):
    pass
