#!/bin/sh

. ${PYXB_ROOT}/tests/support.sh

sh genbindings.sh || failed generating bindings
python showdict.py > showdict.out || failed running
cmp showdict.out showdict.expected || failed output comparison
passed
