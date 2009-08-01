PYTHONPATH=../..:.
export PYTHONPATH
PYXB_ARCHIVE_PATH=.:+
export PYXB_ARCHIVE_PATH
rm -f po1.py
../../scripts/pyxbgen -u po1.xsd  -m po1
python demo1.py
rm -f po2.py
../../scripts/pyxbgen -u po2.xsd  -m po2
python demo2.py
rm -f address.py address.wxs
../../scripts/pyxbgen -u nsaddress.xsd -m address --archive-to-file=address.wxs
if [ ! -f address.wxs ] ; then
  echo 1>&2 "Address namespace archive not found"
  exit 1
fi
rm -f po3.py
../../scripts/pyxbgen -u po3.xsd -m po3
python demo3.py
#rm po4.py
#../../scripts/pyxbgen -u po4.xsd -m po4
