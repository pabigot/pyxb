SCHEMA_DIR=pyxb/standard/schemas
rm -rf pyxb/standard/bindings/raw
mkdir -p pyxb/standard/bindings/raw
touch pyxb/standard/bindings/raw/__init__.py
mkdir -p ${SCHEMA_DIR}

# Get a couple that we don't actually generate bindings for
test -f ${SCHEMA_DIR}/xml.xsd || wget -O ${SCHEMA_DIR}/xml.xsd http://www.w3.org/2001/xml.xsd
test -f ${SCHEMA_DIR}/XMLSchema.xsd || wget -O ${SCHEMA_DIR}/XMLSchema.xsd http://www.w3.org/2001/XMLSchema.xsd

( cat <<EOList
# NOTE: Use prefix xml_ instead of xml because xml conflicts with standard package
# This is now a builtin module, so don't generate a different one
# http://www.w3.org/2001/xml.xsd xml_ --allow-builtin-generation
# NOTE: The non-normative XMLSchema namespace defines far more than
# the public components for which we have built-in values.  The
# incompleteness of the built-ins confuses PyXB.  There's no need to
# fix this since we have a workable XSD schema built-in.
#http://www.w3.org/2001/XMLSchema.xsd xsd
http://www.w3.org/2001/XMLSchema-hasFacetAndProperty xsd_hfp --allow-builtin-generation
http://www.w3.org/1999/xhtml.xsd xhtml --allow-builtin-generation
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
    --schema-location file:${cached_schema} \
    --module=${prefix} \
    --module-prefix=pyxb.standard.bindings \
    --write-for-customization \
    --archive-to-file=pyxb/standard/bindings/raw/${prefix}.wxs
  if [ 0 != $? ] ; then
    break
  fi
  #scripts/pyxbdump pyxb/standard/bindings/raw/${prefix}.wxs
done
