PYTHONPATH=../..
export PYTHONPATH

GEO_WSDL_URI='http://geocoder.us/dist/eg/clients/GeoCoder.wsdl'
GEO_PREFIX=GeoCoder
GEO_WSDL="${GEO_PREFIX}.wsdl"

if [ ! -f ${GEO_WSDL} ] ; then
  wget -O ${GEO_WSDL} "${GEO_WSDL_URI}"
  patch -p0 < ${GEO_WSDL}-patch
fi

mkdir -p raw
touch raw/__init__.py

../../scripts/pyxbgen \
  -u ${GEO_WSDL} \
  -m ${GEO_PREFIX} \
  -r -W
if [ ! -f ${GEO_PREFIX}.py ] ; then
  echo "from raw.${GEO_PREFIX} import *" > ${GEO_PREFIX}.py
fi  
  
