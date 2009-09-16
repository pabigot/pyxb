# Run this from within ~pab/pyxb/pre-release

RELEASE=${1:-0.7.1-TEST}
PYXBREL=PyXB-${RELEASE}
TARFILE=PyXB-full-${RELEASE}.tar.gz

export LANG=en_US.UTF-8

for pv in 2.4.6 2.5.4 2.6.2 ; do
  (
  pt=python-${pv}
  pvs=`echo ${pv} | sed -e 's@..$@@'`
  export PATH=/usr/local/${pt}/bin:/usr/bin:/bin
  mkdir -p ${pt}
  cd ${pt}
  rm -rf ${PYXBREL}
  tar xzf ../${TARFILE}
  cd ${PYXBREL}
  python -V
  idir=/tmp/${pt}-${RELEASE}
  rm -rf ${idir}
  python setup.py install --prefix=${idir}

  # Rename directory to be sure we're using the installed location
  mv pyxb Xpyxb

  export SCHEMAS_OPENGIS_NET=${SCHEMAS_OPENGIS_NET:-${HOME}/SCHEMAS_OPENGIS_NET}
  export PYXB_ROOT=${idir}/lib/python${pvs}/site-packages
  export PYTHONPATH=.:${PYXB_ROOT}
  export PATH=${PATH}:${idir}/bin
  python setup.py test
  find . -name test.sh \
    | while read TEST_PATH ; do
      dir=`dirname ${TEST_PATH}`
      (cd ${dir} && ./test.sh ) || (echo "FAILED: ${TEST_PATH}" ;  exit 1 )
    done

  # Put directory back
  mv Xpyxb pyxb

  ) 2>&1 | tee log.${pv}-${RELEASE}
done
  
