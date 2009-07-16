RELEASE=0.5.1
PYXBREL=PyXB-${RELEASE}
TARFILE=${PYXBREL}.tar.gz

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

  export PYTHONPATH=.:${idir}/lib/python${pvs}/site-packages
  python setup.py test
  cd examples;
  for d in [a-z]* ; do
    if [ -f ${d}/test.sh ] ; then
      ( cd ${d} ; sh test.sh )
    fi
  done
  cd ..  # examples
  cd ../..
  ) 2>&1 | tee log.${pv}
done
  
