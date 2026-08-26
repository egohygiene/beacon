PANDOC ?= pandoc
PYTHON ?= python3
PDF_ENGINE ?= pdflatex
BUILD_DIR ?= build
THEME ?= themes/organization.json
SOURCE_DATE_EPOCH ?=
TASK := $(PYTHON) scripts/tasks.py --build-dir="$(BUILD_DIR)" --theme="$(THEME)" --pandoc="$(PANDOC)" --pdf-engine="$(PDF_ENGINE)" --python="$(PYTHON)" $(if $(SOURCE_DATE_EPOCH),--source-date-epoch="$(SOURCE_DATE_EPOCH)")

.PHONY: all build check check-content check-links clean reproducibility

all: build

build:
	$(TASK) build

check:
	$(TASK) check

check-content:
	$(TASK) check-content

check-links:
	$(TASK) check-links

reproducibility:
	$(TASK) reproducibility

clean:
	$(TASK) clean
