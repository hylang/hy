pypy_url=http://buildbot.pypy.org/nightly/trunk/pypy-c-jit-latest-linux64.tar.bz2
pip_url=https://bootstrap.pypa.io/get-pip.py
python=python
pip=pip
coveralls=coveralls
nose=nosetests
pcache=$(HOME)/.pip-cache

ifeq (PyPy 2.4,$(findstring PyPy 2.4,$(shell python -V 2>&1 | tail -1)))
	bad_pypy=1
	python=./pypy
	pip=./pip
    coveralls=./coveralls
    nose=./nosetests
else
	bad_pypy=
endif

all:
	@echo "No default step. Use setup.py"
	@echo ""
	@echo " Other targets:"
	@echo ""
	@echo "   - docs"
	@echo "   - full"
	@echo ""
	@echo "   - dev (test & flake)"
	@echo "   - flake"
	@echo "   - test"
	@echo "   - diff"
	@echo "   - tox"
	@echo "   - d"
	@echo "   - r"
	@echo "   - clean"
	@echo ""

docs:
	make -C docs html

upload: r
	python setup.py sdist upload

full: d tox docs

venv:
ifeq (,$(findstring hy,$(VIRTUAL_ENV)))
	@echo "You're not in a Hy virtualenv. FOR SHAME"
	exit 1
else
	@echo "We're properly in a virtualenv. Going ahead."
endif

dev: test flake

test: venv
	nosetests -sv

tox: venv
	tox

flake:
	flake8 hy tests

clear:
	clear

d: clear dev

diff:
	git diff --color | less -r

r: d tox diff

python:
ifeq ($(bad_pypy),1)
	# Due to stupid PyPy 2.4 bugs, a custom version needs to be downloaded
	curl $(pypy_url) -o pypy.tbz2
	tar xf pypy.tbz2
	ln -sf `pwd`/pypy-*-linux/bin/pypy $(python)
	curl $(pip_url) | $(python)
	ln -sf `pwd`/pypy-*-linux/bin/pip $(pip)
	sudo $(pip) install nose
	ln -sf `pwd`/pypy-*-linux/bin/nosetests $(nose)
endif
ifeq (Python 2.6,$(findstring Python 2.6,$(shell python -V 2>&1)))
	$(pip) install unittest2
endif
	$(pip) install -r requirements-travis.txt --download-cache $(pcache)
	$(pip) install coveralls --download-cache $(pcache)
	$(pip) install --allow-all-external -e .
ifeq ($(bad_pypy),1)
	ln -sf `pwd`/pypy-*-linux/bin/coveralls $(coveralls)
endif

travis: python
	$(nose) -s --with-coverage --cover-package hy
ifeq (PyPy,$(findstring PyPy,$(shell python -V 2>&1 | tail -1)))
	@echo "skipping flake8 on pypy"
else
	flake8 hy bin tests
endif

coveralls:
	$(coveralls)

clean:
	@find . -name "*.pyc" -exec rm {} \;
	@find -name __pycache__ -delete
	@${RM} -r -f .tox
	@${RM} -r -f dist
	@${RM} -r -f *.egg-info
	@${RM} -r -f docs/_build

.PHONY: docs
