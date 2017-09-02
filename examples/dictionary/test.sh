#!/bin/sh

. ${PYXB_ROOT}/tests/support.sh

sh genbindings.sh || fail generating bindings
python showdict.py > showdict.out || fail running
cmp showdict.out showdict.expected || fail output comparison
passed
