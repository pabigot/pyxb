PYXB_ARCHIVE_PATH=.
export PYXB_ARCHIVE_PATH

# cat >/dev/null <<EOT

rm -f *.wxs *.wxs- *.pyc common.py common4app.py app.py

pyxbgen \
  --schema-location=base.xsd --module=common \
  --archive-to-file=common.wxs || exit 1

#pyxbdump common.wxs
python tst-base.py || exit 1

echo '**************************'

pyxbgen \
  --schema-location=extend.xsd --module=common4app \
  --pre-load-archive=common.wxs \
  --archive-to-file=common4app.wxs || exit 1
  
# pyxbdump common4app.wxs
python tst-extend.py || exit 1

# Use this to verify dependency checking
mv common.wxs common.wxs-
pyxbgen \
  --schema-location=app.xsd --module=app > bad.log 2>&1 \
  && ( echo "Succeeded bad conversion" ; exit 1 )
grep -q 'common4app.wxs: archive depends on unavailable archive' bad.log || exit 1

mv common.wxs- common.wxs
pyxbgen \
  --schema-location=app.xsd --module=app \
  || ( echo "Failed application schema" ; exit 1 )

python tst-app.py || exit 1

echo "nsext TESTS PASSED"
