from PyWXSB.exceptions_ import *
from xml.dom import Node
import types
import datatypes
import structures
import PyWXSB.utility as utility
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

    __ownerDatatype = None
    def ownerDatatype (self):
        """The _PST_mixin subclass to which this facet belongs."""
        return self.__ownerDatatype
    def _ownerDatatype (self, owner_datatype):
        self.__ownerDatatype = owner_datatype

    # valueDataType is a Python type, probably a subclassed built-in,
    # that is used for the value of this facet.  In generated bindings
    # this is usually set explicitly in the facet constructor; when
    # processing a schema, it is derived from the value type
    # definition.
    __valueDatatype = None
    def valueDatatype (self):
        if self.__valueDatatype is None:
            assert self.baseTypeDefinition() is not None
            return self.baseTypeDefinition().pythonSupport()
        return self.__valueDatatype

    __value = None
    def _value (self, v): self.__value = v
    def value (self): return self.__value

    __annotation = None
    def annotation (self): return self.__annotation

    def __init__ (self, **kw):
        super(Facet, self).__init__(**kw)
        # Can't create base class instances
        assert Facet != self.__class__
        self.setFromKeywords(_reset=True, _constructor=True, **kw)

    def _setFromKeywords_vb (self, **kw):
        if not kw.get('_reset', False):
            kw.setdefault('base_type_definition', self.__baseTypeDefinition)
            kw.setdefault('owner_type_definition', self.__ownerTypeDefinition)
            kw.setdefault('owner_datatype', self.__ownerDatatype)
            kw.setdefault('value_datatype', self.__valueDatatype)
        self.__baseTypeDefinition = kw.get('base_type_definition', None)
        self.__ownerTypeDefinition = kw.get('owner_type_definition', None)
        self.__ownerDatatype = kw.get('owner_datatype', None)
        self.__valueDatatype = kw.get('value_datatype', None)
        # Verify that there's enough information that we should be
        # able to identify a PST suitable for representing facet
        # values.
        assert (self.__valueDatatype is not None) or (self.__baseTypeDefinition is not None)
        super_fn = getattr(super(Facet, self), '_setFromKeywords_vb', lambda *a,**kw: self)
        return super_fn(**kw)
    
    def setFromKeywords (self, **kw):
        return self._setFromKeywords_vb(**kw)

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
        if isinstance(self, _CollectionFacet_mixin):
            return ','.join([ str(_i) for _i in self.items() ])
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
        super_fn = getattr(super(ConstrainingFacet, self), '_setFromKeywords_vb', lambda *a,**kw: self)
        rv = super_fn(**kw)
        self.__setFromKeywords(**kw)
        return rv
        
class _LateDatatype_mixin (object):
    """Marker class to indicate that the facet instance must be told
    its datatype when it is constructed.  

    Subclasses must define a class variable
    _LateDatatypeBindsSuperclass with a value of True or False.
    """

    @classmethod
    def LateDatatypeBindsSuperclass (cls):
        """Return true if false if the proposed datatype should be
        used, or True if the base type definition of the proposed
        datatype should be used."""
        return cls._LateDatatypeBindsSuperclass

    @classmethod
    def BindingValueDatatype (cls, value_datatype):
        if isinstance(value_datatype, structures.SimpleTypeDefinition):
            # Back up until we find something that actually has a
            # datatype
            while not value_datatype.hasPythonSupport():
                value_datatype = value_datatype.baseTypeDefinition()
            value_datatype = value_datatype.pythonSupport()
        assert issubclass(value_datatype, datatypes._PST_mixin)
        if cls.LateDatatypeBindsSuperclass():
            value_datatype = value_datatype.XsdSuperType()
        return value_datatype

    def bindValueDatatype (self, value_datatype):
        self.setFromKeywords(_constructor=True, value_datatype=self.BindingValueDatatype(value_datatype))

class _Fixed_mixin (object):
    """Mix-in to a constraining facet that adds support for the 'fixed' property."""
    __fixed = None
    def fixed (self): return self.__fixed

    def __setFromKeywords (self, **kw):
        if kw.get('_reset', False):
            self.__fixed = None
        kwv = kw.get('fixed', None)
        if kwv is not None:
            self.__fixed = datatypes.boolean(kwv)
        
    def _setFromKeywords_vb (self, **kw):
        self.__setFromKeywords(**kw)
        super_fn = getattr(super(_Fixed_mixin, self), '_setFromKeywords_vb', lambda *a,**kw: self)
        return super_fn(**kw)
    
class _CollectionFacet_mixin (object):
    """Mix-in to handle facets whose values are collections, not scalars.

    For example, the enumeration and pattern facets maintain a list of
    enumeration values and patterns, respectively, as their value
    space."""

    __items = None

    def _setFromKeywords_vb (self, **kw):
        if kw.get('_reset', False):
            self.__items = []
        if not kw.get('_constructor', False):
            print self._CollectionFacet_itemType
            self.__items.append(self._CollectionFacet_itemType(**kw))
        super_fn = getattr(super(_CollectionFacet_mixin, self), '_setFromKeywords_vb', lambda *a,**kw: self)
        return super_fn(**kw)

    def items (self): return self.__items

    def values (self):
        for item in self.items():
            yield item.value
            
class CF_length (ConstrainingFacet, _Fixed_mixin):
    _Name = 'length'
    def __init__ (self, **kw):
        super(CF_length, self).__init__(value_datatype=datatypes.nonNegativeInteger, **kw)

class CF_minLength (ConstrainingFacet, _Fixed_mixin):
    _Name = 'minLength'
    def __init__ (self, **kw):
        super(CF_minLength, self).__init__(value_datatype=datatypes.nonNegativeInteger, **kw)

class CF_maxLength (ConstrainingFacet, _Fixed_mixin):
    _Name = 'maxLength'
    def __init__ (self, **kw):
        super(CF_maxLength, self).__init__(value_datatype=datatypes.nonNegativeInteger, **kw)

class _PatternElement:
    def __init__ (self, value=None, annotation=None, **kw):
        assert value is not None
        assert isinstance(value, types.StringTypes)
        self.pattern = value
        self.annotation = annotation

    def __str__ (self): return self.pattern

class CF_pattern (ConstrainingFacet, _CollectionFacet_mixin):
    _Name = 'pattern'
    _CollectionFacet_itemType = _PatternElement

    __patternElements = None
    def patternElements (self): return self.__patternElements

    def __init__ (self, **kw):
        super(CF_pattern, self).__init__(value_datatype=datatypes.string, **kw)
        self.__patternElements = []

class _EnumerationElement:
    # The value is the Python value that is used for equality testing
    # against this enumeration.  This is an instance of
    # enumeration.valueDatatype(), initialized from the unicodeValue.
    value = None

    # The base python identifier used for the named constant
    # representing the enumeration value.
    tag = None

    # A reference to the CF_enumeration instance that owns this element
    enumeration = None

    # The unicode string that defines the enumeration value.
    unicodeValue = None

    def __init__ (self, enumeration=None, unicode_value=None,
                  description=None, annotation=None,
                  **kw):
        if 0 < len(kw):
            print 'EnumerationElement kw: %s' % (kw,)
        if unicode_value is None:
            unicode_value = kw['value']
        self.unicodeValue = unicode_value
        self.tag = utility.MakeIdentifier(self.unicodeValue)
        self.enumeration = enumeration
        self.description = description
        self.annotation = annotation
        if (self.description is None) and (self.annotation is not None):
            self.description = str(self.annotation)
        if self.enumeration is not None:
            self.value = self.enumeration.valueDatatype()(self.unicodeValue)

    def __str__ (self):
        return utility.QuotedEscaped(self.unicodeValue)

class CF_enumeration (ConstrainingFacet, _CollectionFacet_mixin, _LateDatatype_mixin):
    """Capture a constraint that restricts valid values to a fixed set.

    A STD that has an enumeration restriction should mix-in
    _Enumeration_mixin, and should have a class variable titled
    _CF_enumeration that is an instance of this class.
    """
    _Name = 'enumeration'
    _CollectionFacet_itemType = _EnumerationElement
    _LateDatatypeBindsSuperclass = False

    # Map from the 
    __tagToElement = None
    __valueToElement = None
    __unicodeToElement = None
    __enumPrefix = 'EV'

    def __init__ (self, **kw):
        super(CF_enumeration, self).__init__(**kw)
        self.__enumPrefix = kw.get('enum_prefix', self.__enumPrefix)
        self.__tagToElement = { }
        self.__valueToElement = { }
        self.__unicodeToElement = { }

    def enumPrefix (self):
        return self.__enumPrefix

    def addEnumeration (self, **kw):
        kw['enumeration'] = self
        ee = _EnumerationElement(**kw)
        assert ee.value is not None
        if ee.tag in self.__tagToElement:
            raise IncompleteImplementationError('Duplicate enumeration tags')
        self.__tagToElement[ee.tag] = ee
        self.__valueToElement[ee.value] = ee
        self.__unicodeToElement[ee.unicodeValue] = ee
        return ee.value

    def valueForTag (self, tag):
        return self.__tagToElement[tag].value

    def tagForValue (self, value):
        if isinstance(value, self.valueDatatype()):
            return self.prefixedTag(self.__valueToElement[value].tag)
        if isinstance(value, types.StringTypes):
            return self.prefixedTag(self.__unicodeToElement[value].tag)
        raise LogicError('Unexpected value of type %s passed to tagForValue' % (type(value),))

    def prefixedTag (self, tag):
        if self.__enumPrefix is None:
            return tag
        return '%s_%s' % (self.__enumPrefix, tag)

class _Enumeration_mixin (object):
    """Note: This class MUST be earlier in the mro than the Python type"""
    def __init__ (self, value):
        if not isinstance(value, self._CF_enumeration.valueDatatype()):
            value = self._CF_enumeration.valueForTag(value)
        super(_Enumeration_mixin, self).__init__(value)

class _WhiteSpace_enum (_Enumeration_mixin, datatypes.string):
    _EnumerationValueSpace = datatypes.string
    _CF_enumeration = CF_enumeration(value_datatype=_EnumerationValueSpace, enum_prefix='WSV')
    WSV_preserve = _CF_enumeration.addEnumeration(unicode_value=u'preserve')
    WSV_replace = _CF_enumeration.addEnumeration(unicode_value=u'replace')
    WSV_collapse = _CF_enumeration.addEnumeration(unicode_value=u'collapse')

class CF_whiteSpace (ConstrainingFacet, _Fixed_mixin):
    _LegalValues = ( 'preserve', 'replace', 'collapse' )
    _Name = 'whiteSpace'
    def __init__ (self, **kw):
        super(CF_whiteSpace, self).__init__(value_datatype=_WhiteSpace_enum, **kw)
    # @todo correct value type definition

class CF_minInclusive (ConstrainingFacet, _Fixed_mixin, _LateDatatype_mixin):
    _Name = 'minInclusive'
    _LateDatatypeBindsSuperclass = False

class CF_maxInclusive (ConstrainingFacet, _Fixed_mixin, _LateDatatype_mixin):
    _Name = 'maxInclusive'
    _LateDatatypeBindsSuperclass = False

class CF_minExclusive (ConstrainingFacet, _Fixed_mixin, _LateDatatype_mixin):
    _Name = 'minExclusive'
    _LateDatatypeBindsSuperclass = True

class CF_maxExclusive (ConstrainingFacet, _Fixed_mixin, _LateDatatype_mixin):
    _Name = 'maxExclusive'
    _LateDatatypeBindsSuperclass = True

class CF_totalDigits (ConstrainingFacet, _Fixed_mixin):
    _Name = 'totalDigits'
    def __init__ (self, **kw):
        super(CF_totalDigits, self).__init__(value_datatype=datatypes.positiveInteger, **kw)

class CF_fractionDigits (ConstrainingFacet, _Fixed_mixin):
    _Name = 'fractionDigits'
    def __init__ (self, **kw):
        super(CF_fractionDigits, self).__init__(value_datatype=datatypes.nonNegativeInteger, **kw)

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
        super(FF_ordered, self).__init__(value_datatype=datatypes.string, **kw)

class FF_bounded (FundamentalFacet):
    _Name = 'bounded'
    def __init__ (self, **kw):
        super(FF_bounded, self).__init__(value_datatype=datatypes.boolean, **kw)

class FF_cardinality (FundamentalFacet):
    _LegalValues = ( 'finite', 'countably infinite' )
    _Name = 'cardinality'
    def __init__ (self, **kw):
        # @todo correct value type definition
        super(FF_cardinality, self).__init__(value_datatype=datatypes.string, **kw)

class FF_numeric (FundamentalFacet):
    _Name = 'numeric'
    def __init__ (self, **kw):
        super(FF_numeric, self).__init__(value_datatype=datatypes.boolean, **kw)
