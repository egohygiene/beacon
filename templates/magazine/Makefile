PYTHON ?= python3
PROJECT ?= auto
THEME ?= neutral
BUILD_DIR ?= build/$(THEME)
TASK := $(PYTHON) scripts/tasks.py --project="$(PROJECT)" --build-dir="$(BUILD_DIR)" --theme="$(THEME)" --python="$(PYTHON)"

.PHONY: all bootstrap-check bootstrap-test build check check-all clean reproducibility

all: build

build:
	$(TASK) build

check:
	$(TASK) check

reproducibility:
	$(TASK) reproducibility

check-all:
	$(TASK) check-all

bootstrap-check bootstrap-test:
	$(TASK) bootstrap-check

clean:
	$(TASK) clean
