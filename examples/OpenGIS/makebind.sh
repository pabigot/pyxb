export PYXB_ARCHIVE_PATH=opengis:opengis/misc:opengis/citygml:opengis/iso19139:+
PYXB_ROOT=${PYXB_ROOT:-../..}
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

pyxbgen \
  --schema-location=Schemas/citygml/xAL/xAL.xsd --module=xAL \
  --module-prefix=opengis.misc \
  --archive-file=opengis/misc/xAL.wxs

pyxbgen \
  --schema-location=Schemas/gml/3.2.1/gml.xsd --module=gml_3_2 \
  --schema-location=Schemas/iso/19139/20070417/gmd/gmd.xsd --module=iso19139.gmd \
  --schema-location=Schemas/iso/19139/20070417/gts/gts.xsd --module=iso19139.gts \
  --schema-location=Schemas/iso/19139/20070417/gsr/gsr.xsd --module=iso19139.gsr \
  --schema-location=Schemas/iso/19139/20070417/gss/gss.xsd --module=iso19139.gss \
  --schema-location=Schemas/iso/19139/20070417/gco/gco.xsd --module=iso19139.gco \
  --module-prefix=opengis \
  --archive-file=opengis/iso19139/core.wxs
  
pyxbgen \
  --schema-location=Schemas/iso/19139/20070417/gmx/gmx.xsd --module=gmx \
  --module-prefix=opengis.iso19139 \
  --archive-file=opengis/iso19139/gmx.wxs

# Includes smil20, smil20lang, xlink
pyxbgen \
  --schema-location=Schemas/gml/3.1.1/base/gml.xsd --module=gml \
  --module-prefix=opengis \
  --archive-file=opengis/gml.wxs

pyxbgen \
  --schema-location=Schemas/sweCommon/1.0.0/swe.xsd --module=swe_1_0_0 \
  --module-prefix=opengis \
  --archive-file=opengis/swe_1_0_0.wxs
  
pyxbgen \
  --schema-location=Schemas/sweCommon/1.0.1/swe.xsd --module=swe_1_0_1 \
  --module-prefix=opengis \
  --archive-file=opengis/swe_1_0_1.wxs
  
pyxbgen \
  --schema-location=Schemas/citygml/1.0/cityGMLBase.xsd --module=base \
  --module-prefix=opengis.citygml \
  --archive-file=opengis/citygml/base.wxs
  
(cd Schemas/citygml ; ls */1.0/*.xsd ) \
 | cut -d/ -f1,3 \
 | tr '/' ' ' \
 | while read module xsd ; do
    pyxbgen \
     --schema-location=Schemas/citygml/${module}/1.0/${xsd} --module=${module} \
     --module-prefix=opengis.citygml \
     --archive-file=opengis/citygml/${module}.wxs
 done

pyxbgen \
  --schema-location=Schemas/kml/2.2.0/ogckml22.xsd --module=ogckml22 \
  --module-prefix=opengis \
  --archive-file=opengis/ogckml22.wxs

pyxbgen \
  --schema-location=Schemas/ic/2.1/IC-ISM-v2.1.xsd --module=ic_ism_2_1 \
  --module-prefix=opengis \
  --archive-file=opengis/ic_ism_2_1.wxs

pyxbgen \
  --schema-location=Schemas/sensorML/1.0.1/sensorML.xsd --module=sensorML_1_0_1 \
  --module-prefix=opengis \
  --archive-file=opengis/sensorML_1_0_1.wxs

pyxbgen \
  --schema-location=Schemas/ows/1.1.0/owsAll.xsd --module=ows_1_1 \
  --module-prefix=opengis \
  --archive-file=opengis/ows_1_1.wxs

pyxbgen \
  --schema-location=Schemas/sos/1.0.0/sosAll.xsd --module=sos_1_0 \
  --module-prefix=opengis \
  --archive-file=opengis/sos_1_0.wxs

pyxbgen \
  --schema-location=Schemas/sampling/1.0.0/sampling.xsd --module=sampling_1_0 \
  --module-prefix=opengis \
  --archive-file=opengis/sampling_1_0.wxs

pyxbgen \
  --schema-location=Schemas/tml/1.0.0/tml.xsd --module=tml \
  --module-prefix=opengis \
  --archive-file=opengis/tml.wxs

# Can't do context: depends on gml 2.x, and we don't support version
# identification in namespace archives yet.
#pyxbgen \
#  --schema-location=Schemas/context/1.1.0/context.xsd --module=context \
#  --module-prefix=opengis \
#  --archive-file=opengis/context.wxs

