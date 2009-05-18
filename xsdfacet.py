import sys
import pyxb.xmlschema
import pyxb.binding.generate
import pyxb.utils.domutils

files = sys.argv[1:]
if 0 == len(files):
    files = [ 'pyxb/standard/schemas/XMLSchema.xsd' ]

f = file(files[0])
doc = pyxb.utils.domutils.StringToDOM(file(files[0]).read())
wxs = pyxb.xmlschema.schema.CreateFromDOM(doc.documentElement, skip_resolution=True)
rv = pyxb.binding.generate.GeneratePython(schema=wxs, generate_facets=True)
print '''# ---------
%s
# -------------''' % (rv,)
