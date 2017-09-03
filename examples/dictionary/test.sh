#!/bin/sh

: ${PYXB_TEST_ROOT:=${PYXB_ROOT}/tests}
. ${PYXB_TEST_ROOT}/support.sh

sh genbindings.sh || fail generating bindings
python showdict.py > showdict.out || fail running
cmp showdict.out showdict.expected || fail output comparison
passed
