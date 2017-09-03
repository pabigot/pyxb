#!/bin/sh

: ${PYXB_TEST_ROOT:=${PYXB_ROOT}/tests}
. ${PYXB_TEST_ROOT}/support.sh

rm -f content.py
pyxbgen \
    -u content.xsd -m content \
    || fail generating bindings
python showcontent.py > test.out || fail running
cmp test.out test.expected || fail output comparison
passed
