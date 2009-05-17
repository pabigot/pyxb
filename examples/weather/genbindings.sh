PYTHONPATH=../..
export PYTHONPATH
URI='http://ws.cdyne.com/WeatherWS/Weather.asmx?wsdl'
PREFIX='weather'
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
   -r -W
if [ ! -f ${PREFIX}.py ] ; then
  echo "from raw.${PREFIX} import *" > ${PREFIX}.py
fi
