# ./content.py
# PyXB bindings for NamespaceModule
# NSM:e92452c8d3e28a9e27abfc9994d2007779e7f4c9
# Generated 2009-08-23 12:13:53.268284 by PyXB version 0.7.1
import pyxb
import pyxb.binding
import pyxb.binding.saxer
import StringIO
import pyxb.utils.utility
import pyxb.utils.domutils
import sys

# Unique identifier for bindings created at the same time
_GenerationUID = pyxb.utils.utility.UniqueIdentifier('urn:uuid:18cb9c3c-9019-11de-aa32-000c292f797c')

# Import bindings for namespaces imported into schema
import pyxb.binding.datatypes

Namespace = pyxb.namespace.CreateAbsentNamespace()
Namespace.configureCategories(['typeBinding', 'elementBinding'])
ModuleRecord = Namespace.lookupModuleRecordByUID(_GenerationUID, create_if_missing=True)
ModuleRecord._setModule(sys.modules[__name__])

def CreateFromDocument (xml_text, default_namespace=None):
    """Parse the given XML and use the document element to create a Python instance."""
    if pyxb.XMLStyle_saxer != pyxb._XMLStyle:
        dom = pyxb.utils.domutils.StringToDOM(xml_text)
        return CreateFromDOM(dom.documentElement)
    saxer = pyxb.binding.saxer.make_parser(fallback_namespace=Namespace.fallbackNamespace())
    handler = saxer.getContentHandler()
    saxer.parse(StringIO.StringIO(xml_text))
    instance = handler.rootObject()
    return instance

def CreateFromDOM (node, default_namespace=None):
    """Create a Python instance from the given DOM node.
    The node tag must correspond to an element declaration in this module.

    @deprecated: Forcing use of DOM interface is unnecessary; use L{CreateFromDocument}."""
    if default_namespace is None:
        default_namespace = Namespace.fallbackNamespace()
    return pyxb.binding.basis.element.AnyCreateFromDOM(node, _fallback_namespace=default_namespace)


# Complex type CTD_ANON_1 with content type ELEMENT_ONLY
class CTD_ANON_1 (pyxb.binding.basis.complexTypeDefinition):
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = None
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element simple uses Python identifier simple
    __simple = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(None, u'simple'), 'simple', '__AbsentNamespace0_CTD_ANON_1_simple', False)

    
    simple = property(__simple.value, __simple.set, None, None)

    
    # Element complex uses Python identifier complex
    __complex = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(None, u'complex'), 'complex', '__AbsentNamespace0_CTD_ANON_1_complex', False)

    
    complex = property(__complex.value, __complex.set, None, None)

    
    # Attribute attribute uses Python identifier attribute
    __attribute = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, u'attribute'), 'attribute', '__AbsentNamespace0_CTD_ANON_1_attribute', pyxb.binding.datatypes.integer)
    
    attribute = property(__attribute.value, __attribute.set, None, None)


    _ElementMap = {
        __simple.name() : __simple,
        __complex.name() : __complex
    }
    _AttributeMap = {
        __attribute.name() : __attribute
    }



# Complex type CTD_ANON_2 with content type SIMPLE
class CTD_ANON_2 (pyxb.binding.basis.complexTypeDefinition):
    _TypeDefinition = pyxb.binding.datatypes.integer
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_SIMPLE
    _Abstract = False
    _ExpandedName = None
    # Base type is pyxb.binding.datatypes.integer
    
    # Attribute style uses Python identifier style
    __style = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, u'style'), 'style', '__AbsentNamespace0_CTD_ANON_2_style', pyxb.binding.datatypes.string)
    
    style = property(__style.value, __style.set, None, None)


    _ElementMap = {
        
    }
    _AttributeMap = {
        __style.name() : __style
    }



numbers = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, u'numbers'), CTD_ANON_1)
Namespace.addCategoryObject('elementBinding', numbers.name().localName(), numbers)



CTD_ANON_1._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, u'simple'), pyxb.binding.datatypes.integer, scope=CTD_ANON_1))

CTD_ANON_1._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, u'complex'), CTD_ANON_2, scope=CTD_ANON_1))
CTD_ANON_1._ContentModel = pyxb.binding.content.ContentModel(state_map = {
      1 : pyxb.binding.content.ContentModelState(state=1, is_final=False, transitions=[
        pyxb.binding.content.ContentModelTransition(next_state=2, element_use=CTD_ANON_1._UseForTag(pyxb.namespace.ExpandedName(None, u'simple'))),
    ])
    , 2 : pyxb.binding.content.ContentModelState(state=2, is_final=False, transitions=[
        pyxb.binding.content.ContentModelTransition(next_state=3, element_use=CTD_ANON_1._UseForTag(pyxb.namespace.ExpandedName(None, u'complex'))),
    ])
    , 3 : pyxb.binding.content.ContentModelState(state=3, is_final=True, transitions=[
    ])
})
