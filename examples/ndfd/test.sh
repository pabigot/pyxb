#!/bin/sh

: ${PYXB_TEST_ROOT:=${PYXB_ROOT}/tests}
. ${PYXB_TEST_ROOT}/support.sh

PYXB_ARCHIVE_PATH="&pyxb/bundles/wssplat//"
export PYXB_ARCHIVE_PATH

sh genbindings.sh || fail generating bindings

python showreq.py > showreq.out || fail showreq
cmp showreq.out showreq.expected || fail request comparison
# The NWS servers may throttle this; expect it to take no more than 30
# s
echo "Wait for forecast to be retrieved..."
date
python forecast.py > forecast.out || fail forecast
date
cat forecast.out
passed
