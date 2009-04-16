import sys
import pywxsb.binding.generate

files = sys.argv[1:]
if 0 == len(files):
    files = [ 'schemas/kml21.xsd' ]

rv = pywxsb.binding.generate.GeneratePython(schema_file=files[0])
print rv
