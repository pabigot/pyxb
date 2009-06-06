PYTHONPATH=../..
export PYTHONPATH
URI='http://docs.tms.tribune.com/tech/xml/schemas/tmsxtvd.xsd'
PREFIX='tmstvd'

mkdir -p raw
touch raw/__init__.py
../../scripts/pyxbgen \
   -m "${PREFIX}" \
   -u "${URI}" \
   -r --write-schema-path .
if [ ! -f ${PREFIX}.py ] ; then
  echo "from raw.${PREFIX} import *" > ${PREFIX}.py
fi

if [ ! -f tmsdatadirect_sample.xml ] ; then
  wget http://tmsdatadirect.com/docs/tv/tmsdatadirect_sample.xml
fi
