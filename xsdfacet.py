import sys
import PyWXSB.generate

files = sys.argv[1:]
if 0 == len(files):
    files = [ 'schemas/XMLSchema.xsd' ]

rv = PyWXSB.generate.GeneratePython(files[0], generate_facets=True)
print '''# ---------
%s
# -------------''' % (rv,)
