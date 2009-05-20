PYTHONPATH=../..
export PYTHONPATH
URI='http://services.aonaware.com/DictService/DictService.asmx?WSDL'
PREFIX='dict'
WSDL="${PREFIX}.wsdl"
if [ ! -f ${WSDL} ] ; then
  wget -O ${WSDL} "${URI}"
fi

mkdir -p raw
touch raw/__init__.py
../../scripts/pyxbgen \
   -m '' \
   -p "${PREFIX}" \
   -u "${WSDL}" \
   -r -W
if [ ! -f ${PREFIX}.py ] ; then
  echo "from raw.${PREFIX} import *" > ${PREFIX}.py
fi
