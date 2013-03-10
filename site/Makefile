#

LESSC = lessc
LESSCFLAGS = -x
STATIC = static
STATIC_CSS = $(STATIC)/css


all: build
	@echo "Nice."


build: clean less coffee

less:
	$(LESSC) $(LESSCFLAGS) less/hy.less > $(STATIC_CSS)/hy.css

coffee:
	coffee -o static/js -c ./coffee/*

clean:
	rm -f $(STATIC_CSS)/hy.css


.PHONY: build clean less coffee
