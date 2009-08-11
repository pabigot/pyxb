#!/bin/sh

failure () {
  echo "Failed: ${@}"
  exit 1
}

python demo.py || exit 1

# sosRegisterSensor.xml uses tml:tcfTrigger, but the element is really named tml:cfTrigger
# Skip testing it since it will fail to validate thereby confusing the viewer.
if [ -d ${SCHEMAS_OPENGIS_NET:-/dev/null} ] ; then
  ls ${SCHEMAS_OPENGIS_NET}/sos/1.0.0/examples/*.xml \
    | grep -v sosRegisterSensor \
    | xargs python check_sos.py \
  || exit 1
fi

rm -f gmlapp.py raw/gmlapp.py
pyxbgen \
  --schema-location=gmlapp.xsd --module=gmlapp \
  --write-for-customization
python testgml.py || exit 1

