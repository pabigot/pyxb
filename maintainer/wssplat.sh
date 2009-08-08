DEST=pyxb/bundles/wssplat
SCHEMA_DIR=${DEST}/schemas
rm -rf ${DEST}/raw
MODULE_PREFIX=`echo ${DEST} | sed -e s@/@.@g`

mkdir -p ${DEST}/raw
touch ${DEST}/raw/__init__.py
mkdir -p ${SCHEMA_DIR}

( cat <<EOList
http://schemas.xmlsoap.org/wsdl/ wsdl11
http://www.w3.org/2002/ws/desc/ns/wsdl20.xsd wsdl20
http://schemas.xmlsoap.org/ws/2003/03/business-process/ bpws
http://schemas.xmlsoap.org/wsdl/http/ httpbind
http://schemas.xmlsoap.org/wsdl/mime/ mimebind
http://schemas.xmlsoap.org/soap/envelope/ soap11
http://www.w3.org/2003/05/soap-envelope/ soap12
http://schemas.xmlsoap.org/wsdl/soap/ soapbind11
http://schemas.xmlsoap.org/wsdl/soap12/wsdl11soap12.xsd soapbind12
http://www.w3.org/2002/ws/desc/ns/http.xsd whttp
http://www.w3.org/TR/xmldsig-core/xmldsig-core-schema.xsd ds
http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd wsu
http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd wsse
http://www.w3.org/2002/ws/policy/ns/ws-policy wsp
http://www.w3.org/2006/07/ws-policy.xsd wsp200607
http://www.w3.org/2002/ws/addr/ns/ws-addr wsa
http://www.w3.org/2002/ws/addr/ns/ws-addr-metadata wsam
http://www.w3.org/2002/ws/desc/ns/soap.xsd wsoap
http://docs.oasis-open.org/ws-tx/wscoor/2006/06/wstx-wscoor-1.1-schema-200701.xsd wscoor
http://www.w3.org/2002/ws/desc/ns/wsdl-instance.xsd wsdli
http://www.w3.org/2002/ws/desc/ns/wsdl-extensions.xsd wsdlx
EOList
) | sed -e '/^#/d' \
  | while read uri prefix auxflags ; do
  cached_schema=${SCHEMA_DIR}/${prefix}.xsd
  if [ ! -f ${cached_schema} ] ; then
     echo "Retrieving ${prefix} from ${uri}"
     wget -O ${cached_schema} ${uri}
  fi
  echo
  echo "Translating to ${prefix} from ${cached_schema}"
  scripts/pyxbgen \
    ${auxflags} \
    --archive-path=${DEST}/raw:+ \
    --schema-location file:${cached_schema} \
    --module=${prefix} \
    --module-prefix=${MODULE_PREFIX} \
    --write-for-customization \
    --archive-to-file=${DEST}/raw/${prefix}.wxs
  if [ 0 != $? ] ; then
    break
  fi
  #scripts/pyxbdump ${DEST}/raw/${prefix}.wxs
done
