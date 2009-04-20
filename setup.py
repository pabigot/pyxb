from distutils.core import setup

# Require Python 2.4

setup(name='PyWXSB',
      description = 'Python W3C Schema XML Bindings',
      author='Peter A. Bigot',
      author_email='pywxsb@comcast.net',
      url='http://home.comcast.net/~pabigot/pywxsb',
      version='0.1.1',
      packages=[ 'pywxsb', 'pywxsb.binding', 'pywxsb.utils', 'pywxsb.xmlschema', 'pywxsb.standard.bindings' ],
      data_files= [ ('pywxsb/standard/schemas', [ '*.xsd' ] ) ],
      scripts=[ 'scripts/genbind' ])
      
