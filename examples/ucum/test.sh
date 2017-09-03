#!/bin/sh

: ${PYXB_TEST_ROOT:=${PYXB_ROOT}/tests}
. ${PYXB_TEST_ROOT}/support.sh

pyxbgen \
  -u ucum-essence.xsd \
  -m ucum \
 || fail generating bindings

if [ ! -f ucum-essence.xml ] ; then
    wget http://unitsofmeasure.org/ucum-essence.xml
fi

python showunits.py > test.out || fail running
cmp test.out test.expected || fail output mismatch
passed
