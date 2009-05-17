PYTHONPATH=../..
export PYTHONPATH
URI='http://docs.tms.tribune.com/tech/xml/schemas/tmsxtvd.xsd'
PREFIX='tmstvd'
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
if [ ! -f tmsdatadirect_sample.xml ] ; then
  wget http://tmsdatadirect.com/docs/tv/tmsdatadirect_sample.xml
fi
