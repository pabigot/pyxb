mkdir -p bindings
touch bindings/__init__.py
export PYXB_NAMESPACE_PATH="`pwd`/bindings:+"
pyxbgen -m bindings.xlinks -u xlink/xlinks.xsd
pyxbgen -m bindings.gml -u gml/gml.xsd
pyxbgen -m bindings.gco -u iso19139/gco/gco.xsd
pyxbgen -m bindings.gmd -u iso19139/gmd/gmd.xsd
pyxbgen -m bindings.gts -u iso19139/gts/gts.xsd
pyxbgen -m bindings.gsr -u iso19139/gsr/gsr.xsd
pyxbgen -m bindings.gss -u iso19139/gss/gss.xsd



