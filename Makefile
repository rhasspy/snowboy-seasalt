SHELL := bash

.PHONY: reformat check install run

all:
	scripts/build-docker.sh

reformat:
	scripts/format-code.sh

check:
	scripts/check-code.sh

install:
	scripts/create-venv.sh

run:
	bin/snowboy-web
