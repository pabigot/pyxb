PYXB_ROOT=../../..
PYTHONPATH=${PYXB_ROOT}:.
PATH=${PYXB_ROOT}/scripts:${PATH}
PYXB_ARCHIVE_PATH=.
export PYTHONPATH PATH PYXB_ARCHIVE_PATH

# cat >/dev/null <<EOT

rm -f *.wxs *.pyc common.py common4app.py app.py

exit 0

pyxbgen \
  --schema-location=base.xsd --module=common \
  --archive-to-file=common.wxs

pyxbdump common.wxs

echo '**************************'

pyxbgen \
  --schema-location=extend.xsd --module=common4app \
  --archive-to-file=common4app.wxs
  
pyxbdump common4app.wxs

# EOT

python tst-base.py \
&& python tst-extend.py \
&& echo 'Passed common tests'

pyxbgen \
  --schema-location=app.xsd --module=app
  
python tst-app.py \
&& echo 'Passed application tests'
