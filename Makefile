pip_url=https://bootstrap.pypa.io/get-pip.py
python=python
pip=pip
coveralls=coveralls

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
	$(MAKE) -C docs html

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
	pytest

tox: venv
	tox

flake:
	flake8 hy tests --ignore=E121,E123,E126,E226,E24,E704,W503,E302,E305,E701

clear:
	clear

d: clear dev

diff:
	git diff --color | less -r

r: d tox diff

python:
ifeq (Python 2.6,$(findstring Python 2.6,$(shell python -V 2>&1)))
	$(pip) install unittest2
endif
	$(pip) install -r requirements-travis.txt
	$(pip) install coveralls
	$(pip) install -e .

coveralls:
	$(coveralls)

clean:
	@find . -name "*.pyc" -exec rm {} \;
	@find . -name __pycache__ -delete
	@${RM} -r -f .tox
	@${RM} -r -f dist
	@${RM} -r -f *.egg-info
	@${RM} -r -f docs/_build

.PHONY: all docs upload full venv dev test tox flake clear d diff r python coveralls clean
