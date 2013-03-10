STATIC = static
STATIC_CSS = $(STATIC)/css
STATIC_JS = $(STATIC)/js


all: hello build


hello:
	@cowsay 'Welcome to Hy!'


build: clean less coffee


less:
	make -C less
	mv less/*css $(STATIC_CSS)


coffee:
	make -C coffee
	mv coffee/*js $(STATIC_JS)

clean:
	rm -f $(STATIC_CSS)/hy.css

devel:
	@./devel.sh

.PHONY: build clean less coffee devel
