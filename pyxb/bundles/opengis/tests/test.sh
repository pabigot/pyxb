PYXB_ROOT=${PYXB_ROOT:-/home/pab/pyxb/dev}
BUNDLE_ROOT=${PYXB_ROOT}/pyxb/bundles/opengis
SCHEMA_DIR=${BUNDLE_ROOT}/schemas

PYTHONPATH=${PYXB_ROOT}:.
PATH=${PYXB_ROOT}/scripts:/usr/bin:/bin
export PATH PYTHONPATH

failure () {
  echo "Failed: ${@}"
  exit 1
}

python demo.py || exit 1

# sosRegisterSensor.xml uses tml:tcfTrigger, but the element is really named tml:cfTrigger
# Skip testing it since it will fail to validate thereby confusing the viewer.
ls ${SCHEMA_DIR}/sos/1.0.0/examples/*.xml \
 | grep -v sosRegisterSensor \
 | xargs python check_sos.py \
|| exit 1

rm -f gmlapp.py raw/gmlapp.py
pyxbgen \
  --archive-path=${BUNDLE_ROOT}/raw \
  --schema-location=gmlapp.xsd --module=gmlapp \
  --write-for-customization
python testgml.py
