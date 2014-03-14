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

travis:
	nosetests -s --with-coverage --cover-package hy
ifeq (PyPy,$(findstring PyPy,$(shell python -V 2>&1 | tail -1)))
	@echo "skipping flake8 on pypy"
else
	flake8 hy bin tests
endif

clean:
	@find . -name "*.pyc" -exec rm {} \;
	@find -name __pycache__ -delete
	@${RM} -r -f .tox
	@${RM} -r -f dist
	@${RM} -r -f *.egg-info
	@${RM} -r -f docs/_build

.PHONY: docs
