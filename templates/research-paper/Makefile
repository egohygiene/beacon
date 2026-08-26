PYTHON ?= python3
PROJECT ?= auto
THEME ?= neutral
BUILD_DIR ?= build/$(THEME)
TASK := $(PYTHON) scripts/tasks.py --project="$(PROJECT)" --build-dir="$(BUILD_DIR)" --theme="$(THEME)" --python="$(PYTHON)"

.PHONY: all bootstrap-check build check check-content check-links clean reproducibility

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

bootstrap-check:
	$(TASK) bootstrap-check

clean:
	$(TASK) clean
