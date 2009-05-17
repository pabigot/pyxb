PYTHONPATH=../..
export PYTHONPATH

URI='http://schemas.opengis.net/kml/2.2.0/ogckml22.xsd'
PREFIX='ogckml'

mkdir -p raw
touch raw/__init__.py

# Hack until we get relative URI handling into the import routine
../../scripts/genbind \
   -u 'http://schemas.opengis.net/kml/2.2.0/atom-author-link.xsd' \
   -p atom \
   -r -C
../../scripts/genbind \
   -u 'http://docs.oasis-open.org/election/external/xAL.xsd' \
   -p xAL \
   -r -C

PYXB_NAMESPACE_PATH='raw:+'
export PYXB_NAMESPACE_PATH

# NB: If you add -C to this, Python will blow up from the bug about
# pickling heavily recursive structures.  Fortunately, we don't need
# the content model.
../../scripts/genbind \
   -u "${URI}" \
   -p "${PREFIX}" \
   -r

# Except that we do need the content model for Google's extensions.
# So this one has to be disabled.
#../../scripts/genbind \
#   -u 'http://code.google.com/apis/kml/schema/kml22gx' \
#   -p gx \
#   -r

for f in atom xAL ${PREFIX} gx ; do
  if [ ! -f ${f}.py ] ; then
    echo "from raw.${f} import *" > ${f}.py
  fi
done
