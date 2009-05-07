rm pyxb/standard/bindings/raw/[a-z]*

# Some must be done in order, to handle dependencies
# NOTE: Use prefix xml_ instead of xml because xml conflicts with standard package
scripts/genbind pyxb/standard/schemas/xml.xsd pyxb/standard/bindings/raw xml_
# NOTE: XSD depends on XML which depends on XSD.  Since we have a workable
# XSD schema built-in, do not create an external pre-loaded schema for
# which we'll have to resolve in XML and subsequently in XSD.
#scripts/genbind pyxb/standard/schemas/XMLSchema.xsd pyxb/standard/bindings/raw xs
scripts/genbind pyxb/standard/schemas/XMLSchema-hasFacetAndProperty.xsd pyxb/standard/bindings/raw xsd_hfp
scripts/genbind pyxb/standard/schemas/wsdl.xsd pyxb/standard/bindings/raw wsdl
scripts/genbind pyxb/standard/schemas/xhtml.xsd pyxb/standard/bindings/raw xhtml

# Useful wsdl dependents
scripts/genbind pyxb/standard/schemas/soap.xsd pyxb/standard/bindings/raw soap
scripts/genbind pyxb/standard/schemas/soapenc.xsd pyxb/standard/bindings/raw soapenc
scripts/genbind pyxb/standard/schemas/mimebind.xsd pyxb/standard/bindings/raw soapmime
scripts/genbind pyxb/standard/schemas/soapbind.xsd pyxb/standard/bindings/raw soapbind
scripts/genbind pyxb/standard/schemas/httpbind.xsd pyxb/standard/bindings/raw soaphttp
scripts/genbind pyxb/standard/schemas/soap12.xsd pyxb/standard/bindings/raw soap12

# Process anything remaining
scripts/genbind pyxb/standard/schemas/kml21.xsd pyxb/standard/bindings/raw kml
scripts/genbind pyxb/standard/schemas/xmldsig-core-schema.xsd pyxb/standard/bindings/raw xmldsig
scripts/genbind pyxb/standard/schemas/xenc-schema.xsd pyxb/standard/bindings/raw xenc

scripts/genbind pyxb/standard/schemas/saml-schema-assertion-2.0.xsd pyxb/standard/bindings/raw saml_assert
