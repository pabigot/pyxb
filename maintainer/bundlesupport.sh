if [ ! "${BUNDLE_TAG}" ] ; then
  echo 1>&2 "ERROR: Must set BUNDLE_TAG environment variable (should set PYXB_ROOT as well)"
  exit 1
fi

BUNDLE_TAG=${BUNDLE_TAG:-core}

PYXB_ROOT=${PYXB_ROOT:-/home/pab/pyxb/dev}
MODULE_PREFIX=pyxb.bundles.${BUNDLE_TAG}
BUNDLE_ROOT=${PYXB_ROOT}/pyxb/bundles/${BUNDLE_TAG}
SCHEMA_DIR=${BUNDLE_ROOT}/schemas
RAW_DIR=${BUNDLE_ROOT}/raw
rm -rf ${RAW_DIR}
mkdir -p ${RAW_DIR}
touch ${RAW_DIR}/__init__.py
mkdir -p ${SCHEMA_DIR}

PYTHONPATH=${PYXB_ROOT}
PATH=${PYXB_ROOT}/scripts:/usr/bin:/bin
export PATH PYTHONPATH

generateBindings () {
  sed -e '/^#/d' \
    | while read uri prefix auxflags ; do
    cached_schema=${SCHEMA_DIR}/${prefix}.xsd
    if [ ! -f ${cached_schema} ] ; then
       echo "Retrieving ${prefix} from ${uri}"
       wget -O ${cached_schema} ${uri}
    fi
    echo
    echo "Translating to ${prefix} from ${cached_schema}"
    pyxbgen \
      ${auxflags} \
      --schema-location file:${cached_schema} \
      --module=${prefix} \
      --module-prefix=${MODULE_PREFIX} \
      --write-for-customization \
      --archive-path=${RAW_DIR}:+ \
      --archive-to-file=${RAW_DIR}/${prefix}.wxs
    if [ 0 != $? ] ; then
      break
    fi
  done
}

  
