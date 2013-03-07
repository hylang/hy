all:
	@echo "No default step. Use setup.py"
	@echo ""
	@echo " Other targets:"
	@echo ""
	@echo "   - dev (test & flake)"
	@echo "   - flake"
	@echo "   - test"
	@echo "   - diff"
	@echo "   - tox"
	@echo "   - d"
	@echo "   - r"
	@echo ""


dev: test flake

test:
	nosetests -sv

tox:
	tox

flake:
	flake8 hy

clear:
	clear

d: clear dev

diff:
	git diff --color | less -r

r: d tox diff
