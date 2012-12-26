LESSC = lessc
LESSCFLAGS = -x
DEPLOYMENT = dev

all: clean build

STATIC=./static

clean:
	rm -rf $(STATIC)/css

build:
	mkdir $(STATIC)/css
	$(LESSC) $(LESSCFLAGS) less/debuild.me.less > $(STATIC)/css/debuild.css
