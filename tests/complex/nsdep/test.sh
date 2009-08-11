PYXB_ARCHIVE_PATH=${PYXB_ARCHIVE_PATH:+${PYXB_ARCHIVE_PATH}:}bindings
# PYTHONPATH=${PYTHONPATH:+${PYTHONPATH}:}bindings:.
rm -rf bindings
mkdir -p bindings
touch bindings/__init__.py

pyxbgen \
  --module-prefix=bindings \
  --schema-location=d_c.xsd --module=D \
  --archive-to-file=bindings/D.wxs \
 && python tst-a.py \
 && python tst-b.py \
 && echo "Passed"
