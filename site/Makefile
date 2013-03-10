STATIC = static
STATIC_CSS = $(STATIC)/css
STATIC_JS = $(STATIC)/js


all: build
	@echo "Nice."


build: clean less coffee


less:
	make -C less
	mv less/*css $(STATIC_CSS)


coffee:
	make -C coffee
	mv coffee/*js $(STATIC_JS)

clean:
	rm -f $(STATIC_CSS)/hy.css


.PHONY: build clean less coffee
