export PYXB_ARCHIVE_PATH=opengis//:+
PYXB_ROOT=../..
export PYTHONPATH=${PYXB_ROOT}:.
export PATH=${PYXB_ROOT}/scripts:${PATH}

if [ ! -d opengis ] ; then
  sh makebind.sh
fi

python demo.py || exit 1

# sosRegisterSensor.xml uses tml:tcfTrigger, but the element is really named tml:cfTrigger
# Skip testing it since it will fail to validate thereby confusing the viewer.
ls Schemas/sos/1.0.0/examples/*.xml \
 | grep -v sosRegisterSensor \
 | xargs python check_sos.py \
|| exit 1

rm gmlapp.py raw/gmlapp.py
pyxbgen \
  --schema-location=gmlapp.xsd --module=gmlapp \
  --write-for-customization
python testgml.py
