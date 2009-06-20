# PyWXSB bindings for <not provided>
# Generated 2009-06-20 08:59:35.861047 by PyWXSB version UNSPECIFIED
import pyxb.binding
import pyxb.exceptions_
import pyxb.utils.domutils
import sys

# Import bindings for namespaces imported into schema


# Make sure there's a registered Namespace instance, and that it knows
# about this module.
Namespace = pyxb.namespace.CreateAbsentNamespace()
Namespace._setModule(sys.modules[__name__])
Namespace.configureCategories(['typeBinding', 'elementBinding'])

def CreateFromDocument (xml_text):
    """Parse the given XML and use the document element to create a Python instance."""
    dom = pyxb.utils.domutils.StringToDOM(xml_text)
    return CreateFromDOM(dom.documentElement)

def CreateFromDOM (node):
    """Create a Python instance from the given DOM node.
    The node tag must correspond to an element declaration in this module."""
    import xml.dom
    if node.nodeType == xml.dom.Node.DOCUMENT_NODE:
        node = node.documentElement
    return pyxb.binding.basis.element.AnyCreateFromDOM(node, Namespace)

# Complex type _CTD_ANON_1 with content type ELEMENT_ONLY
class _CTD_ANON_1 (pyxb.binding.basis.complexTypeDefinition):
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = None
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element simple uses Python identifier simple
    __simple = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(None, u'simple'), 'simple', '__CTD_ANON_1_simple', False)
    def simple (self):
        """Get the value of the simple element."""
        return self.__simple.value(self)
    def setSimple (self, new_value):
        """Set the value of the simple element.  Raises BadValueTypeException
        if the new value is not consistent with the element's type."""
        return self.__simple.set(self, new_value)
    
    # Element complex uses Python identifier complex
    __complex = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(None, u'complex'), 'complex', '__CTD_ANON_1_complex', False)
    def complex (self):
        """Get the value of the complex element."""
        return self.__complex.value(self)
    def setComplex (self, new_value):
        """Set the value of the complex element.  Raises BadValueTypeException
        if the new value is not consistent with the element's type."""
        return self.__complex.set(self, new_value)
    
    # Attribute attribute uses Python identifier attribute
    __attribute = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, u'attribute'), 'attribute', '__CTD_ANON_1_attribute', pyxb.binding.datatypes.integer)
    def attribute (self):
        """Get the attribute value for attribute."""
        return self.__attribute.value(self)
    def setAttribute (self, new_value):
        """Set the attribute value for attribute.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__attribute.set(self, new_value)

    _ElementMap = {
        __simple.name() : __simple,
        __complex.name() : __complex
    }
    _AttributeMap = {
        __attribute.name() : __attribute
    }



# Complex type _CTD_ANON_2 with content type SIMPLE
class _CTD_ANON_2 (pyxb.binding.basis.complexTypeDefinition):
    _TypeDefinition = pyxb.binding.datatypes.integer
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_SIMPLE
    _Abstract = False
    _ExpandedName = None
    # Base type is pyxb.binding.datatypes.integer
    
    # Attribute style uses Python identifier style
    __style = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, u'style'), 'style', '__CTD_ANON_2_style', pyxb.binding.datatypes.string)
    def style (self):
        """Get the attribute value for style."""
        return self.__style.value(self)
    def setStyle (self, new_value):
        """Set the attribute value for style.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__style.set(self, new_value)

    _ElementMap = {
        
    }
    _AttributeMap = {
        __style.name() : __style
    }



numbers = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, u'numbers'), _CTD_ANON_1)
Namespace.addCategoryObject('elementBinding', numbers.name().localName(), numbers)



_CTD_ANON_1._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, u'simple'), pyxb.binding.datatypes.integer, scope=_CTD_ANON_1))

_CTD_ANON_1._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, u'complex'), _CTD_ANON_2, scope=_CTD_ANON_1))
_CTD_ANON_1._ContentModel = pyxb.binding.content.ContentModel(state_map = {
      1 : pyxb.binding.content.ContentModelState(state=1, is_final=False, transitions=[
        pyxb.binding.content.ContentModelTransition(next_state=2, element_use=_CTD_ANON_1._UseForTag(pyxb.namespace.ExpandedName(None, u'simple'))),
    ])
    , 2 : pyxb.binding.content.ContentModelState(state=2, is_final=False, transitions=[
        pyxb.binding.content.ContentModelTransition(next_state=3, element_use=_CTD_ANON_1._UseForTag(pyxb.namespace.ExpandedName(None, u'complex'))),
    ])
    , 3 : pyxb.binding.content.ContentModelState(state=3, is_final=True, transitions=[
    ])
})
