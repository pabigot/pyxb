PYTHONPATH=../..:.
export PYTHONPATH
PYXB_NAMESPACE_PATH=.:+
export PYXB_NAMESPACE_PATH
rm po1.py
../../scripts/pyxbgen -u po1.xsd  -m po1
python demo1.py
rm po2.py
../../scripts/pyxbgen -u po2.xsd  -m po2
python demo2.py
../../scripts/pyxbgen -u nsaddress.xsd -m address -C
rm po3.py
../../scripts/pyxbgen -u po3.xsd -m po3
python demo3.py
#rm po4.py
#../../scripts/pyxbgen -u po4.xsd -m po4
