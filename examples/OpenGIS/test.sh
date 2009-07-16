export PYXB_ARCHIVE_PATH=opengis:opengis/misc:opengis/citygml:opengis/iso19139:+
PYXB_ROOT=../..
export PYTHONPATH=${PYXB_ROOT}:.
export PATH=${PYXB_ROOT}/scripts:${PATH}

if [ ! -d opengis ] ; then
  sh makebind.sh
fi

python demo.py || exit 1
#python check_sos.py Schemas/sos/1.0.0/examples/*.xml

rm gmlapp.py raw/gmlapp.py
pyxbgen \
  --schema-location=gmlapp.xsd --module=gmlapp \
  --write-for-customization
python testgml.py
  
