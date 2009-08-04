PYXB_ROOT=../../..
PYTHONPATH=${PYXB_ROOT}:.
PATH=${PYXB_ROOT}/scripts:${PATH}
PYXB_ARCHIVE_PATH=.:+
export PYTHONPATH PATH PYXB_ARCHIVE_PATH

rm -f *.wxs common.py common4app.py

pyxbgen \
  --schema-location=base.xsd --module=common \
  --archive-to-file=common.wxs

pyxbgen \
  --schema-location=extend.xsd --module=common4app \
  
python tst-base.py \
&& python tst-extend.py \
&& echo 'Passed'
