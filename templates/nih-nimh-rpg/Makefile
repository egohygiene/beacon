PYTHON ?= python3
BUILD_DIR ?= build
TASK := $(PYTHON) scripts/tasks.py --build-dir="$(BUILD_DIR)" --python="$(PYTHON)"

.PHONY: all build check clean

all: build

build:
	$(TASK) build

check:
	$(TASK) check

clean:
	$(TASK) clean
