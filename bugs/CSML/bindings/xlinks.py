# PyWXSB bindings for <not provided>
# Generated 2009-06-24 07:11:52.695705 by PyWXSB version UNSPECIFIED
import pyxb.binding
import pyxb.exceptions_
import pyxb.utils.domutils
import sys

# Import bindings for namespaces imported into schema


# Make sure there's a registered Namespace instance, and that it knows
# about this module.
Namespace = pyxb.namespace.NamespaceForURI(u'http://www.w3.org/1999/xlink', create_if_missing=True)
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

# Atomic SimpleTypeDefinition
class _STD_ANON_1 (pyxb.binding.datatypes.string, pyxb.binding.basis.enumeration_mixin):
    """No information"""

    _ExpandedName = None
_STD_ANON_1._CF_enumeration = pyxb.binding.facets.CF_enumeration(value_datatype=_STD_ANON_1, enum_prefix=None)
_STD_ANON_1.onLoad = _STD_ANON_1._CF_enumeration.addEnumeration(unicode_value=u'onLoad')
_STD_ANON_1.onRequest = _STD_ANON_1._CF_enumeration.addEnumeration(unicode_value=u'onRequest')
_STD_ANON_1.other = _STD_ANON_1._CF_enumeration.addEnumeration(unicode_value=u'other')
_STD_ANON_1.none = _STD_ANON_1._CF_enumeration.addEnumeration(unicode_value=u'none')
_STD_ANON_1._InitializeFacetMap(_STD_ANON_1._CF_enumeration)

# Atomic SimpleTypeDefinition
class _STD_ANON_2 (pyxb.binding.datatypes.string, pyxb.binding.basis.enumeration_mixin):
    """No information"""

    _ExpandedName = None
_STD_ANON_2._CF_enumeration = pyxb.binding.facets.CF_enumeration(value_datatype=_STD_ANON_2, enum_prefix=None)
_STD_ANON_2.new = _STD_ANON_2._CF_enumeration.addEnumeration(unicode_value=u'new')
_STD_ANON_2.replace = _STD_ANON_2._CF_enumeration.addEnumeration(unicode_value=u'replace')
_STD_ANON_2.embed = _STD_ANON_2._CF_enumeration.addEnumeration(unicode_value=u'embed')
_STD_ANON_2.other = _STD_ANON_2._CF_enumeration.addEnumeration(unicode_value=u'other')
_STD_ANON_2.none = _STD_ANON_2._CF_enumeration.addEnumeration(unicode_value=u'none')
_STD_ANON_2._InitializeFacetMap(_STD_ANON_2._CF_enumeration)
