PYXB_ROOT=${PYXB_ROOT:-../..}
export PYXB_ARCHIVE_PATH=${PYXB_ROOT}/pyxb/bundles/opengis//:+
export PYTHONPATH=${PYXB_ROOT}
export PATH=${PYXB_ROOT}/scripts:${PATH}
if [ ! -f SCHEMAS_OPENGIS_NET.tgz ] ; then
  wget http://schemas.opengis.net/SCHEMAS_OPENGIS_NET.tgz
fi
if [ ! -d Schemas ] ; then
  rm -rf Schemas
  mkdir Schemas
  echo "Unpacking schemas"
  ( cd Schemas ; tar xzf ../SCHEMAS_OPENGIS_NET.tgz )
fi

failure () {
  echo "Failed: ${@}"
  exit 1
}

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
