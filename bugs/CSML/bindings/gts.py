# PyWXSB bindings for <not provided>
# Generated 2009-06-25 05:42:38.375226 by PyWXSB version UNSPECIFIED
import pyxb.binding
import pyxb.exceptions_
import pyxb.utils.domutils
import sys

# Import bindings for namespaces imported into schema


# Make sure there's a registered Namespace instance, and that it knows
# about this module.
Namespace = pyxb.namespace.NamespaceForURI(u'http://www.isotc211.org/2005/gts', create_if_missing=True)
Namespace._setModule(sys.modules[__name__])
Namespace.configureCategories(['typeBinding', 'elementBinding'])

def CreateFromDocument (xml_text):
    """Parse the given XML and use the document element to create a Python instance."""
    dom = pyxb.utils.domutils.StringToDOM(xml_text)
    return CreateFromDOM(dom.documentElement)

def CreateFromDOM (node):
    """Create a Python instance from the given DOM node.
    The node tag must correspond to an element declaration in this module."""
    return pyxb.binding.basis.element.AnyCreateFromDOM(node, Namespace)

# Complex type TM_PeriodDuration_PropertyType with content type ELEMENT_ONLY
class TM_PeriodDuration_PropertyType (pyxb.binding.basis.complexTypeDefinition):
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, u'TM_PeriodDuration_PropertyType')
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.isotc211.org/2005/gts}TM_PeriodDuration uses Python identifier TM_PeriodDuration
    __TM_PeriodDuration = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(Namespace, u'TM_PeriodDuration'), 'TM_PeriodDuration', '__TM_PeriodDuration_PropertyType_httpwww_isotc211_org2005gtsTM_PeriodDuration', False)
    def TM_PeriodDuration (self):
        """Get the value of the {http://www.isotc211.org/2005/gts}TM_PeriodDuration element."""
        return self.__TM_PeriodDuration.value(self)
    def setTM_PeriodDuration (self, new_value):
        """Set the value of the {http://www.isotc211.org/2005/gts}TM_PeriodDuration element.  Raises BadValueTypeException
        if the new value is not consistent with the element's type."""
        return self.__TM_PeriodDuration.set(self, new_value)
    
    # Attribute {http://www.isotc211.org/2005/gco}nilReason uses Python identifier nilReason
    __nilReason = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_isotc211_org2005gco.Namespace, u'nilReason'), 'nilReason', '__TM_PeriodDuration_PropertyType_httpwww_isotc211_org2005gconilReason', MODULEhttpwww_opengis_netgml.UNBOUNDhttpwww_opengis_netgmlNilReasonType)
    def nilReason (self):
        """Get the attribute value for {http://www.isotc211.org/2005/gco}nilReason."""
        return self.__nilReason.value(self)
    def setNilReason (self, new_value):
        """Set the attribute value for {http://www.isotc211.org/2005/gco}nilReason.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__nilReason.set(self, new_value)

    _ElementMap = {
        __TM_PeriodDuration.name() : __TM_PeriodDuration
    }
    _AttributeMap = {
        __nilReason.name() : __nilReason
    }
Namespace.addCategoryObject('typeBinding', u'TM_PeriodDuration_PropertyType', TM_PeriodDuration_PropertyType)


# Complex type TM_Primitive_PropertyType with content type ELEMENT_ONLY
class TM_Primitive_PropertyType (pyxb.binding.basis.complexTypeDefinition):
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, u'TM_Primitive_PropertyType')
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.opengis.net/gml}AbstractTimePrimitive uses Python identifier AbstractTimePrimitive
    __AbstractTimePrimitive = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(MODULEhttpwww_opengis_netgml.Namespace, u'AbstractTimePrimitive'), 'AbstractTimePrimitive', '__TM_Primitive_PropertyType_httpwww_opengis_netgmlAbstractTimePrimitive', False)
    def AbstractTimePrimitive (self):
        """Get the value of the {http://www.opengis.net/gml}AbstractTimePrimitive element."""
        return self.__AbstractTimePrimitive.value(self)
    def setAbstractTimePrimitive (self, new_value):
        """Set the value of the {http://www.opengis.net/gml}AbstractTimePrimitive element.  Raises BadValueTypeException
        if the new value is not consistent with the element's type."""
        return self.__AbstractTimePrimitive.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}href uses Python identifier href
    __href = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'href'), 'href', '__TM_Primitive_PropertyType_httpwww_w3_org1999xlinkhref', pyxb.binding.datatypes.anyURI)
    def href (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}href."""
        return self.__href.value(self)
    def setHref (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}href.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__href.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'type'), 'type', '__TM_Primitive_PropertyType_httpwww_w3_org1999xlinktype', pyxb.binding.datatypes.string, fixed=True, unicode_default=u'simple')
    def type (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}type."""
        return self.__type.value(self)
    def setType (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}type.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__type.set(self, new_value)
    
    # Attribute {http://www.isotc211.org/2005/gco}nilReason uses Python identifier nilReason
    __nilReason = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_isotc211_org2005gco.Namespace, u'nilReason'), 'nilReason', '__TM_Primitive_PropertyType_httpwww_isotc211_org2005gconilReason', MODULEhttpwww_opengis_netgml.UNBOUNDhttpwww_opengis_netgmlNilReasonType_)
    def nilReason (self):
        """Get the attribute value for {http://www.isotc211.org/2005/gco}nilReason."""
        return self.__nilReason.value(self)
    def setNilReason (self, new_value):
        """Set the attribute value for {http://www.isotc211.org/2005/gco}nilReason.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__nilReason.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}arcrole uses Python identifier arcrole
    __arcrole = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'arcrole'), 'arcrole', '__TM_Primitive_PropertyType_httpwww_w3_org1999xlinkarcrole', pyxb.binding.datatypes.anyURI)
    def arcrole (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}arcrole."""
        return self.__arcrole.value(self)
    def setArcrole (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}arcrole.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__arcrole.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'title'), 'title', '__TM_Primitive_PropertyType_httpwww_w3_org1999xlinktitle', pyxb.binding.datatypes.string)
    def title (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}title."""
        return self.__title.value(self)
    def setTitle (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}title.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__title.set(self, new_value)
    
    # Attribute uuidref uses Python identifier uuidref
    __uuidref = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, u'uuidref'), 'uuidref', '__TM_Primitive_PropertyType_uuidref', pyxb.binding.datatypes.string)
    def uuidref (self):
        """Get the attribute value for uuidref."""
        return self.__uuidref.value(self)
    def setUuidref (self, new_value):
        """Set the attribute value for uuidref.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__uuidref.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}show uses Python identifier show
    __show = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'show'), 'show', '__TM_Primitive_PropertyType_httpwww_w3_org1999xlinkshow', MODULEhttpwww_w3_org1999xlink.UNBOUNDNone)
    def show (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}show."""
        return self.__show.value(self)
    def setShow (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}show.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__show.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'role'), 'role', '__TM_Primitive_PropertyType_httpwww_w3_org1999xlinkrole', pyxb.binding.datatypes.anyURI)
    def role (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}role."""
        return self.__role.value(self)
    def setRole (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}role.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__role.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}actuate uses Python identifier actuate
    __actuate = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'actuate'), 'actuate', '__TM_Primitive_PropertyType_httpwww_w3_org1999xlinkactuate', MODULEhttpwww_w3_org1999xlink.UNBOUNDNone_)
    def actuate (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}actuate."""
        return self.__actuate.value(self)
    def setActuate (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}actuate.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__actuate.set(self, new_value)

    _ElementMap = {
        __AbstractTimePrimitive.name() : __AbstractTimePrimitive
    }
    _AttributeMap = {
        __href.name() : __href,
        __type.name() : __type,
        __nilReason.name() : __nilReason,
        __arcrole.name() : __arcrole,
        __title.name() : __title,
        __uuidref.name() : __uuidref,
        __show.name() : __show,
        __role.name() : __role,
        __actuate.name() : __actuate
    }
Namespace.addCategoryObject('typeBinding', u'TM_Primitive_PropertyType', TM_Primitive_PropertyType)


TM_PeriodDuration = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, u'TM_PeriodDuration'), pyxb.binding.datatypes.duration)
Namespace.addCategoryObject('elementBinding', TM_PeriodDuration.name().localName(), TM_PeriodDuration)



TM_PeriodDuration_PropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, u'TM_PeriodDuration'), pyxb.binding.datatypes.duration, scope=TM_PeriodDuration_PropertyType))
TM_PeriodDuration_PropertyType._ContentModel = pyxb.binding.content.ContentModel(state_map = {
      1 : pyxb.binding.content.ContentModelState(state=1, is_final=True, transitions=[
        pyxb.binding.content.ContentModelTransition(next_state=2, element_use=TM_PeriodDuration_PropertyType._UseForTag(pyxb.namespace.ExpandedName(Namespace, u'TM_PeriodDuration'))),
    ])
    , 2 : pyxb.binding.content.ContentModelState(state=2, is_final=True, transitions=[
    ])
})



TM_Primitive_PropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(MODULEhttpwww_opengis_netgml.Namespace, u'AbstractTimePrimitive'), MODULEhttpwww_opengis_netgml.UNBOUNDhttpwww_opengis_netgmlAbstractTimePrimitiveType, abstract=pyxb.binding.datatypes.boolean(1), scope=TM_Primitive_PropertyType))
TM_Primitive_PropertyType._ContentModel = pyxb.binding.content.ContentModel(state_map = {
      1 : pyxb.binding.content.ContentModelState(state=1, is_final=True, transitions=[
        pyxb.binding.content.ContentModelTransition(next_state=2, element_use=TM_Primitive_PropertyType._UseForTag(pyxb.namespace.ExpandedName(MODULEhttpwww_opengis_netgml.Namespace, u'AbstractTimePrimitive'))),
    ])
    , 2 : pyxb.binding.content.ContentModelState(state=2, is_final=True, transitions=[
    ])
})
