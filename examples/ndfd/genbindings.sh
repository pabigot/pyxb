PYTHONPATH=../..
export PYTHONPATH
URI='http://www.weather.gov/forecasts/xml/DWMLgen/schema/DWML.xsd'
PREFIX='DWML'

rm -rf raw
mkdir -p raw
touch raw/__init__.py
../../scripts/pyxbgen \
   -u "${URI}" \
   -m "${PREFIX}" \
   -r --write-schema-path .
if [ ! -f ${PREFIX}.py ] ; then
  echo "from raw.${PREFIX} import *" > ${PREFIX}.py
fi

# Retrieve the wsdl.  Heck, show it off even.  Just not using it yet.
WSDL_URI='http://www.weather.gov/forecasts/xml/DWMLgen/wsdl/ndfdXML.wsdl'
if [ ! -f ndfdXML.wsdl ] ; then
  wget ${WSDL_URI}
fi
../../scripts/pyxbgen \
   -u "${WSDL_URI}" \
   -m ndfd \
   -r -W

../../scripts/pyxbwsdl file:ndfdXML.wsdl

# Get an example query
if [ ! -f NDFDgen.xml ] ; then
  wget http://www.weather.gov/forecasts/xml/docs/SOAP_Requests/NDFDgen.xml
fi
