test -f soap.xsd || wget -O soap.xsd http://schemas.xmlsoap.org/soap/envelope/
test -f soapenc.xsd || wget -O soapenc.xsd http://schemas.xmlsoap.org/soap/encoding/
test -f wsdl.xsd || wget -O wsdl.xsd http://schemas.xmlsoap.org/wsdl/
test -f soapbind.xsd || wget -O soapbind.xsd http://schemas.xmlsoap.org/wsdl/soap/
test -f httpbind.xsd || wget -O httpbind.xsd http://schemas.xmlsoap.org/wsdl/http/
test -f mimebind.xsd || wget -O mimebind.xsd http://schemas.xmlsoap.org/wsdl/mime/
test -f XMLSchema.xsd || wget http://www.w3.org/2001/XMLSchema.xsd
test -f xml.xsd || wget http://www.w3.org/2001/xml.xsd
test -f XMLSchema-hasFacetAndProperty.xsd || wget -O XMLSchema-hasFacetAndProperty.xsd http://www.w3.org/2001/XMLSchema-hasFacetAndProperty
test -f xhtml.xsd || wget http://www.w3.org/1999/xhtml.xsd
test -f kml21.xsd || wget http://code.google.com/apis/kml/schema/kml21.xsd
test -f saml-schema-assertion-2.0.xsd || wget http://docs.oasis-open.org/security/saml/v2.0/saml-schema-assertion-2.0.xsd
test -f saml-schema-protocol-2.0.xsd || wget http://docs.oasis-open.org/security/saml/v2.0/saml-schema-protocol-2.0.xsd
test -f xmldsig-core-schema.xsd || wget http://www.w3.org/TR/2002/REC-xmldsig-core-20020212/xmldsig-core-schema.xsd
test -f xenc-schema.xsd || wget http://www.w3.org/TR/2002/REC-xmlenc-core-20021210/xenc-schema.xsd
