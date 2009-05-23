test:
	nosetests tests/{utils,drivers,datatypes,bindings}

PYVERS=2.4.6 2.5.2 2.6.2

alltest:
	maintainer/dobinds.sh

pytests:
	for pyver in $(PYVERS) ; do \
	  echo "Running tests with Python $${pyver}" ; \
	  find . -name '*.pyc' | xargs rm -f ; \
	  PYTHONPATH=. /usr/local/python-$${pyver}/bin/nosetests tests/{utils,drivers,datatypes,bindings} ; \
	done
	(cd tests/drivers ; PYTHONPATH=../.. ./test-stored.sh )

apidoc:
	rm -rf pyxb/standard/bindings/raw
	epydoc --config doc/documentation.cfg
