LESS_SCRIPTS = hy.css

LESSC = lessc
LESSCFLAGS = -x
STATIC = static

.SUFFIXES:
.SUFFIXES: .less .css


all: build


build: $(LESS_SCRIPTS)


.less.css:
	$(LESSC) $(LESSCFLAGS) $< > $@


.PHONY: build
