# PyWXSB bindings for <not provided>
# Generated 2009-06-24 07:13:32.741750 by PyWXSB version UNSPECIFIED
import pyxb.binding
import pyxb.exceptions_
import pyxb.utils.domutils
import sys

# Import bindings for namespaces imported into schema


# Make sure there's a registered Namespace instance, and that it knows
# about this module.
Namespace = pyxb.namespace.NamespaceForURI(u'http://www.isotc211.org/2005/gss', create_if_missing=True)
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

# Complex type GM_Object_PropertyType with content type ELEMENT_ONLY
class GM_Object_PropertyType (pyxb.binding.basis.complexTypeDefinition):
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, u'GM_Object_PropertyType')
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.opengis.net/gml}AbstractGeometry uses Python identifier AbstractGeometry
    __AbstractGeometry = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(MODULEhttpwww_opengis_netgml.Namespace, u'AbstractGeometry'), 'AbstractGeometry', '__GM_Object_PropertyType_httpwww_opengis_netgmlAbstractGeometry', False)
    def AbstractGeometry (self):
        """Get the value of the {http://www.opengis.net/gml}AbstractGeometry element."""
        return self.__AbstractGeometry.value(self)
    def setAbstractGeometry (self, new_value):
        """Set the value of the {http://www.opengis.net/gml}AbstractGeometry element.  Raises BadValueTypeException
        if the new value is not consistent with the element's type."""
        return self.__AbstractGeometry.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'role'), 'role', '__GM_Object_PropertyType_httpwww_w3_org1999xlinkrole', pyxb.binding.datatypes.anyURI)
    def role (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}role."""
        return self.__role.value(self)
    def setRole (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}role.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__role.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'type'), 'type', '__GM_Object_PropertyType_httpwww_w3_org1999xlinktype', pyxb.binding.datatypes.string, fixed=True, unicode_default=u'simple')
    def type (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}type."""
        return self.__type.value(self)
    def setType (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}type.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__type.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}href uses Python identifier href
    __href = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'href'), 'href', '__GM_Object_PropertyType_httpwww_w3_org1999xlinkhref', pyxb.binding.datatypes.anyURI)
    def href (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}href."""
        return self.__href.value(self)
    def setHref (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}href.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__href.set(self, new_value)
    
    # Attribute {http://www.isotc211.org/2005/gco}nilReason uses Python identifier nilReason
    __nilReason = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_isotc211_org2005gco.Namespace, u'nilReason'), 'nilReason', '__GM_Object_PropertyType_httpwww_isotc211_org2005gconilReason', MODULEhttpwww_opengis_netgml.UNBOUNDhttpwww_opengis_netgmlNilReasonType)
    def nilReason (self):
        """Get the attribute value for {http://www.isotc211.org/2005/gco}nilReason."""
        return self.__nilReason.value(self)
    def setNilReason (self, new_value):
        """Set the attribute value for {http://www.isotc211.org/2005/gco}nilReason.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__nilReason.set(self, new_value)
    
    # Attribute uuidref uses Python identifier uuidref
    __uuidref = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, u'uuidref'), 'uuidref', '__GM_Object_PropertyType_uuidref', pyxb.binding.datatypes.string)
    def uuidref (self):
        """Get the attribute value for uuidref."""
        return self.__uuidref.value(self)
    def setUuidref (self, new_value):
        """Set the attribute value for uuidref.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__uuidref.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'title'), 'title', '__GM_Object_PropertyType_httpwww_w3_org1999xlinktitle', pyxb.binding.datatypes.string)
    def title (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}title."""
        return self.__title.value(self)
    def setTitle (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}title.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__title.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}actuate uses Python identifier actuate
    __actuate = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'actuate'), 'actuate', '__GM_Object_PropertyType_httpwww_w3_org1999xlinkactuate', MODULEhttpwww_w3_org1999xlink.UNBOUNDNone)
    def actuate (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}actuate."""
        return self.__actuate.value(self)
    def setActuate (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}actuate.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__actuate.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}arcrole uses Python identifier arcrole
    __arcrole = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'arcrole'), 'arcrole', '__GM_Object_PropertyType_httpwww_w3_org1999xlinkarcrole', pyxb.binding.datatypes.anyURI)
    def arcrole (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}arcrole."""
        return self.__arcrole.value(self)
    def setArcrole (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}arcrole.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__arcrole.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}show uses Python identifier show
    __show = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'show'), 'show', '__GM_Object_PropertyType_httpwww_w3_org1999xlinkshow', MODULEhttpwww_w3_org1999xlink.UNBOUNDNone_)
    def show (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}show."""
        return self.__show.value(self)
    def setShow (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}show.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__show.set(self, new_value)

    _ElementMap = {
        __AbstractGeometry.name() : __AbstractGeometry
    }
    _AttributeMap = {
        __role.name() : __role,
        __type.name() : __type,
        __href.name() : __href,
        __nilReason.name() : __nilReason,
        __uuidref.name() : __uuidref,
        __title.name() : __title,
        __actuate.name() : __actuate,
        __arcrole.name() : __arcrole,
        __show.name() : __show
    }
Namespace.addCategoryObject('typeBinding', u'GM_Object_PropertyType', GM_Object_PropertyType)


# Complex type GM_Point_PropertyType with content type ELEMENT_ONLY
class GM_Point_PropertyType (pyxb.binding.basis.complexTypeDefinition):
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = pyxb.namespace.ExpandedName(Namespace, u'GM_Point_PropertyType')
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element {http://www.opengis.net/gml}Point uses Python identifier Point
    __Point = pyxb.binding.content.ElementUse(pyxb.namespace.ExpandedName(MODULEhttpwww_opengis_netgml.Namespace, u'Point'), 'Point', '__GM_Point_PropertyType_httpwww_opengis_netgmlPoint', False)
    def Point (self):
        """Get the value of the {http://www.opengis.net/gml}Point element."""
        return self.__Point.value(self)
    def setPoint (self, new_value):
        """Set the value of the {http://www.opengis.net/gml}Point element.  Raises BadValueTypeException
        if the new value is not consistent with the element's type."""
        return self.__Point.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}type uses Python identifier type
    __type = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'type'), 'type', '__GM_Point_PropertyType_httpwww_w3_org1999xlinktype', pyxb.binding.datatypes.string, fixed=True, unicode_default=u'simple')
    def type (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}type."""
        return self.__type.value(self)
    def setType (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}type.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__type.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}show uses Python identifier show
    __show = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'show'), 'show', '__GM_Point_PropertyType_httpwww_w3_org1999xlinkshow', MODULEhttpwww_w3_org1999xlink.UNBOUNDNone_2)
    def show (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}show."""
        return self.__show.value(self)
    def setShow (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}show.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__show.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}role uses Python identifier role
    __role = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'role'), 'role', '__GM_Point_PropertyType_httpwww_w3_org1999xlinkrole', pyxb.binding.datatypes.anyURI)
    def role (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}role."""
        return self.__role.value(self)
    def setRole (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}role.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__role.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}href uses Python identifier href
    __href = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'href'), 'href', '__GM_Point_PropertyType_httpwww_w3_org1999xlinkhref', pyxb.binding.datatypes.anyURI)
    def href (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}href."""
        return self.__href.value(self)
    def setHref (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}href.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__href.set(self, new_value)
    
    # Attribute uuidref uses Python identifier uuidref
    __uuidref = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(None, u'uuidref'), 'uuidref', '__GM_Point_PropertyType_uuidref', pyxb.binding.datatypes.string)
    def uuidref (self):
        """Get the attribute value for uuidref."""
        return self.__uuidref.value(self)
    def setUuidref (self, new_value):
        """Set the attribute value for uuidref.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__uuidref.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}arcrole uses Python identifier arcrole
    __arcrole = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'arcrole'), 'arcrole', '__GM_Point_PropertyType_httpwww_w3_org1999xlinkarcrole', pyxb.binding.datatypes.anyURI)
    def arcrole (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}arcrole."""
        return self.__arcrole.value(self)
    def setArcrole (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}arcrole.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__arcrole.set(self, new_value)
    
    # Attribute {http://www.isotc211.org/2005/gco}nilReason uses Python identifier nilReason
    __nilReason = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_isotc211_org2005gco.Namespace, u'nilReason'), 'nilReason', '__GM_Point_PropertyType_httpwww_isotc211_org2005gconilReason', MODULEhttpwww_opengis_netgml.UNBOUNDhttpwww_opengis_netgmlNilReasonType_)
    def nilReason (self):
        """Get the attribute value for {http://www.isotc211.org/2005/gco}nilReason."""
        return self.__nilReason.value(self)
    def setNilReason (self, new_value):
        """Set the attribute value for {http://www.isotc211.org/2005/gco}nilReason.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__nilReason.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}actuate uses Python identifier actuate
    __actuate = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'actuate'), 'actuate', '__GM_Point_PropertyType_httpwww_w3_org1999xlinkactuate', MODULEhttpwww_w3_org1999xlink.UNBOUNDNone_3)
    def actuate (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}actuate."""
        return self.__actuate.value(self)
    def setActuate (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}actuate.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__actuate.set(self, new_value)
    
    # Attribute {http://www.w3.org/1999/xlink}title uses Python identifier title
    __title = pyxb.binding.content.AttributeUse(pyxb.namespace.ExpandedName(MODULEhttpwww_w3_org1999xlink.Namespace, u'title'), 'title', '__GM_Point_PropertyType_httpwww_w3_org1999xlinktitle', pyxb.binding.datatypes.string)
    def title (self):
        """Get the attribute value for {http://www.w3.org/1999/xlink}title."""
        return self.__title.value(self)
    def setTitle (self, new_value):
        """Set the attribute value for {http://www.w3.org/1999/xlink}title.  Raises BadValueTypeException
        if the new value is not consistent with the attribute's type."""
        return self.__title.set(self, new_value)

    _ElementMap = {
        __Point.name() : __Point
    }
    _AttributeMap = {
        __type.name() : __type,
        __show.name() : __show,
        __role.name() : __role,
        __href.name() : __href,
        __uuidref.name() : __uuidref,
        __arcrole.name() : __arcrole,
        __nilReason.name() : __nilReason,
        __actuate.name() : __actuate,
        __title.name() : __title
    }
Namespace.addCategoryObject('typeBinding', u'GM_Point_PropertyType', GM_Point_PropertyType)




GM_Object_PropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(MODULEhttpwww_opengis_netgml.Namespace, u'AbstractGeometry'), MODULEhttpwww_opengis_netgml.UNBOUNDhttpwww_opengis_netgmlAbstractGeometryType, abstract=pyxb.binding.datatypes.boolean(1), scope=GM_Object_PropertyType))
GM_Object_PropertyType._ContentModel = pyxb.binding.content.ContentModel(state_map = {
      1 : pyxb.binding.content.ContentModelState(state=1, is_final=True, transitions=[
        pyxb.binding.content.ContentModelTransition(next_state=2, element_use=GM_Object_PropertyType._UseForTag(pyxb.namespace.ExpandedName(MODULEhttpwww_opengis_netgml.Namespace, u'AbstractGeometry'))),
    ])
    , 2 : pyxb.binding.content.ContentModelState(state=2, is_final=True, transitions=[
    ])
})



GM_Point_PropertyType._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(MODULEhttpwww_opengis_netgml.Namespace, u'Point'), MODULEhttpwww_opengis_netgml.UNBOUNDhttpwww_opengis_netgmlPointType, scope=GM_Point_PropertyType))
GM_Point_PropertyType._ContentModel = pyxb.binding.content.ContentModel(state_map = {
      1 : pyxb.binding.content.ContentModelState(state=1, is_final=True, transitions=[
        pyxb.binding.content.ContentModelTransition(next_state=2, element_use=GM_Point_PropertyType._UseForTag(pyxb.namespace.ExpandedName(MODULEhttpwww_opengis_netgml.Namespace, u'Point'))),
    ])
    , 2 : pyxb.binding.content.ContentModelState(state=2, is_final=True, transitions=[
    ])
})
