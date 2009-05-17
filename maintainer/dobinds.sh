rm pyxb/standard/bindings/raw/[a-z]*

( cat <<EOList
# NOTE: Use prefix xml_ instead of xml because xml conflicts with standard package
xml.xsd xml_
# NOTE: XSD depends on XML which depends on XSD.  Since we have a workable
# XSD schema built-in, do not create an external pre-loaded schema for
# which we'll have to resolve in XML and subsequently in XSD.
#XMLSchema.xsd xsd
XMLSchema-hasFacetAndProperty.xsd xsd_hfp
wsdl.xsd wsdl
xhtml.xsd xhtml
soapenv.xsd soapenv
soapenc.xsd soapenc
mime.xsd mime
soap.xsd soap
http.xsd http
soap12.xsd soap12
kml21.xsd kml
xmldsig-core-schema.xsd xmldsig
xenc-schema.xsd xenc
saml-schema-assertion-2.0.xsd saml_assert
EOList
) | sed -e '/^#/d' \
  | while read schema prefix ; do
  scripts/genbind \
    --module-path-prefix pyxb.standard.bindings \
    --schema-uri pyxb/standard/schemas/${schema} \
    --schema-prefix ${prefix} \
    --generate-raw-binding \
    --save-component-model
done
