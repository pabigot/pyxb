#!/bin/sh

. ${PYXB_ROOT}/tests/support.sh

sh genbindings.sh || fail generating bindings
python demo.py > demo.out || fail running demo
cmp demo.out demo.expected || fail demo output mismatch

passed
