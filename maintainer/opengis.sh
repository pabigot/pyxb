DEST=pyxb/bundles/opengis
SCHEMA_DIR=${DEST}/schemas
rm -rf ${DEST}/raw
MODULE_PREFIX=`echo ${DEST} | sed -e s@/@.@g`

export PYXB_ARCHIVE_PATH=pyxb/bundles/opengis//:+
PYXB_ROOT=${PYXB_ROOT:-/home/pab/pyxb/dev}
export PYTHONPATH=${PYXB_ROOT}
export PATH=${PYXB_ROOT}/scripts:${PATH}

(
mkdir -p ${SCHEMA_DIR}
cd ${SCHEMA_DIR} ; 
if [ ! -d gml ] ; then
  rm -rf [a-z]*
fi
if [ ! -f SCHEMAS_OPENGIS_NET.tgz ] ; then
  wget http://schemas.opengis.net/SCHEMAS_OPENGIS_NET.tgz
fi
if [ ! -d gml ] ; then
  echo "Unpacking schemas"
  tar xzf SCHEMAS_OPENGIS_NET.tgz
fi
)

find ${DEST} -name '*.wxs' | xargs rm -f

failure () {
  echo "Failed: ${@}"
  exit 1
}

pyxbgen \
  --schema-location=${SCHEMA_DIR}/citygml/xAL/xAL.xsd --module=xAL \
  --module-prefix=pyxb.bundles.opengis.misc \
  --write-for-customization \
  --archive-to-file=${DEST}/misc/xAL.wxs \
 || failure xAL

pyxbgen \
  --schema-location=${SCHEMA_DIR}/xlink/1.0.0/xlinks.xsd --module=xlinks \
  --module-prefix=pyxb.bundles.opengis.misc \
  --write-for-customization \
  --archive-to-file=${DEST}/misc/xlinks.wxs \
 || failure xlinks

pyxbgen \
  --schema-location=${SCHEMA_DIR}/gml/3.2.1/gml.xsd --module=gml_3_2 \
  --schema-location=${SCHEMA_DIR}/iso/19139/20070417/gmd/gmd.xsd --module=iso19139.gmd \
  --schema-location=${SCHEMA_DIR}/iso/19139/20070417/gts/gts.xsd --module=iso19139.gts \
  --schema-location=${SCHEMA_DIR}/iso/19139/20070417/gsr/gsr.xsd --module=iso19139.gsr \
  --schema-location=${SCHEMA_DIR}/iso/19139/20070417/gss/gss.xsd --module=iso19139.gss \
  --schema-location=${SCHEMA_DIR}/iso/19139/20070417/gco/gco.xsd --module=iso19139.gco \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/iso19139/core.wxs \
 || failure gml_3_2
  
pyxbgen \
  --schema-location=${SCHEMA_DIR}/iso/19139/20070417/gmx/gmx.xsd --module=gmx \
  --module-prefix=pyxb.bundles.opengis.iso19139 \
  --write-for-customization \
  --archive-to-file=${DEST}/iso19139/gmx.wxs \
 || failure gmx

# Includes smil20, smil20lang
pyxbgen \
  --schema-location=${SCHEMA_DIR}/gml/3.1.1/base/gml.xsd --module=gml \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/gml.wxs \
 || failure gml

pyxbgen \
  --schema-location=${SCHEMA_DIR}/filter/1.1.0/filter.xsd --module=filter \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/filter.wxs \
 || failure filter

pyxbgen \
  --schema-location=${SCHEMA_DIR}/sweCommon/1.0.0/swe.xsd --module=swe_1_0_0 \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/swe_1_0_0.wxs \
 || failure swe_1_0_0
  
pyxbgen \
  --schema-location=${SCHEMA_DIR}/sweCommon/1.0.1/swe.xsd --module=swe_1_0_1 \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/swe_1_0_1.wxs \
 || failure swe_1_0_1
  
pyxbgen \
  --schema-location=${SCHEMA_DIR}/citygml/1.0/cityGMLBase.xsd --module=base \
  --module-prefix=pyxb.bundles.opengis.citygml \
  --write-for-customization \
  --archive-to-file=${DEST}/citygml/base.wxs \
 || failure citygml
  
pyxbgen \
  --schema-location=${SCHEMA_DIR}/kml/2.2.0/ogckml22.xsd --module=ogckml22 \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/ogckml22.wxs \
 || failure ogckml22

pyxbgen \
  --schema-location=${SCHEMA_DIR}/ic/2.1/IC-ISM-v2.1.xsd --module=ic_ism_2_1 \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/ic_ism_2_1.wxs \
 || failure ic_ism_2_1

pyxbgen \
  --schema-location=${SCHEMA_DIR}/sensorML/1.0.1/sensorML.xsd --module=sensorML_1_0_1 \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/sensorML_1_0_1.wxs \
 || failure sensorML_1_0_1

pyxbgen \
  --schema-location=${SCHEMA_DIR}/ows/1.0.0/owsAll.xsd --module=ows \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/ows.wxs \
 || failure ows

pyxbgen \
  --schema-location=${SCHEMA_DIR}/ows/1.1.0/owsAll.xsd --module=ows_1_1 \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/ows_1_1.wxs \
 || failure ows_1_1

pyxbgen \
  --schema-location=${SCHEMA_DIR}/om/1.0.0/om.xsd --module=om_1_0 \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/om_1_0.wxs \
 || failure om_1_0

# Conflicts with filter's definition of ogc
pyxbgen \
  --schema-location=${SCHEMA_DIR}/sos/1.0.0/sosAll.xsd --module=sos_1_0 \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --pre-load-archive=${DEST}/filter.wxs \
  --archive-to-file=${DEST}/sos_1_0.wxs \
 || failure sos_1_0

pyxbgen \
  --schema-location=${SCHEMA_DIR}/sampling/1.0.0/sampling.xsd --module=sampling_1_0 \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/sampling_1_0.wxs \
 || failure sampling_1_0

# Conflicts with sos + filter
pyxbgen \
  --schema-location=${SCHEMA_DIR}/tml/1.0.0/tml.xsd --module=tml \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/tml.wxs \
 || failure tml

pyxbgen \
  --schema-location=${SCHEMA_DIR}/wfs/1.1.0/wfs.xsd --module=wfs \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/wfs.wxs \
 || failure wfs

pyxbgen \
  --schema-location=${SCHEMA_DIR}/wcs/1.1/wcsAll.xsd --module=wcs_1_1 \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/wcs_1_1.wxs \
 || failure wcs_1_1

# NB: Uses a special (private) version of Dublin Core
pyxbgen \
  --schema-location=${SCHEMA_DIR}/csw/2.0.2/record.xsd --module=csw_2_0_2 \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/csw_2_0_2.wxs \
 || failure csw_2_0_2

# This supports the simplified features variants of GML, which have
# three levels (0, 1, and 2).  Need ability to prefer a specific
# namespace archive to make use of this.
pyxbgen \
  --schema-location=${SCHEMA_DIR}/gml/3.1.1/profiles/gmlsfProfile/1.0.0/gmlsfLevels.xsd --module=gmlsf \
  --module-prefix=pyxb.bundles.opengis \
  --write-for-customization \
  --archive-to-file=${DEST}/gmlsf.wxs \
 || failure gmlsf

# Can't do context: depends on gml 2.x, and we don't support version
# identification in namespace archives yet.
# Actually, we do now, I just haven't bothered updating this
#pyxbgen \
#  --schema-location=${SCHEMA_DIR}/context/1.1.0/context.xsd --module=context \
#  --module-prefix=pyxb.bundles.opengis \
#  --archive-to-file=${DEST}/context.wxs

# Get the gazetteer application profile package here:
#   http://portal.opengeospatial.org/files/index.php?artifact_id=15529
# This presents a license agreement you need to click OK on, so you'll
# have to retrieve it by browser, then unpack it into a Gazetteer
# directory here.

(cd ${SCHEMA_DIR}/citygml ; ls */1.0/*.xsd ) \
 | cut -d/ -f1,3 \
 | tr '/' ' ' \
 | while read module xsd ; do
    pyxbgen \
     --schema-location=${SCHEMA_DIR}/citygml/${module}/1.0/${xsd} --module=${module} \
     --module-prefix=pyxb.bundles.opengis.citygml \
     --write-for-customization \
     --archive-to-file=${DEST}/citygml/${module}.wxs \
    || failure citygml ${module}
 done

