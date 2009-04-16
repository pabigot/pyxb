mkdir -p bindings
rm pywxsb/standard/bindings/[a-z]*

# Some must be done in order, to handle dependencies
# NOTE: Use prefix xml_ instead of xml because xml conflicts with standard package
scripts/genbind pywxsb/standard/schemas/xml.xsd pywxsb/standard/bindings xml_
# NOTE: XSD depends on XML which depends on XSD.  Since we have a workable
# XSD schema built-in, do not create an external pre-loaded schema for
# which we'll have to resolve in XML and subsequently in XSD.
#scripts/genbind pywxsb/standard/schemas/XMLSchema.xsd pywxsb/standard/bindings xs
scripts/genbind pywxsb/standard/schemas/XMLSchema-hasFacetAndProperty.xsd pywxsb/standard/bindings xsd_hfp
scripts/genbind pywxsb/standard/schemas/wsdl.xsd pywxsb/standard/bindings wsdl
scripts/genbind pywxsb/standard/schemas/xhtml.xsd pywxsb/standard/bindings xhtml

# Process anything remaining
scripts/genbind pywxsb/standard/schemas/kml21.xsd pywxsb/standard/bindings kml
scripts/genbind pywxsb/standard/schemas/xmldsig-core-schema.xsd pywxsb/standard/bindings xmldsig
scripts/genbind pywxsb/standard/schemas/xenc-schema.xsd pywxsb/standard/bindings xenc

scripts/genbind pywxsb/standard/schemas/saml-schema-assertion-2.0.xsd pywxsb/standard/bindings saml_assert
