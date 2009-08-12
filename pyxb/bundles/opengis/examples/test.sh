#!/bin/sh

failure () {
  echo "Failed: ${@}"
  exit 1
}

python demo.py || exit 1

if test -d ${SCHEMAS_OPENGIS_NET:-/dev/null} ; then
  echo "testing nothingness"
  # sosRegisterSensor.xml uses tml:tcfTrigger, but the element is really named tml:cfTrigger
  # Skip testing it since it will fail to validate thereby confusing the viewer.
  ls ${SCHEMAS_OPENGIS_NET}/sos/1.0.0/examples/*.xml \
    | grep -v sosRegisterSensor \
    | xargs python check_sos.py \
  || exit 1
else
  echo 1>&2 "WARNING: Need SCHEMAS_OPENGIS_NET defined to test example documents"
fi

rm -f gmlapp.py* raw/gmlapp.py*
PYXB_ARCHIVE_PATH='&pyxb/bundles/opengis//'
export PYXB_ARCHIVE_PATH
pyxbgen \
  --schema-location=gmlapp.xsd --module=gmlapp \
  --write-for-customization
python testgml.py || exit 1

