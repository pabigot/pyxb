#!/bin/sh

. ${PYXB_ROOT}/tests/support.sh

xmllint --schema custom.xsd test.xml || fail Test document is not valid

rm -rf raw *.pyc
pyxbgen \
    -m custom \
    -u custom.xsd \
    --write-for-customization \
    || fail generating bindings
python tst-normal.py || fail Normal customization failed
python tst-introspect.py || fail Introspection customization failed
passed
