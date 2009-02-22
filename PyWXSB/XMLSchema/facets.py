from PyWXSB.exceptions_ import *
from xml.dom import Node
import types
import datatypes
import structures

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

    # valueDataType is a Python type, probably a subclassed built-in,
    # that is used for the value of this facet.
    __valueDatatype = None
    def valueDatatype (self):
        if (self.__valueDatatype is None) and (self.__baseTypeDefinition is not None):
            self.__valueDatatype = self.__baseTypeDefinition.pythonSupport()
        if self.__valueDatatype is not None:
            return self.__valueDatatype
        raise LogicError("No value datatype available for facet %s" % (self.Name(),))

    __value = None
    def _value (self, v): self.__value = v
    def value (self): return self.__value

    __annotation = None
    def annotation (self): return self.__annotation

    def __init__ (self, **kw):
        super(Facet, self).__init__()
        # Can't create base class instances
        assert Facet != self.__class__
        self.__baseTypeDefinition = kw.get('base_type_definition', None)
        self.__valueDatatype = kw.get('value_datatype', None)
        self.__ownerTypeDefinition = kw.get('owner_type_definition', None)
        value = kw.get('value', None)
        if value is not None:
            self._value(value)

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

    def _setValueFromDOM (self, wxs, node):
        if node.hasAttribute('value'):
            self._value(self.valueDatatype()(node.getAttribute('value')))
        
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

    def updateFromDOM (self, wxs, node):
        super(_Fixed_mixin, self).updateFromDOM(wxs, node)
        self.__fixed = False
        if node.hasAttribute('fixed'):
            self.__fixed = datatypes.boolean.StringToPython(node.getAttribute('fixed'))

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

class CF_pattern (ConstrainingFacet):
    _Name = 'pattern'

    class _PatternElement:
        pattern = None
        annotation = None
        def __init__ (self, pattern=None, annotation=None):
            self.pattern = pattern
            self.annotation = annotation

    __patternElements = None
    def patternElements (self): return self.__patternElements

    def __init__ (self, **kw):
        super(CF_pattern, self).__init__(**kw)
        self.__patternElements = []

    def _setValueFromDOM (self, wxs, node):
        self.__pattern = node.getAttribute('value')

    def updateFromDOM (self, wxs, node):
        super(CF_pattern, self).updateFromDOM(wxs, node)
        self.__patternElements.append(self._PatternElement(self.__pattern, structures.LocateUniqueChild(node, wxs, 'annotation')))

    def _valueString (self):
        return '(%s)' % (','.join([ str(_x.pattern) for _x in self.__patternElements ]),)

class CF_enumeration (ConstrainingFacet):
    _Name = 'enumeration'

    class _EnumerationElement:
        tag = None
        value = None
        description = None
        annotation = None
        def __init__ (self, tag=None, value=None, description=None, annotation=None):
            self.tag = tag
            self.value = value
            self.description = description
            if (self.description is None) and (self.annotation is not None):
                self.description = str(self.annotation)

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
        self.__enumerationElements.append(self._EnumerationElement(tag=self.__tag,
                                                                   annotation=structures.LocateUniqueChild(node, wxs, 'annotation'))) 

    def addEnumeration (self, **kw):
        self.__enumerationElements.append(self._EnumerationElement(**kw))

    def _valueString (self):
        return '(%s)' % (','.join([ str(_x.tag) for _x in self.__enumerationElements ]),)

    def enumPrefix (self, enum_prefix=None):
        if enum_prefix is not None:
            self.__enumPrefix = enum_prefix
        return self.__enumPrefix

class CF_whiteSpace (ConstrainingFacet, _Fixed_mixin):
    _LegalValues = ( 'preserve', 'replace', 'collapse' )
    _Name = 'whiteSpace'

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
        super(FF_ordered, self).__init__(value_datatype=datatypes.string, **kw)

class FF_bounded (FundamentalFacet):
    _Name = 'bounded'
    def __init__ (self, **kw):
        super(FF_bounded, self).__init__(value_datatype=datatypes.boolean, **kw)

class FF_cardinality (FundamentalFacet):
    _LegalValues = ( 'finite', 'countably infinite' )
    _Name = 'cardinality'
    def __init__ (self, **kw):
        super(FF_cardinality, self).__init__(value_datatype=datatypes.string, **kw)

class FF_numeric (FundamentalFacet):
    _Name = 'numeric'
    def __init__ (self, **kw):
        super(FF_numeric, self).__init__(value_datatype=datatypes.boolean, **kw)
