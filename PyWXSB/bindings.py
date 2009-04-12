import domutils

class PyWXSB_element (object):
    __content = None
    
    def __init__ (self, *args, **kw):
        self.__content = self._TypeDefinition.Factory(*args, **kw)

    def content (self):
        return self.__content
 
    @classmethod
    def CreateFromDOM (cls, node):
        return cls(domutils.ExtractTextContent(node))

class PyWXSB_enumeration_mixin (object):
    pass

class PyWXSB_complexTypeDefinition (object):
    pass

class PyWXSB_CTD_empty (PyWXSB_complexTypeDefinition):
    pass

class PyWXSB_CTD_simple (PyWXSB_complexTypeDefinition):
    __content = None
    def content (self):
        return self.__content

    def __init__ (self, *args, **kw):
        self.__content = self._TypeDefinition.Factory(*args, **kw)

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
