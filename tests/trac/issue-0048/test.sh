#! /bin/sh

pyxbgen \
  --schema-location profile.xsd --module profile
python check.py
