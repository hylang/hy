.SUFFIXES:
.SUFFIXES: .coffee .js

COFFEE_SCRIPTS = main.js


all: build


build: $(COFFEE_SCRIPTS)


.coffee.js:
	coffee -c $<
	uglifyjs --no-copyright --overwrite $@


.PHONY: build
