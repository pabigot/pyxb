import sys
import pyxb.xmlschema
import pyxb.binding.generate
import pyxb.utils.domutils

files = sys.argv[1:]
if 0 == len(files):
    files = [ 'pyxb/standard/schemas/XMLSchema.xsd' ]

rv = pyxb.binding.generate.GeneratePython(schema_location=files[0], generate_facets=True)
print '''# ---------
%s
# -------------''' % (rv,)
