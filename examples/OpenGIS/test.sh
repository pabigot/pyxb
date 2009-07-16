export PYXB_ARCHIVE_PATH=opengis:opengis/misc:opengis/citygml:opengis/iso19139:+
PYXB_ROOT=../..
export PYTHONPATH=${PYXB_ROOT}:.

if [ ! -d opengis ] ; then
  sh makebind.sh
fi

python demo.py || exit 1
python check_sos.py Schemas/sos/1.0.0/examples/*.xml

