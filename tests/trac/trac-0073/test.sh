pyxbgen \
  --archive-path '&pyxb/bundles/opengis//:+' \
  --schema-location profile.xsd --module profile
python test.py
