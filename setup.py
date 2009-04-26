from distutils.core import setup

# Require Python 2.4

setup(name='PyXB',
      description = 'Python W3C XML Schema Bindings',
      author='Peter A. Bigot',
      author_email='pyxb@comcast.net',
      url='http://home.comcast.net/~pyxb',
      version='0.1.3',
      packages=[ 'pyxb', 'pyxb.binding', 'pyxb.utils', 'pyxb.xmlschema', 'pyxb.standard.bindings' ],
      data_files= [ ('pyxb/standard/schemas', [ '*.xsd' ] ) ],
      scripts=[ 'scripts/genbind' ])
      
