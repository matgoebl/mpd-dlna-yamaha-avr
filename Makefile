VENV=venv
PYTHON_MODULES=python-musicpd git+https://github.com/wuub/rxv.git git+https://github.com/matgoebl/nano-dlna.git@dev

all: install

install:
	virtualenv $(VENV) --python=python3 && . $(VENV)/bin/activate && pip3 install $(PYTHON_MODULES)
	cp mpd-dlna-yamaha-avr.py $(VENV)/bin/

clean:
	rm -rf $(VENV)

run:
	. $(VENV)/bin/activate && ./mpd-dlna-yamaha-avr.py

.PHONY: all install clean run
