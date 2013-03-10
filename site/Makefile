#

LESSC = lessc
LESSCFLAGS = -x
STATIC = static
STATIC_CSS = $(STATIC)/css


all: build
	@echo "Nice."


build: clean
	$(LESSC) $(LESSCFLAGS) less/hy.less > $(STATIC_CSS)/hy.css


clean:
	rm -f $(STATIC_CSS)/hy.css


.PHONY: build clean
