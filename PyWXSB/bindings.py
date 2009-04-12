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

