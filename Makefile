test:
	nosetests tests/{utils,drivers,datatypes,bindings}

alltest:
	maintainer/dobinds.sh
	nosetests tests/{utils,drivers,datatypes,bindings}
	(cd tests/drivers ; ./test-stored.sh )

apidoc:
	rm -rf pyxb/standard/bindings/raw
	epydoc --config doc/documentation.cfg
