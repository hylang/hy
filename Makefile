all:
	@echo "No default step. Use setup.py"
	@echo ""
	@echo " Other targets:"
	@echo ""
	@echo "   - dev (test & flake)"
	@echo "   - flake"
	@echo "   - test"
	@echo ""


dev: test flake

test:
	nosetests -sv

flake:
	flake8 hy

clear:
	clear

d: clear dev

diff:
	git diff --color | less -r

r: d diff
