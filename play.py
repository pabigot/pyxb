import sys
import PyWXSB.generate

files = sys.argv[1:]
if 0 == len(files):
    files = [ 'schemas/kml21.xsd' ]

rv = PyWXSB.generate.GeneratePython(files[0])
print rv
