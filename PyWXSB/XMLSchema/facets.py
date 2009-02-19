from PyWXSB.exceptions_ import *
from xml.dom import Node
import types
import datatypes

class _Fixed_mixin (object):
    __fixed = None
    def fixed (self): return self.__fixed

    def _setFromDOM (self, wxs, node):
        super(_Fixed_mixin, self)._setFromDOM(wxs, node)
        self.__fixed = False
        if node.hasAttribute('fixed'):
            self.__fixed = datatypes.boolean.StringToPython(node.getAttribute('fixed'))

class Facet (object):
    _Name = None
    def Name (self): return self._Name

    __baseTypeDefinition = None
    def baseTypeDefinition (self): return self.__baseTypeDefinition

    __valueDatatype = None
    __value = None
    def value (self): return self.__value

    __annotation = None
    def annotation (self): return self.__annotation

    def _setFromDOM (self, wxs, node):
        if not node.hasAttribute('name'):
            raise SchemaValidationError('No name attribute in facet')
        assert node.getAttribute('name') == self.Name()
        if (self.__valueDatatype is not None) and node.hasAttribute('value'):
            self.__value = self.__valueDatatype.StringToPython(node.getAttribute('value'))
        # @todo
        self.__annotation = None
        return self

    def __init__ (self, **kw):
        super(Facet, self).__init__()
        # Can't create base class instances
        assert Facet != self.__class__
        node = kw.get('node', None)
        self.__baseTypeDefinition = kw.get('base_type_definition', None)
        value_datatype = kw.get('value_datatype', None)
        if value_datatype is not None:
            self.__valueDatatype = value_datatype
        if node is not None:
            self._setFromDOM(kw['wxs'], node)

    @classmethod
    def ClassForFacet (cls, name):
        assert cls != Facet
        if 0 <= name.find(':'):
            name = name.split(':', 1)[1]
        assert name in cls._Facets
        facet_class = globals().get('%s_%s' % (cls._FacetPrefix, name), None)
        assert facet_class is not None
        return facet_class

    @classmethod
    def _CreateFromDOM (cls, **kw):
        node = kw.get('node', None)
        assert node is not None
        rv = cls.ClassForFacet(node.nodeName)(*kw)
        return rv

    def __str__ (self):
        rv = []
        if self.__valueDatatype is not None:
            rv.append('%s="%s"' % (self.__name, self.__valueDatatype.PythonToString(self.__value)))
        else:
            rv.append('%s="%s"' % (self.__name, self.__value))
        if self.__fixed:
            rv.append('[fixed]')
        return ''.join(rv)

class ConstrainingFacet (Facet):
    _Facets = [ 'length', 'minLength', 'maxLength', 'pattern', 'enumeration',
                'whiteSpace', 'maxInclusive', 'maxExclusive',
                'minExclusive', 'minInclusive', 'totalDigits', 'fractionDigits' ]
    _FacetPrefix = 'CF'
    
    @classmethod
    def CreateFromDOM (cls, wxs, node, base_type_definition):
        return cls._CreateFromDOM(wxs=wxs, node=node, base_type_definition=base_type_definition)

class CF_length (ConstrainingFacet, _Fixed_mixin):
    _Name = 'length'
    def __init__ (self, **kw):
        super(CF_length, self).__init__(value_datatype=datatype.nonNegativeInteger, **kw)

class CF_minLength (ConstrainingFacet, _Fixed_mixin):
    _Name = 'minLength'
    def __init__ (self, **kw):
        super(CF_minLength, self).__init__(value_datatype=datatype.nonNegativeInteger, **kw)

class CF_maxLength (ConstrainingFacet, _Fixed_mixin):
    _Name = 'maxLength'
    def __init__ (self, **kw):
        super(CF_maxLength, self).__init__(value_datatype=datatype.nonNegativeInteger, **kw)

class CF_pattern (ConstrainingFacet):
    _Name = 'pattern'

class CF_enumeration (ConstrainingFacet):
    _Name = 'enumeration'

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
    def CreateFromDOM (cls, wxs, node):
        facet_class = cls.ClassForFacet(node.getAttribute('name'))
        return facet_class(wxs=wxs, node=node)

class FF_equal (FundamentalFacet):
    _Name = 'equal'

class FF_ordered (FundamentalFacet):
    _LegalValues = ( 'false', 'partial', 'total' )
    _Name = 'ordered'

class FF_bounded (FundamentalFacet):
    _Name = 'bounded'
    def __init__ (self, **kw):
        super(FF_bounded, self).__init__(value_datatype=datatypes.boolean, **kw)

class FF_cardinality (FundamentalFacet):
    _LegalValues = ( 'finite', 'countably infinite' )
    _Name = 'cardinality'

class FF_numeric (FundamentalFacet):
    _Name = 'numeric'
    def __init__ (self, **kw):
        super(FF_numeric, self).__init__(value_datatype=datatypes.boolean, **kw)
