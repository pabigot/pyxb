PYTHONPATH=../..
export PYTHONPATH
mkdir -p raw
touch raw/__init__.py
../../scripts/pyxbgen \
  -u ipo.xsd \
  -p ipo \
  -r
  
  
