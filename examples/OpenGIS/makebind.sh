if [ ! -f SCHEMAS_OPENGIS_NET.tgz ] ; then
  wget http://schemas.opengis.net/SCHEMAS_OPENGIS_NET.tgz
fi
if [ ! -d Schemas ] ; then
  rm -rf Schemas
  mkdir Schemas
  echo "Unpacking schemas"
  ( cd Schemas ; tar xzf ../SCHEMAS_OPENGIS_NET.tgz )
fi
