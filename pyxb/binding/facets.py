# Copyright 2009, Peter A. Bigot
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain a
# copy of the License at:
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Classes related to XMLSchema facets.

The definitions herein are from sections U{4.2<http://www.w3.org/TR/xmlschema-2/index.html#rf-facets>}
and U{4.3<http://www.w3.org/TR/xmlschema-2/index.html#rf-facets>} of
U{XML Schema Part 2: Datatypes<http://www.w3.org/TR/xmlschema-2/>}.
Facets are attributes of a datatype that constrain its lexical and
value spaces.

"""

from xml.dom import Node
import pyxb
import types
import datatypes
import basis
from pyxb.utils import utility
from pyxb.utils import domutils
import re

class Facet (pyxb.cscRoot):
    """The base class for facets.

    This provides association with STDs, a name, and a value for the facet.
    """
    
    _Name = None
    @classmethod
    def Name (self):
        """The name of a facet is a class constant."""
        return self._Name

    __baseTypeDefinition = None
    def baseTypeDefinition (self):
        """The SimpleTypeDefinition component restricted by this facet.

        Note: this is NOT the STD to which the facet belongs, but is
        usually that STD's base type.  I.e., this jumps us through all
        the containing restrictions and extensions to get to the core
        type definition."""
        return self.__baseTypeDefinition

    __ownerTypeDefinition = None
    def ownerTypeDefinition (self):
        """The SimpleTypeDefinition component to which this facet belongs.

        I.e., the one in which the hasFacet specification was found.
        This value is None if the facet is not associated with an
        STD."""
        return self.__ownerTypeDefinition

    __ownerDatatype = None
    def ownerDatatype (self):
        """The PyXB_simpleTypeDefinition subclass to which this facet belongs."""
        return self.__ownerDatatype
    def _ownerDatatype (self, owner_datatype):
        self.__ownerDatatype = owner_datatype

    # The default valueDatatype to use for instances of this class.
    # This is overridden in subclasses that do not use late value
    # datatype bindings.
    _ValueDatatype = None

    # The datatype used for facet values.
    __valueDatatype = None
    def valueDatatype (self):
        """Get the datatype used to represent values of the facet.

        This usually has nothing to do with the owner datatype; for
        example, the length facet may apply to any STD but the value
        of the facet is an integer.  In generated bindings this is
        usually set explicitly in the facet constructor; when
        processing a schema, it is derived from the value's type
        definition.
        """
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
        """Create a facet instance, initializing it from the keyword parameters."""
        super(Facet, self).__init__(**kw)
        # Can't create base class instances
        assert Facet != self.__class__
        self.setFromKeywords(_reset=True, _constructor=True, **kw)

    def _setFromKeywords_vb (self, **kw):
        """Configure values of the facet from a set of keywords.

        This method is pre-extended; subclasses should invoke the
        parent method after setting their local configuration.

        @keyword _reset: If C{False} or missing, existing values will
                         be retained if they do not appear in the
                         keywords.  If C{True}, members not defined in
                         the keywords are set to a default.
        @keyword base_type_definition:
        @keyword owner_type_definition:
        @keyword owner_datatype:
        @keyword value_datatype:
        """

        if not kw.get('_reset', False):
            kw.setdefault('base_type_definition', self.__baseTypeDefinition)
            kw.setdefault('owner_type_definition', self.__ownerTypeDefinition)
            kw.setdefault('owner_datatype', self.__ownerDatatype)
            kw.setdefault('value_datatype', self.__valueDatatype)
        self.__baseTypeDefinition = kw.get('base_type_definition', None)
        self.__ownerTypeDefinition = kw.get('owner_type_definition', None)
        self.__ownerDatatype = kw.get('owner_datatype', None)
        self.__valueDatatype = kw.get('value_datatype', self._ValueDatatype)
        # Verify that there's enough information that we should be
        # able to identify a PST suitable for representing facet
        # values.
        assert (self.__valueDatatype is not None) or (self.__baseTypeDefinition is not None)
        super_fn = getattr(super(Facet, self), '_setFromKeywords_vb', lambda *a,**kw: self)
        return super_fn(**kw)
    
    def setFromKeywords (self, **kw):
        """Public entrypoint to the _setFromKeywords_vb call hierarchy."""
        return self._setFromKeywords_vb(**kw)

    @classmethod
    def ClassForFacet (cls, name):
        """Given the name of a facet, return the Facet subclass that represents it."""
        assert cls != Facet
        if 0 <= name.find(':'):
            name = name.split(':', 1)[1]
        facet_class = globals().get('%s_%s' % (cls._FacetPrefix, name), None)
        if facet_class is None:
            raise pyxb.LogicError('Unrecognized facet name %s: expect %s' % (name, ','.join([_f._Name for _f in cls.Facets])))
        assert facet_class is not None
        return facet_class

    def _valueString (self):
        if isinstance(self, _CollectionFacet_mixin):
            return ','.join([ str(_i) for _i in self.items() ])
        if (self.valueDatatype() is not None) and (self.value() is not None):
            try:
                return self.valueDatatype().XsdLiteral(self.value())
            except Exception, e:
                print 'Stringize facet %s produced %s' % (self.Name(), e)
                raise
        return str(self.value())
    
    def __str__ (self):
        rv = []
        rv.append('%s="%s"' % (self.Name(), self._valueString()))
        if isinstance(self, _Fixed_mixin) and self.fixed():
            rv.append('[fixed]')
        return ''.join(rv)

class ConstrainingFacet (Facet):
    """One of the facets defined in section 4.3, which provide
    constraints on the lexical space of a type definition."""
    
    # The prefix used for Python classes used for a constraining
    # facet.  Note that this is not the prefix used when generating a
    # Python class member that specifies a constraining instance, even
    # if it happens to be the same digraph.
    _FacetPrefix = 'CF'
    
    def __init__ (self, **kw):
        super(ConstrainingFacet, self).__init__(**kw)

    def _validateConstraint_vx (self, value):
        raise pyxb.LogicError("Facet %s does not implement constraints" % (self.Name(),))

    def validateConstraint (self, value):
        """Return True iff the given value satisfies the constraint represented by this facet instance.

        The actual test is delegated to the subclasses."""
        return self._validateConstraint_vx(value)

    def __setFromKeywords(self, **kw):
        kwv = kw.get('value', None)
        if kwv is not None:
            if not isinstance(kwv, self.valueDatatype()):
                kwv = self.valueDatatype()(kwv)
            self._value(kwv)

    def _setFromKeywords_vb (self, **kw):
        """Extend base class.

        Additional keywords:
        * value
        """
        # NB: This uses post-extension because it makes reference to the value_data_type
        super_fn = getattr(super(ConstrainingFacet, self), '_setFromKeywords_vb', lambda *a,**kw: self)
        rv = super_fn(**kw)
        self.__setFromKeywords(**kw)
        return rv
        
class _LateDatatype_mixin (pyxb.cscRoot):
    """Marker class to indicate that the facet instance must be told
    its datatype when it is constructed.

    This is necessary for facets like L{CF_minInclusive} and
    L{CF_minExclusive}, for which the value is determined by the base
    type definition of the associated STD.  In some cases the value
    that must be used in the facet cannot be represented in the Python
    type used for the facet; see L{LateDatatypeBindsSuperclass}.
    """

    _LateDatatypeBindsSuperclass = None
    """The class variable that indicates that the Subclasses must
    override this variable with a value of C{True} or C{False}.  The
    value is C{True} iff the value used for the facet is not within
    the value space of the corresponding value datatype; for example,
    L{CF_minExclusive}."""


    @classmethod
    def LateDatatypeBindsSuperclass (cls):
        """Return true if false if the proposed datatype should be
        used, or True if the base type definition of the proposed
        datatype should be used."""
        if cls._LateDatatypeBindsSuperclass is None:
            raise pyxb.LogicError('Class %s did not set _LateDatatypeBindsSuperclass variable.')
        return cls._LateDatatypeBindsSuperclass

    @classmethod
    def BindingValueDatatype (cls, value_type):
        """Find the datatype for facet values when this facet is bound
        to the given value_type.

        If the C{value_type} is an STD, the associated Python support
        datatype from this value_type scanning up through the base
        type hierarchy is used.
        """
        
        import pyxb.xmlschema.structures as structures
        if isinstance(value_type, structures.SimpleTypeDefinition):
            # Back up until we find something that actually has a
            # datatype
            while not value_type.hasPythonSupport():
                value_type = value_type.baseTypeDefinition()
            value_type = value_type.pythonSupport()
        assert issubclass(value_type, basis.simpleTypeDefinition)
        if cls.LateDatatypeBindsSuperclass():
            value_type = value_type.XsdSuperType()
        return value_type

    def bindValueDatatype (self, value_datatype):
        self.setFromKeywords(_constructor=True, value_datatype=self.BindingValueDatatype(value_datatype))

class _Fixed_mixin (pyxb.cscRoot):
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
        """Extend base class.

        Additional keywords:
        * fixed
        """
        self.__setFromKeywords(**kw)
        super_fn = getattr(super(_Fixed_mixin, self), '_setFromKeywords_vb', lambda *a,**kw: self)
        return super_fn(**kw)
    
class _CollectionFacet_mixin (pyxb.cscRoot):
    """Mix-in to handle facets whose values are collections, not scalars.

    For example, the enumeration and pattern facets maintain a list of
    enumeration values and patterns, respectively, as their value
    space.

    Subclasses must define a class variable _CollectionFacet_itemType
    which is a reference to a class that is used to construct members
    of the collection.
    """

    __items = None
    def _setFromKeywords_vb (self, **kw):
        """Extend base class.
        
        @keyword _constructor: If C{False} or absent, the object being
                               set is a member of the collection.  If
                               C{True}, the object being set is the
                               collection itself.
        """
        if kw.get('_reset', False):
            self.__items = []
        if not kw.get('_constructor', False):
            #print self._CollectionFacet_itemType
            self.__items.append(self._CollectionFacet_itemType(facet_instance=self, **kw))
        super_fn = getattr(super(_CollectionFacet_mixin, self), '_setFromKeywords_vb', lambda *a,**kw: self)
        return super_fn(**kw)

    def items (self):
        """The members of the collection."""
        # @todo should this be by reference?
        return self.__items

    def values (self):
        """A generator for members of the collection."""
        for item in self.items():
            yield item.value
            
class CF_length (ConstrainingFacet, _Fixed_mixin):
    """A facet that specifies the length of the lexical representation of a value.
    
    See U{http://www.w3.org/TR/xmlschema-2/#rf-length}
    """
    _Name = 'length'
    _ValueDatatype = datatypes.nonNegativeInteger

    def _validateConstraint_vx (self, value):
        value_length = value.xsdValueLength()
        return (value_length is None) or (self.value() is None) or (value_length == self.value())

class CF_minLength (ConstrainingFacet, _Fixed_mixin):
    """A facet that constrains the length of the lexical representation of a value.
    
    See U{http://www.w3.org/TR/xmlschema-2/#rf-minLength}
    """
    _Name = 'minLength'
    _ValueDatatype = datatypes.nonNegativeInteger

    def _validateConstraint_vx (self, value):
        value_length = value.xsdValueLength()
        return (value_length is None) or (self.value() is None) or (value_length >= self.value())

class CF_maxLength (ConstrainingFacet, _Fixed_mixin):
    """A facet that constrains the length of the lexical representation of a value.
    
    See U{http://www.w3.org/TR/xmlschema-2/#rf-minLength}
    """
    _Name = 'maxLength'
    _ValueDatatype = datatypes.nonNegativeInteger

    def _validateConstraint_vx (self, value):
        value_length = value.xsdValueLength()
        return (value_length is None) or (self.value() is None) or (value_length <= self.value())

import pyxb.utils.xmlre

class _PatternElement (utility.PrivateTransient_mixin):
    """This class represents individual patterns that appear within a CF_pattern collection."""

    # The compiled regular expression is marked transient because we
    # normally do development with Python 2.5, and consequently save
    # the pickled namespace archives that go into the distribution
    # with that version.  Compiled regular expressions in Python 2.5
    # include a reference to the re._compile method, which does not
    # exist in Python 2.4.  As a result, attempts to load a namespace
    # which includes types with pattern restrictions fail.
    __PrivateTransient = set()

    __compiledExpression = None
    __PrivateTransient.add('compiledExpression')

    __pythonExpression = None

    pattern = None
    annotation = None
    def __init__ (self, pattern=None, value=None, annotation=None, **kw):
        if pattern is None:
            assert value is not None
            pattern = value
        assert isinstance(pattern, types.StringTypes)
        self.pattern = pattern
        self.annotation = annotation
        self.__pythonExpression = pyxb.utils.xmlre.XMLToPython(pattern)
        #print 'Translated pattern %s to %s' % (pattern.encode('ascii', 'xmlcharrefreplace'),
        #                                       self.__pythonExpression.encode('ascii', 'xmlcharrefreplace'))

    def __str__ (self): return self.pattern

    def matches (self, text):
        if self.__compiledExpression is None:
            self.__compiledExpression = re.compile(self.__pythonExpression)
        return self.__compiledExpression.match(text)

class CF_pattern (ConstrainingFacet, _CollectionFacet_mixin):
    """A facet that constrains the lexical representation of a value
    to match one of a set of patterns.

    See U{http://www.w3.org/TR/xmlschema-2/#rf-pattern}

    @note: In PyXB, pattern constraints are ignored for any type with
    a Python representation that does not derive from C{basestring}.
    This is due to the difficulty in reconstructing the lexical
    representation of a non-string type after it has been converted to
    its value space.

    @todo: On creating new instances of non-string simple types from
    string representations, we could apply pattern constraints.  That
    would mean checking them prior to invoking the Factory method.
    """
    _Name = 'pattern'
    _CollectionFacet_itemType = _PatternElement
    _ValueDatatype = datatypes.string

    __patternElements = None
    def patternElements (self): return self.__patternElements

    def __init__ (self, **kw):
        super(CF_pattern, self).__init__(**kw)
        self.__patternElements = []

    def addPattern (self, **kw):
        pattern = self._CollectionFacet_itemType(**kw)
        self.__patternElements.append(pattern)
        return pattern

    def _validateConstraint_vx (self, value):
        # If validation is inhibited, or if the facet hasn't had any
        # restrictions applied yet, return True.
        if 0 == len(self.__patternElements):
            return True
        if not isinstance(value, basestring):
            return True
        for pe in self.__patternElements:
            if pe.matches(value):
                return True
        return False

class _EnumerationElement (object):
    """This class represents individual values that appear within a
    L{CF_enumeration} collection."""
    
    __value = None
    def value (self):
        """The Python value that is used for equality testing
        against this enumeration. 

        This is an instance of L{enumeration.valueDatatype()<CF_enumeration.valueDatatype>},
        initialized from the unicodeValue."""
        return self.__value

    __tag = None
    def tag (self):
        """The Python identifier used for the named constant representing
        the enumeration value.

        This should include any desired prefix, since it must be
        unique within its binding class.  If C{None}, no enumeration
        constant will be generated."""
        return self.__tag
    def _setTag (self, tag):
        """Set the tag to be used for this enumeration."""
        self.__tag = tag

    __bindingTag = None
    def bindingTag (self):
        return self.__bindingTag
    def _setBindingTag (self, binding_tag):
        self.__bindingTag = binding_tag

    __enumeration = None
    def enumeration (self):
        """A reference to the L{CF_enumeration} instance that owns this element."""
        return self.__enumeration

    __unicodeValue = None
    def unicodeValue (self):
        """The unicode string that defines the enumeration value."""
        return self.__unicodeValue

    def __init__ (self, enumeration=None, unicode_value=None,
                  description=None, annotation=None,
                  **kw):
        # The preferred keyword is "unicode_value", but when being
        # generically applied by
        # structures.SimpleTypeDefinition.__updateFacets, the unicode
        # value comes in through the keyword "value".  Similarly for
        # "enumeration" and "facet_instance".
        if unicode_value is None:
            unicode_value = kw['value']
        if enumeration is None:
            enumeration = kw['facet_instance']
        self.__unicodeValue = unicode_value
        self.__enumeration = enumeration
        self.__description = description
        self.__annotation = annotation

        assert self.__enumeration is not None

        value_datatype = self.enumeration().valueDatatype()
        self.__value = value_datatype.Factory(self.unicodeValue(), _validate_constraints=False)

        if (self.__description is None) and (self.__annotation is not None):
            self.__description = str(self.__annotation)

    def __str__ (self):
        return utility.QuotedEscaped(self.unicodeValue())

class CF_enumeration (ConstrainingFacet, _CollectionFacet_mixin, _LateDatatype_mixin):
    """Capture a constraint that restricts valid values to a fixed set.

    A STD that has an enumeration restriction should mix-in
    L{pyxb.binding.basis.enumeration_mixin}, and should have a class
    variable titled C{_CF_enumeration} that is an instance of this
    class.

    "unicode" refers to the Unicode string by which the value is
    represented in XML.

    "tag" refers to the Python member reference associated with the
    enumeration.  The value is derived from the unicode value of the
    enumeration element and an optional prefix that identifies the
    owning simple type when the tag is promoted to module-level
    visibility.
    
    "value" refers to the Python value held in the tag

    See U{http://www.w3.org/TR/xmlschema-2/#rf-enumeration}
    """
    _Name = 'enumeration'
    _CollectionFacet_itemType = _EnumerationElement
    _LateDatatypeBindsSuperclass = False

    __elements = None
    __tagToElement = None
    __valueToElement = None
    __unicodeToElement = None

    # The prefix to be used when making enumeration tags visible at
    # the module level.  If None, tags are not made visible.
    __enumPrefix = None

    def __init__ (self, **kw):
        super(CF_enumeration, self).__init__(**kw)
        self.__enumPrefix = kw.get('enum_prefix', self.__enumPrefix)
        self.__elements = []
        self.__tagToElement = { }
        self.__valueToElement = { }
        self.__unicodeToElement = { }

    def enumPrefix (self):
        return self.__enumPrefix

    def addEnumeration (self, **kw):
        kw['enumeration'] = self
        ee = _EnumerationElement(**kw)
        if ee.tag in self.__tagToElement:
            raise pyxb.IncompleteImplementationError('Duplicate enumeration tags')
        self.__tagToElement[ee.tag()] = ee
        self.__unicodeToElement[ee.unicodeValue()] = ee
        value = ee.value()
        # Not just issubclass(self.valueDatatype(), basis.STD_list);
        # this may be a union with one of those as a member type.
        if isinstance(value, list):
            value = ' '.join([ _v.xsdLiteral() for _v in value ])
        self.__valueToElement[value] = ee
        self.__elements.append(ee)
        return value

    def elementForValue (self, value):
        """Return the L{_EnumerationElement} instance that has the given value.

        @raise KeyError: the value is not valid for the enumeration."""
        return self.__valueToElement[value]

    def valueForUnicode (self, ustr):
        """Return the enumeration value corresponding to the given unicode string.

        If ustr is not a valid option for this enumeration, return None."""
        rv = self.__unicodeToElement.get(ustr, None)
        if rv is not None:
            rv = rv.value()
        return rv

    def _validateConstraint_vx (self, value):
        # If validation is inhibited, or if the facet hasn't had any
        # restrictions applied yet, return True.
        if 0 == len(self.__elements):
            return True
        for ee in self.__elements:
            if ee.value() == value:
                return True
        return False

class _Enumeration_mixin (pyxb.cscRoot):
    """Marker class to indicate that the generated binding has enumeration members."""
    @classmethod
    def valueForUnicode (cls, ustr):
        return cls._CF_enumeration.valueForUnicode(ustr)

class _WhiteSpace_enum (datatypes.NMTOKEN, _Enumeration_mixin):
    """The enumeration used to constrain the whiteSpace facet"""
    pass
_WhiteSpace_enum._CF_enumeration = CF_enumeration(value_datatype=_WhiteSpace_enum)
_WhiteSpace_enum.preserve = _WhiteSpace_enum._CF_enumeration.addEnumeration(unicode_value=u'preserve')
_WhiteSpace_enum.replace = _WhiteSpace_enum._CF_enumeration.addEnumeration(unicode_value=u'replace')
_WhiteSpace_enum.collapse = _WhiteSpace_enum._CF_enumeration.addEnumeration(unicode_value=u'collapse')
# NOTE: For correctness we really need to initialize the facet map for
# WhiteSpace_enum, even though at the moment it isn't necessary.  We
# can't right now, because its parent datatypes.NMTOKEN hasn't been
# initialized yet
_WhiteSpace_enum._InitializeFacetMap(_WhiteSpace_enum._CF_enumeration)

class CF_whiteSpace (ConstrainingFacet, _Fixed_mixin):
    """Specify the value-space interpretation of whitespace.

    See U{http://www.w3.org/TR/xmlschema-2/#rf-whiteSpace}
    """
    _Name = 'whiteSpace'
    _ValueDatatype = _WhiteSpace_enum

    __TabCRLF_re = re.compile("[\t\n\r]")
    __MultiSpace_re = re.compile(" +")
    def normalizeString (self, value):
        """Normalize the given string in accordance with the configured whitespace interpretation."""
        if self.value() is None:
            return value
        if self.value() == _WhiteSpace_enum.preserve:
            return utility.NormalizeWhitespace(value, preserve=True)
        if self.value() == _WhiteSpace_enum.replace:
            return utility.NormalizeWhitespace(value, replace=True)
        assert self.value() == _WhiteSpace_enum.collapse, 'Unexpected value "%s" for whiteSpace facet' % (self.value(),)
        return utility.NormalizeWhitespace(value, collapse=True)
    
    def _validateConstraint_vx (self, value):
        """No validation rules for whitespace facet."""
        return True

class CF_minInclusive (ConstrainingFacet, _Fixed_mixin, _LateDatatype_mixin):
    """Specify the minimum legal value for the constrained type.

    See U{http://www.w3.org/TR/xmlschema-2/#rf-minInclusive}
    """
    _Name = 'minInclusive'
    _LateDatatypeBindsSuperclass = False

    def _validateConstraint_vx (self, value):
        return (self.value() is None) or (self.value() <= value)


class CF_maxInclusive (ConstrainingFacet, _Fixed_mixin, _LateDatatype_mixin):
    """Specify the maximum legal value for the constrained type.

    See U{http://www.w3.org/TR/xmlschema-2/#rf-maxInclusive}
    """
    _Name = 'maxInclusive'
    _LateDatatypeBindsSuperclass = False

    def _validateConstraint_vx (self, value):
        return (self.value() is None) or (self.value() >= value)

class CF_minExclusive (ConstrainingFacet, _Fixed_mixin, _LateDatatype_mixin):
    """Specify the exclusive lower bound of legal values for the constrained type.

    See U{http://www.w3.org/TR/xmlschema-2/#rf-minExclusive}
    """
    _Name = 'minExclusive'
    _LateDatatypeBindsSuperclass = True

    def _validateConstraint_vx (self, value):
        return (self.value() is None) or (self.value() < value)

class CF_maxExclusive (ConstrainingFacet, _Fixed_mixin, _LateDatatype_mixin):
    """Specify the exclusive upper bound of legal values for the constrained type.

    See U{http://www.w3.org/TR/xmlschema-2/#rf-maxExclusive}
    """
    _Name = 'maxExclusive'
    _LateDatatypeBindsSuperclass = True

    def _validateConstraint_vx (self, value):
        return (self.value() is None) or (self.value() > value)

class CF_totalDigits (ConstrainingFacet, _Fixed_mixin):
    """Specify the number of digits in the *value* space of the type.

    See U{http://www.w3.org/TR/xmlschema-2/#rf-totalDigits}
    """
    _Name = 'totalDigits'
    _ValueDatatype = datatypes.positiveInteger

    def _validateConstraint_vx (self, value):
        if self.value() is None:
            return True
        n = 0
        scale = 1
        match = False
        v = None
        while (n <= self.value()) and (not match):
            v = long(value * scale)
            match = ((value * scale) == v)
            if self.value() == n:
                break
            n += 1
            scale *= 10
        while n < self.value():
            n += 1
            scale *= 10
        return match and (v is not None) and (abs(v) < scale)

class CF_fractionDigits (ConstrainingFacet, _Fixed_mixin):
    """Specify the number of sub-unit digits in the *value* space of the type.

    See U{http://www.w3.org/TR/xmlschema-2/#rf-fractionDigits}
    """
    _Name = 'fractionDigits'
    _ValueDatatype = datatypes.nonNegativeInteger

    def _validateConstraint_vx (self, value):
        if self.value() is None:
            return True
        n = 0
        scale = 1
        while n <= self.value():
            if ((value * scale) == long(value * scale)):
                return True
            n += 1
            scale *= 10
        return False

class FundamentalFacet (Facet):
    """A fundamental facet provides information on the value space of the associated type."""
    
    _FacetPrefix = 'FF'

    @classmethod
    def CreateFromDOM (cls, node, owner_type_definition, base_type_definition=None):
        facet_class = cls.ClassForFacet(node.getAttribute('name'))
        rv = facet_class(base_type_definition=base_type_definition,
                         owner_type_definition=owner_type_definition)
        rv.updateFromDOM(node)

    def updateFromDOM (self, node):
        if not node.hasAttribute('name'):
            raise pyxb.SchemaValidationError('No name attribute in facet')
        assert node.getAttribute('name') == self.Name()
        self._updateFromDOM(node)

    def _updateFromDOM (self, node):
        try:
            super(FundamentalFacet, self)._updateFromDOM(node)
        except AttributeError, e:
            pass
        if (self.valueDatatype() is not None) and node.hasAttribute('value'):
            self._value(self.valueDatatype()(node.getAttribute('value')))
        # @todo
        self.__annotation = None
        return self

class FF_equal (FundamentalFacet):
    """Specifies that the associated type supports a notion of equality.

    See U{http://www.w3.org/TR/xmlschema-2/#equal}
    """
    
    _Name = 'equal'

class FF_ordered (FundamentalFacet):
    """Specifies that the associated type supports a notion of order.

    See U{http://www.w3.org/TR/xmlschema-2/#rf-ordered}
    """

    _LegalValues = ( 'false', 'partial', 'total' )
    _Name = 'ordered'
    _ValueDatatype = datatypes.string

    def __init__ (self, **kw):
        # @todo: correct value type definition
        super(FF_ordered, self).__init__(**kw)

class FF_bounded (FundamentalFacet):
    """Specifies that the associated type supports a notion of bounds.

    See U{http://www.w3.org/TR/xmlschema-2/#rf-bounded}
    """

    _Name = 'bounded'
    _ValueDatatype = datatypes.boolean

class FF_cardinality (FundamentalFacet):
    """Specifies that the associated type supports a notion of length.

    See U{http://www.w3.org/TR/xmlschema-2/#rf-cardinality}
    """

    _LegalValues = ( 'finite', 'countably infinite' )
    _Name = 'cardinality'
    _ValueDatatype = datatypes.string
    def __init__ (self, **kw):
        # @todo correct value type definition
        super(FF_cardinality, self).__init__(value_datatype=datatypes.string, **kw)

class FF_numeric (FundamentalFacet):
    """Specifies that the associated type represents a number.

    See U{http://www.w3.org/TR/xmlschema-2/#rf-numeric}
    """

    _Name = 'numeric'
    _ValueDatatype = datatypes.boolean

# The fixed set of expected facets
ConstrainingFacet.Facets = [
    CF_length, CF_minLength, CF_maxLength, CF_pattern, CF_enumeration,
    CF_whiteSpace, CF_minInclusive, CF_maxInclusive, CF_minExclusive,
    CF_maxExclusive, CF_totalDigits, CF_fractionDigits ]

FundamentalFacet.Facets = [
    FF_equal, FF_ordered, FF_bounded, FF_cardinality, FF_numeric ]

Facet.Facets = []
Facet.Facets.extend(ConstrainingFacet.Facets)
Facet.Facets.extend(FundamentalFacet.Facets)
