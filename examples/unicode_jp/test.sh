#!/bin/sh

# Because this is an OpenGIS application, the OpenGIS bundle must be
# made available during binding generation.
export PYXB_ARCHIVE_PATH='&pyxb/bundles/opengis//:+'

# This allows this script to run under the autotest environment, where
# output is sent to a file.
export PYTHONIOENCODING='utf-8'

rm fgd_gml.*

# A customized pyxbgen is required to do the translation
./pyxbgen_jp \
   --schema-location=data/shift_jis/FGD_GMLSchema.xsd --module=fgd_gml

# Make sure it worked
python check.py

