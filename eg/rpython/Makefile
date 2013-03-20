RPY_WRAP = python -m hy
RPY_FLAGS = -O2
RPY = ~/pypy/rpython/bin/rpython

all: clean build

clear:
	@clear

clean:
	rm -f target-c

build:
	$(RPY_WRAP) $(RPY) $(RPY_FLAGS) target.py
