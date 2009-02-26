from PyWXSB.exceptions_ import *
from xml.dom import Node
import types
import datatypes
import PyWXSB.domutils as domutils

class Facet (object):
    _Name = None
    @classmethod
    def Name (self): return self._Name

    __baseTypeDefinition = None
    def baseTypeDefinition (self):
        """The SimpleTypeDefinition component restricted by this facet.

        Note: this is NOT the STD to which the facet belongs."""
        return self.__baseTypeDefinition

    __ownerTypeDefinition = None
    def ownerTypeDefinition (self):
        """The SimpleTypeDefinition component to which this facet belongs."""
        return self.__ownerTypeDefinition

    # @todo make this valueTypeDefinition
    __valueTypeDefinition = None
    def valueTypeDefinition (self):
        """The SimpleTypeDefinition component that defines the value
        space of the facet itself.  If None, defaults to
        baseTypeDefinition(), as appropriate for
        {min,max}{inclusive,exclusive}."""
        if self.__valueTypeDefinition is None:
            self.__valueTypeDefinition = self.baseTypeDefinition()
        return self.__valueTypeDefinition

    # valueDataType is a Python type, probably a subclassed built-in,
    # that is used for the value of this facet.
    __valueDatatype = None
    def valueDatatype (self):
        vtd = self.valueTypeDefinition()
        if vtd is not None:
            return vtd.pythonSupport()
        raise LogicError("No value type definition available for facet %s" % (self.Name(),))

    __value = None
    def _value (self, v): self.__value = v
    def value (self): return self.__value

    __annotation = None
    def annotation (self): return self.__annotation

    def __init__ (self, **kw):
        super(Facet, self).__init__()
        # Can't create base class instances
        assert Facet != self.__class__
        self.setFromKeywords(_reset=True, **kw)

    def _setFromKeywords_vb (self, **kw):
        self.__baseTypeDefinition = kw.get('base_type_definition', None)
        self.__ownerTypeDefinition = kw.get('owner_type_definition', None)
        self.__valueTypeDefinition = kw.get('value_type_definition', None)
        super_fn = getattr(super(Facet, self), '_setFromKeywords_vb', lambda *a,**kw: self)
        return super_fn(**kw)
    
    def setFromKeywords (self, **kw):
        return self._setFromKeywords_vb(**kw)

    def extendFromKeywords (self, **kw):
        raise NotImplementedError('%s: Class does not implement extendFromKeywords.' % (self.__class__.__name__,))

    @classmethod
    def ClassForFacet (cls, name):
        assert cls != Facet
        if 0 <= name.find(':'):
            name = name.split(':', 1)[1]
        if not name in cls._Facets:
            raise LogicError('Unrecognized facet name %s: expect %s' % (name, ','.join(cls._Facets)))
        facet_class = globals().get('%s_%s' % (cls._FacetPrefix, name), None)
        assert facet_class is not None
        return facet_class

    def _valueString (self):
        if self.valueDatatype() is not None:
            try:
                self.valueDatatype().XsdToString(self.value())
            except Exception, e:
                print 'Stringize face %s produced %s' % (self.Name(), e)
                raise
        return str(self.value())
    
    def __str__ (self):
        rv = []
        rv.append('%s="%s"' % (self.Name(), self._valueString()))
        if isinstance(self, _Fixed_mixin) and self.fixed():
            rv.append('[fixed]')
        return ''.join(rv)

class ConstrainingFacet (Facet):
    _Facets = [ 'length', 'minLength', 'maxLength', 'pattern', 'enumeration',
                'whiteSpace', 'maxInclusive', 'maxExclusive',
                'minExclusive', 'minInclusive', 'totalDigits', 'fractionDigits' ]
    _FacetPrefix = 'CF'
    
    __superFacet = None
    def superFacet (self):
        """Return the constraining facet instance from the base type, if any.

        For example, if this is a CF_length instance, the super-facet
        is a CF_length instance in the base type definition, or None
        if the neither base type definition nor its ancesters
        constrains CF_length.
        """
        return self.__superFacet

    def __init__ (self, **kw):
        super(ConstrainingFacet, self).__init__(**kw)
        self.__superFacet = kw.get('super_facet', None)

    def _validateConstraint_ov (self, string_value, value):
        pass

    def validateConstraint (self, string_value, value):
        if self.superFacet() is not None:
            self.superFacet().validateConstraint(string_value, value)
        self._validateConstraint_ov(string_value, value)

    def __setFromKeywords(self, **kw):
        kwv = kw.get('value', None)
        if kwv is not None:
            if not isinstance(kwv, self.valueDatatype()):
                kwv = self.valueDatatype()(kwv)
            self._value(kwv)

    def _setFromKeywords_vb (self, **kw):
        self.__setFromKeywords(**kw)
        super_fn = getattr(super(ConstrainingFacet, self), '_setFromKeywords_vb', lambda *a,**kw: self)
        return super_fn(**kw)
        
    def _setValueFromDOM (self, wxs, node):
        self.__setFromKeywords(value=domutils.NodeAttribute(node, wxs, 'value'))
        
    def updateFromDOM (self, wxs, node):
        try:
            super(ConstrainingFacet, self).updateFromDOM(wxs, node)
        except AttributeError, e:
            pass
        assert node.nodeName in wxs.xsQualifiedNames(self.Name())
        self._setValueFromDOM(wxs, node)
        # @todo
        self.__annotation = None
        return self

class _Fixed_mixin (object):
    """Mix-in to a constraining facet that adds support for the 'fixed' property."""
    __fixed = None
    def fixed (self): return self.__fixed

    def __setFromKeywords (self, **kw):
        if '_reset' in kw:
            self.__fixed = None
        kwv = kw.get('fixed', None)
        if kwv is not None:
            self.__fixed = datatypes.boolean.StringToPython(kwv)
        
    def _setFromKeywords_vb (self, **kw):
        print 'Fixed_mixin sFK'
        self.__setFromKeywords(**kw)
        super_fn = getattr(super(_Fixed_mixin, self), '_setFromKeywords_vb', lambda *a,**kw: self)
        return super_fn(**kw)
    
    def updateFromDOM (self, wxs, node):
        super(_Fixed_mixin, self).updateFromDOM(wxs, node)
        self.__setFromKeywords(fixed=domutils.NodeAttribute(node, wxs, 'fixed'))

class _CollectionFacet_Item (tuple):
    def __init__ (self, value=None, annotation=None, description=None):
        self.value = value
        self.annotation = annotation
        self.description = description
        super(_CollectionFacet_Item, self).__init__(self, value, annotation, description)

class _CollectionFacet_mixin (object):
    """Mix-in to handle facets whose values are collections, not scalars.

    For example, the enumeration and pattern facets maintain a list of
    enumeration values and patterns, respectively, as their value
    space."""

    __items = None

    def _setFromKeywords_vb (self, **kw):
        print 'CF_mixin sFK'
        if '_reset' in kw:
            self.__items = []
        if 'value' in kw:
            del kw['value']
        super_fn = getattr(super(_CollectionFacet_mixin, self), '_setFromKeywords_vb', lambda *a,**kw: self)
        return super_fn(**kw)

    def extendFromKeywords (self, **kw):
        self.__items.append(_CollectionFacet_Item(**kw))

    def items (self): return self.__items

    def values (self):
        for item in self.items():
            yield item.value
            
class CF_length (ConstrainingFacet, _Fixed_mixin):
    _Name = 'length'
    def __init__ (self, **kw):
        super(CF_length, self).__init__(value_type_definition=datatypes.nonNegativeInteger.SimpleTypeDefinition(), **kw)

class CF_minLength (ConstrainingFacet, _Fixed_mixin):
    _Name = 'minLength'
    def __init__ (self, **kw):
        super(CF_minLength, self).__init__(value_type_definition=datatypes.nonNegativeInteger.SimpleTypeDefinition(), **kw)

class CF_maxLength (ConstrainingFacet, _Fixed_mixin):
    _Name = 'maxLength'
    def __init__ (self, **kw):
        super(CF_maxLength, self).__init__(value_type_definition=datatypes.nonNegativeInteger.SimpleTypeDefinition(), **kw)

class _PatternElement:
    pattern = None
    annotation = None
    def __init__ (self, pattern=None, annotation=None):
        self.pattern = pattern
        self.annotation = annotation

class CF_pattern (ConstrainingFacet, _CollectionFacet_mixin):
    _Name = 'pattern'

    __patternElements = None
    def patternElements (self): return self.__patternElements

    def __init__ (self, **kw):
        super(CF_pattern, self).__init__(**kw)
        self.__patternElements = []

    def _setValueFromDOM (self, wxs, node):
        self.__pattern = node.getAttribute('value')

    def updateFromDOM (self, wxs, node):
        super(CF_pattern, self).updateFromDOM(wxs, node)
        self.__patternElements.append(_PatternElement(self.__pattern, domutils.LocateUniqueChild(node, wxs, 'annotation')))

    def _valueString (self):
        return '(%s)' % (','.join([ str(_x.pattern) for _x in self.__patternElements ]),)

class _EnumerationElement:
    tag = None
    value = None
    description = None
    annotation = None
    __bindingPrefix = None

    def bindingPrefix (self): return self.__bindingPrefix
    
    def __init__ (self, tag=None, value=None, description=None, annotation=None, binding_prefix=None):
        self.tag = tag
        self.value = value
        self.description = description
        if (self.description is None) and (self.annotation is not None):
            self.description = str(self.annotation)
        self.__bindingPrefix = binding_prefix

class CF_enumeration (ConstrainingFacet, _CollectionFacet_mixin):
    _Name = 'enumeration'

    __enumerationElements = None
    def enumerationElements (self): return self.__enumerationElements

    __enumPrefix = 'EV_'

    def __init__ (self, **kw):
        super(CF_enumeration, self).__init__(**kw)
        self.__enumerationElements = []

    def _setValueFromDOM (self, wxs, node):
        self.__tag = node.getAttribute('value')

    def updateFromDOM (self, wxs, node):
        super(CF_enumeration, self).updateFromDOM(wxs, node)
        self.__enumerationElements.append(_EnumerationElement(tag=self.__tag,
                                                              annotation=domutils.LocateUniqueChild(node, wxs, 'annotation'))) 

    def addEnumeration (self, **kw):
        self.__enumerationElements.append(_EnumerationElement(**kw))

    def _valueString (self):
        return '(%s)' % (','.join([ str(_x.tag) for _x in self.__enumerationElements ]),)

    def enumPrefix (self, enum_prefix=None):
        if enum_prefix is not None:
            self.__enumPrefix = enum_prefix
        return self.__enumPrefix

class CF_whiteSpace (ConstrainingFacet, _Fixed_mixin):
    _LegalValues = ( 'preserve', 'replace', 'collapse' )
    _Name = 'whiteSpace'
    # @todo correct value type definition

class CF_maxInclusive (ConstrainingFacet, _Fixed_mixin):
    _Name = 'maxInclusive'

class CF_maxExclusive (ConstrainingFacet, _Fixed_mixin):
    _Name = 'maxExclusive'

class CF_minExclusive (ConstrainingFacet, _Fixed_mixin):
    _Name = 'minExclusive'

class CF_minInclusive (ConstrainingFacet, _Fixed_mixin):
    _Name = 'minInclusive'

class CF_totalDigits (ConstrainingFacet, _Fixed_mixin):
    _Name = 'totalDigits'

class CF_fractionDigits (ConstrainingFacet, _Fixed_mixin):
    _Name = 'fractionDigits'

class FundamentalFacet (Facet):
    _Facets = [ 'equal', 'ordered', 'bounded', 'cardinality', 'numeric' ]
    _FacetPrefix = 'FF'

    @classmethod
    def CreateFromDOM (cls, wxs, node, owner_type_definition, base_type_definition=None):
        facet_class = cls.ClassForFacet(node.getAttribute('name'))
        rv = facet_class(base_type_definition=base_type_definition,
                         owner_type_definition=owner_type_definition)
        rv.updateFromDOM(wxs, node)

    def updateFromDOM (self, wxs, node):
        if not node.hasAttribute('name'):
            raise SchemaValidationError('No name attribute in facet')
        assert node.getAttribute('name') == self.Name()
        self._updateFromDOM(wxs, node)

    def _updateFromDOM (self, wxs, node):
        try:
            super(FundamentalFacet, self)._updateFromDOM(wxs, node)
        except AttributeError, e:
            pass
        if (self.valueDatatype() is not None) and node.hasAttribute('value'):
            self._value(self.valueDatatype()(node.getAttribute('value')))
        # @todo
        self.__annotation = None
        return self

class FF_equal (FundamentalFacet):
    _Name = 'equal'

class FF_ordered (FundamentalFacet):
    _LegalValues = ( 'false', 'partial', 'total' )
    _Name = 'ordered'
    def __init__ (self, **kw):
        # @todo correct value type definition
        super(FF_ordered, self).__init__(value_type_definition=datatypes.string.SimpleTypeDefinition(), **kw)

class FF_bounded (FundamentalFacet):
    _Name = 'bounded'
    def __init__ (self, **kw):
        super(FF_bounded, self).__init__(value_type_definition=datatypes.boolean.SimpleTypeDefinition(), **kw)

class FF_cardinality (FundamentalFacet):
    _LegalValues = ( 'finite', 'countably infinite' )
    _Name = 'cardinality'
    def __init__ (self, **kw):
        # @todo correct value type definition
        super(FF_cardinality, self).__init__(value_type_definition=datatypes.string.SimpleTypeDefinition(), **kw)

class FF_numeric (FundamentalFacet):
    _Name = 'numeric'
    def __init__ (self, **kw):
        super(FF_numeric, self).__init__(value_type_definition=datatypes.boolean.SimpleTypeDefinition(), **kw)
