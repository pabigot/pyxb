PYTHONPATH=../..:.
export PYTHONPATH
rm -f content.py
../../scripts/pyxbgen -u content.xsd  -m content
python showcontent.py > showcontent.out
cat showcontent.out


