PYTHONPATH=../..
rm -rf bindings
mkdir bindings
PYXB_NAMESPACE_PATH='bindings:+'
export PYXB_NAMESPACE_PATH

../../scripts/pyxbgen --schema-uri ../schemas/shared-types.xsd --module-path bindings.st --save-component-model
../../scripts/pyxbgen --schema-uri ../schemas/test-external.xsd --module-path bindings.te --save-component-model
OFN=test-stored-$$.py
cat >>${OFN} <<EOText
import pyxb
print "\n".join(pyxb.namespace.AvailableForLoad())
ns = pyxb.namespace.NamespaceForURI('URN:shared-types', True)
ns.validateComponentModel()
ns = pyxb.namespace.NamespaceForURI('URN:test-external', True)
ns.validateComponentModel()
EOText
python ${OFN}
rm -f ${OFN}
