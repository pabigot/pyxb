PYTHONPATH=../..
export PYTHONPATH
URI='http://www.weather.gov/forecasts/xml/DWMLgen/schema/DWML.xsd'
PREFIX='DWML'
WSDL="${PREFIX}.wsdl"
if [ ! -f ${WSDL} ] ; then
  wget -O ${WSDL} "${URI}"
fi

mkdir -p raw
touch raw/__init__.py
../../scripts/genbind \
   -m '' \
   -p "${PREFIX}" \
   -u "${WSDL}" \
   -r 
if [ ! -f ${PREFIX}.py ] ; then
  echo "from raw.${PREFIX} import *" > ${PREFIX}.py
fi
