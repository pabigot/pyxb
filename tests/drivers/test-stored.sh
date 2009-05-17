PYTHONPATH=../..
rm -rf bindings
mkdir bindings
PYXB_NAMESPACE_PATH='bindings:+'
export PYXB_NAMESPACE_PATH

../../scripts/genbind --schema-uri ../schemas/shared-types.xsd --module-path bindings --schema-prefix st --save-component-model
../../scripts/genbind --schema-uri ../schemas/test-external.xsd --module-path bindings --schema-prefix te --save-component-model
OFN=test-stored-$$.py
cat >>${OFN} <<EOText
import pyxb.Namespace
print "\n".join(pyxb.Namespace.AvailableForLoad())
ns = pyxb.Namespace.NamespaceForURI('URN:shared-types', True)
ns.validateComponentModel()
ns = pyxb.Namespace.NamespaceForURI('URN:test-external', True)
ns.validateComponentModel()
EOText
python ${OFN}
rm -f ${OFN}
