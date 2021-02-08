#! /bin/sh

pyxbgen -u multipleRestriction.xsd -m mr
python check.py
