PYTHONPATH=../..
export PYTHONPATH
mkdir -p raw

test -f ogckml22.xsd || wget http://schemas.opengis.net/kml/2.2.0/ogckml22.xsd
test -f atom-author-link.xsd || wget http://schemas.opengis.net/kml/2.2.0/atom-author-link.xsd
../../scripts/genbind ogckml22.xsd raw kml
test -f kml22gx.xsd || wget http://code.google.com/apis/kml/schema/kml22gx.xsd
../../scripts/genbind kml22gx.xsd gx
