#! /bin/sh

pyxbgen \
  -u po3.xsd -m po3 \
  --archive-path .:+
