STATIC = static
STATIC_CSS = $(STATIC)/css
STATIC_JS = $(STATIC)/js


all: hello deps build


hello:
	@cowsay 'Welcome to Hy!'


build: clean css js


css: less
	cp css/* $(STATIC_CSS)


js: coffee
	cp js/* $(STATIC_JS)


less:
	make -C less
	mv less/*css $(STATIC_CSS)


coffee:
	make -C coffee
	mv coffee/*js $(STATIC_JS)


clean:
	rm -fr $(STATIC_CSS) $(STATIC_JS)
	mkdir -p $(STATIC_CSS) $(STATIC_JS)


devel:
	@./devel.sh

deps:
	set -e; for x in $(shell cat dependencies); do \
		echo "Checking for dependency: $$x"; \
		dpkg-query -s $$x >/dev/null 2>&1; \
	done;

.PHONY: build clean less coffee devel
