ATTACHMENTS := \
	project-summary-abstract \
	project-narrative \
	specific-aims \
	research-strategy \
	bibliography-references

TEX_SOURCES := $(addprefix attachments/,$(addsuffix .tex,$(ATTACHMENTS)))
BUILD_DIR ?= build

.PHONY: all check clean

all:
	@mkdir -p "$(BUILD_DIR)"
	@BEACON_BUILD_DIR="$(BUILD_DIR)" latexmk -r latexmkrc -pdf $(TEX_SOURCES)

check: all
	@python3 scripts/check.py --build-dir="$(BUILD_DIR)"

clean:
	@BEACON_BUILD_DIR="$(BUILD_DIR)" latexmk -r latexmkrc -C $(TEX_SOURCES)
	@rm -rf "$(BUILD_DIR)"
