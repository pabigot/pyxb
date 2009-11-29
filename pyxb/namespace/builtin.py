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

"""Classes and global objects related to built-in U{XML Namespaces<http://www.w3.org/TR/2006/REC-xml-names-20060816/index.html>}."""

import pyxb

# A unique identifier for components that are built-in to the PyXB system
BuiltInObjectUID = pyxb.utils.utility.UniqueIdentifier('PyXB-' + pyxb.__version__ + '-Builtin')

from pyxb.namespace import Namespace

class _XMLSchema_instance (Namespace):
    """Extension of L{Namespace} that pre-defines components available in the
    XMLSchema Instance namespace."""

    def _defineBuiltins_ox (self, structures_module):
        """Ensure this namespace is ready for use.

        Overrides base class implementation, since there is no schema
        for this namespace. """
        
        assert structures_module is not None
        schema = structures_module.Schema(namespace_context=self.initialNamespaceContext(), schema_location="URN:noLocation:PyXB:xsi", generation_uid=BuiltInObjectUID, _bypass_preload=True)
        type = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('type', schema))
        nil = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('nil', schema))
        schema_location = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('schemaLocation', schema))
        no_namespace_schema_location = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('noNamespaceSchemaLocation', schema))
        return self

class _XML (Namespace):
    """Extension of L{Namespace} that pre-defines components available in the
    XML (xml) namespace.  Specifically those are the attribute declarations:

      - C{xml:space}
      - C{xml:lang}
      - C{xml:base}
      - C{xml:id}

    the encompassing attribute group declaration:

      - C{xml:specialAttrs}

    and the anonymous types that support these."""

    def _defineBuiltins_ox (self, structures_module):
        """Ensure this namespace is ready for use.

        Overrides base class implementation, since there is no schema
        for this namespace. """
        
        assert structures_module is not None
        import pyxb.binding.datatypes as xsd
        import pyxb.binding.facets as xsdf
        import archive

        self.configureCategories([archive.NamespaceArchive._AnonymousCategory()])

        schema = structures_module.Schema(namespace_context=self.initialNamespaceContext(), schema_location="URN:noLocation:PyXB:XML", generation_uid=BuiltInObjectUID, _bypass_preload=True)

        std_space = structures_module.SimpleTypeDefinition._CreateXMLInstance('space', schema)
        std_space._setAnonymousName(self, anon_name='STD_ANON_space')
        std_space._setBindingNamespace(self)
        std_lang = structures_module.SimpleTypeDefinition._CreateXMLInstance('lang', schema)
        std_lang._setAnonymousName(self, anon_name='STD_ANON_lang')
        std_lang._setBindingNamespace(self)

        base = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('base', schema, std=xsd.anyURI.SimpleTypeDefinition()))
        id = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('id', schema, std=xsd.ID.SimpleTypeDefinition()))
        space = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('space', schema, std=std_space))
        lang = schema._addNamedComponent(structures_module.AttributeDeclaration.CreateBaseInstance('lang', schema, std=std_lang))

        specialAttrs = schema._addNamedComponent(structures_module.AttributeGroupDefinition.CreateBaseInstance('specialAttrs', schema, [
                    structures_module.AttributeUse.CreateBaseInstance(schema, space),
                    structures_module.AttributeUse.CreateBaseInstance(schema, base),
                    structures_module.AttributeUse.CreateBaseInstance(schema, lang),
                    structures_module.AttributeUse.CreateBaseInstance(schema, id),
                    ]))
        
        return self

class _XMLSchema (Namespace):
    """Extension of L{Namespace} that pre-defines components available in the
    XMLSchema namespace.

    The types are defined when L{pyxb.xmlschema.structures} is imported.
    """

    def _defineBuiltins_ox (self, structures_module):
        """Register the built-in types into the XMLSchema namespace."""

        # Defer the definitions to the structures module
        assert structures_module is not None
        structures_module._AddSimpleTypes(self)

        # A little validation here
        assert structures_module.ComplexTypeDefinition.UrTypeDefinition() == self.typeDefinitions()['anyType']
        assert structures_module.SimpleTypeDefinition.SimpleUrTypeDefinition() == self.typeDefinitions()['anySimpleType']

        # Provide access to the binding classes
        self.configureCategories(['typeBinding', 'elementBinding'])
        for ( en, td ) in self.typeDefinitions().items():
            if td.pythonSupport() is not None:
                self.addCategoryObject('typeBinding', en, td.pythonSupport())

XMLSchema_instance = _XMLSchema_instance('http://www.w3.org/2001/XMLSchema-instance',
                                         description='XML Schema Instance',
                                         builtin_namespace='XMLSchema_instance')
"""Namespace and URI for the XMLSchema Instance namespace.  This is always
built-in, and does not (cannot) have an associated schema."""

XMLNamespaces = Namespace('http://www.w3.org/2000/xmlns/',
                          description='Namespaces in XML',
                          builtin_namespace='XMLNamespaces',
                          bound_prefix='xmlns')
"""Namespaces in XML.  Not really a namespace, but is always available as C{xmlns}."""

# http://www.w3.org/2001/XMLSchema.xsd
XMLSchema = _XMLSchema('http://www.w3.org/2001/XMLSchema',
                       description='XML Schema',
                       builtin_namespace='XMLSchema',
                       builtin_module_path='pyxb.binding.datatypes',
                       in_scope_namespaces = { 'xs' : None })
"""Namespace and URI for the XMLSchema namespace (often C{xs}, or C{xsd})"""

# http://www.w3.org/1999/xhtml.xsd
XHTML = Namespace('http://www.w3.org/1999/xhtml',
                  description='Family of document types that extend HTML',
                  builtin_namespace='XHTML',
                  default_namespace=XMLSchema)
"""There really isn't a schema for this, but it's used as the default
namespace in the XML schema, so define it."""

# http://www.w3.org/2001/xml.xsd
XML = _XML('http://www.w3.org/XML/1998/namespace',
           description='XML namespace',
           builtin_namespace='XML',
           builtin_module_path='pyxb.binding.xml_',
           is_undeclared_namespace=True,
           bound_prefix='xml',
           default_namespace=XHTML,
           in_scope_namespaces = { 'xs' : XMLSchema })
"""Namespace and URI for XML itself (always available as C{xml})"""

# http://www.w3.org/2001/XMLSchema-hasFacetAndProperty
XMLSchema_hfp = Namespace('http://www.w3.org/2001/XMLSchema-hasFacetAndProperty',
                          description='Facets appearing in appinfo section',
                          builtin_namespace='XMLSchema_hfp',
                          default_namespace=XMLSchema,
                          in_scope_namespaces = { 'hfp' : None
                                                , 'xhtml' : XHTML })
"""Elements appearing in appinfo elements to support data types."""

# List of built-in namespaces.
BuiltInNamespaces = [
  XMLSchema_instance,
  XMLSchema_hfp,
  XMLSchema,
  XMLNamespaces,
  XML,
  XHTML
]

__InitializedBuiltinNamespaces = False

def _InitializeBuiltinNamespaces (structures_module):
    """Invoked at the end of the L{pyxb.xmlschema.structures} module to
    initialize the component models of the built-in namespaces.

    @param structures_module: The L{pyxb.xmlschema.structures} module may not
    be importable by that name at the time this is invoked (because it is
    still being processed), so it gets passed in as a parameter."""
    global __InitializedBuiltinNamespaces
    if not __InitializedBuiltinNamespaces:
        __InitializedBuiltinNamespaces = True
        [ _ns._defineBuiltins(structures_module) for _ns in BuiltInNamespaces ]

# Set up the prefixes for xml, xmlns, etc.
_UndeclaredNamespaceMap = { }
[ _UndeclaredNamespaceMap.setdefault(_ns.boundPrefix(), _ns) for _ns in BuiltInNamespaces if _ns.isUndeclaredNamespace() ]
