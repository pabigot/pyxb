PYTHONPATH=../..
rm -rf bindings
mkdir bindings
PYXB_ARCHIVE_PATH='bindings:+'
export PYXB_ARCHIVE_PATH

../../scripts/pyxbgen --schema-location=../schemas/shared-types.xsd --module-prefix=bindings --module=st --archive-to-file=bindings/st.wxs
../../scripts/pyxbgen --schema-location=../schemas/test-external.xsd --module-prefix=bindings --module=te --archive-to-file=bindings/te.wxs
OFN=test-stored-$$.py
cat >>${OFN} <<EOText
import pyxb
print "\n".join([ str(_ns) for _ns in pyxb.namespace.AvailableNamespaces() ])
ns = pyxb.namespace.NamespaceForURI('URN:shared-types', True)
ns.validateComponentModel()
ns = pyxb.namespace.NamespaceForURI('URN:test-external', True)
ns.validateComponentModel()

import bindings.st as st
import bindings.te as te

import unittest

class ExternalTest (unittest.TestCase):
    def testUnionExtension (self):
        e = te.morewords('one')
        self.assertTrue(isinstance(e, st.english))
        w = te.morewords('un')
        self.assertTrue(isinstance(w, st.welsh))
        n = te.morewords('ichi')
        self.assertTrue(te.uMorewords._IsValidValue(n))

unittest.main()

EOText
python ${OFN}
rm -f ${OFN}
