#!/bin/sh

: ${PYXB_TEST_ROOT:=${PYXB_ROOT}/tests}
. ${PYXB_TEST_ROOT}/support.sh

TEST_URI=http://www.w3.org/People/mimasa/test/xhtml/media-types/test.xhtml

if [ ! -f in.xhtml ] ; then
  wget -O in.xhtml ${TEST_URI} || fail retrieving document
fi
python rewrite.py || fail rewriting document

xmllint --format in.xhtml > inf.xhtml
xmllint --format out.xhtml > outf.xhtml
diff -uw inf.xhtml outf.xhtml > deltas || true

# Need to manually validate that outf.xhtml and in.xhtml are about the
# same.  The rewrite does not preserve the order of attributes in the
# elements.
echo "See deltas for differences"

# Test most primitive generation of documents
rm -f genout.xhtml
python generate.py > genout.xhtml || fail running
passed
