PYXB_ROOT=${PYXB_ROOT:-../..}
export PYXB_ARCHIVE_PATH=${PYXB_ROOT}/pyxb/bundles/opengis/raw:+
export PYTHONPATH=${PYXB_ROOT}
export PATH=${PYXB_ROOT}/scripts:${PATH}

if [ ! -f dwGML.xsd ] ; then
  wget -O- 'http://www.weather.gov/forecasts/xml/OGC_services/ndfdOWSserver.php?SERVICE=WFS&Request=DescribeFeatureType&VERSION=1.1.0&TYPENAME=Forecast_GmlsfPoint,Forecast_GmlObs,NdfdMultiPointCoverage' \
    | sed -e 's@name="Forecast_GmlObs" substitutionGroup="gml:Observation"@name="Forecast_GmlObs" type="gml:ObservationType"@' \
    > dwGML.xsd
fi
pyxbgen \
  --schema-location=dwGML.xsd --module=dwGML \
  --module-prefix=ndfd

