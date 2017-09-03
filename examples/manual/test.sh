#!/bin/sh

: ${PYXB_TEST_ROOT:=${PYXB_ROOT}/tests}
. ${PYXB_TEST_ROOT}/support.sh

rm -f *.wxs po?.py *.pyc

sh demo1.sh || fail building demo1
python demo1.py > demo1.out || fail running demo1
cat demo1.out
cmp demo1.out demo.expected || fail demo1 output check

sh demo2.sh || fail building demo2
python demo2.py > demo2.out || fail running demo2
cat demo2.out
cmp demo2.out demo.expected || fail demo2 output check

sh demo3a.sh || fail building demo3a
python demo3.py > demo3a.out || fail running demo3a
cat demo3a.out
cmp demo3a.out demo.expected || fail demo3a output check

sh demo3b.sh || fail building demo3b
python demo3.py > demo3b.out || fail running demo3 variant b
cat demo3b.out
cmp demo3b.out demo.expected || fail demo3b output check

sh demo3c1.sh || fail building demo3c1
sh demo3c2.sh || fail building demo3c2
python demo3.py > demo3c.out || fail running demo3c
cat demo3c.out
cmp demo3c.out demo.expected || fail demo3c output check

sh demo4.sh || fail building demo4

python demo4a.py > demo4a.out || fail running demo4a
cat demo4a.out
cmp demo4a.out demo4.expected || fail demo4a output check

# This one displays an error which we capture and verify
python demo4a1.py 2>demo4a1.err 1>demo4a1.out || true
test -s demo4a1.out && fail demo4a1 stdout check
# Do output comparison without checking line numbers in trace
cat demo4a1.err \
    | sed -r \
        -e "s@${PYXB_ROOT}@PYXB_ROOT@g" \
	-e 's@line [0-9]+@line #@' \
    > demo4a1.errc
cmp demo4a1.errc demo4a1.expected || fail demo4a1 error check

python demo4a2.py > demo4a2.out || fail running demo4a2
cat demo4a2.out
cmp demo4a2.out demo4.expected || fail demo4a2 output check

sh demo4b.sh || fail building demo4b
python demo4b.py > demo4b.out || fail running demo4b
cat demo4b.out
cmp demo4b.out demo4.expected || fail demo4b output check

# 4c disables validation on output, so comparison is not
# reliable.
for dc in 4c1 4c2 4c3 ; do
    python demo${dc}.py | xmllint --format - > demo${dc}.out
    cmp demo${dc}.out demo${dc}.expected || fail demo${dc} output check
done
python badcontent.py > badcontent.out || fail running badcontent
cat badcontent.out
cmp badcontent.out badcontent.expected || fail badcontent output check

passed
