PYTHONPATH=../..
rm -rf bindings
mkdir bindings
PYXB_NAMESPACE_PATH='bindings:../../pyxb/standard/bindings'

../../scripts/genbind ../schemas/shared-types.xsd bindings st
../../scripts/genbind ../schemas/test-external.xsd bindings te
