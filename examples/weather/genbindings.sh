URI='http://ws.cdyne.com/WeatherWS/Weather.asmx?wsdl'
PREFIX='weather'
WSDL="${PREFIX}.wsdl"
if [ ! -f ${WSDL} ] ; then
  wget -O ${WSDL} "${URI}"
fi

rm -rf raw weather.pyc weather.py
mkdir -p raw
touch raw/__init__.py
pyxbgen \
   -m "${PREFIX}" \
   -W "${WSDL}" \
   -r \
 || ( echo "Failed to generate bindings" ; exit 1 )
