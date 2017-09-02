#!/bin/sh

. ${PYXB_ROOT}/tests/support.sh

rm -f content.py
pyxbgen \
    -u content.xsd -m content \
    || fail generating bindings
python showcontent.py > test.out || fail running
cmp test.out test.expected || fail output comparison
passed
