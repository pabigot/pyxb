PYTHONPATH=../..
rm -rf bindings
mkdir bindings
PYXB_NAMESPACE_PATH='bindings:../../pyxb/standard/bindings'
export PYXB_NAMESPACE_PATH

../../scripts/genbind ../schemas/shared-types.xsd bindings st
../../scripts/genbind ../schemas/test-external.xsd bindings te
OFN=test-stored-$$.py
cat >>${OFN} <<EOText
import pyxb.Namespace
print "\n".join(pyxb.Namespace.AvailableForLoad())
ns = pyxb.Namespace.NamespaceForURI('URN:test-external', True)
ns.validateSchema()
EOText
python ${OFN}
rm -f ${OFN}
