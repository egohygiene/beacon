PYTHON ?= python3
PROJECT ?= auto
THEME ?= neutral
BUILD_DIR ?= build
SOURCE_REVISION ?=
REVISION_POLICY ?= local
TASK := $(PYTHON) scripts/tasks.py --project="$(PROJECT)" --build-dir="$(BUILD_DIR)" --theme="$(THEME)" --python="$(PYTHON)" --source-revision="$(SOURCE_REVISION)" --revision-policy="$(REVISION_POLICY)"

.PHONY: all bootstrap-check build check check-content clean reproducibility test validate

all: build

build:
	$(TASK) build

validate:
	$(TASK) validate

check-content:
	$(TASK) check-content

reproducibility:
	$(TASK) reproducibility

test:
	$(TASK) test

bootstrap-check:
	$(TASK) bootstrap-check

check:
	$(TASK) check

clean:
	$(TASK) clean
