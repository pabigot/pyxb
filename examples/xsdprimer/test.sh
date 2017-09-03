#!/bin/sh

: ${PYXB_TEST_ROOT:=${PYXB_ROOT}/tests}
. ${PYXB_TEST_ROOT}/support.sh

sh genbindings.sh || fail generating bindings
python demo.py > demo.out || fail running demo
cmp demo.out demo.expected || fail demo output mismatch

passed
