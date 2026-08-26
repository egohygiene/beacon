PANDOC ?= pandoc
PYTHON ?= python3
PDF_ENGINE ?= pdflatex
BUILD_DIR ?= build
THEME ?= themes/organization.json
SOURCE_DATE_EPOCH ?= 1787616000

SOURCE := manuscript/whitepaper.md
METADATA := metadata/whitepaper.json
BIBLIOGRAPHY := manuscript/references.bib
PDF_TEMPLATE := templates/whitepaper.tex
HTML_TEMPLATE := templates/whitepaper.html
PDF_OUTPUT := $(BUILD_DIR)/whitepaper.pdf
HTML_OUTPUT := $(BUILD_DIR)/web/index.html
COMMON_ARGS := $(SOURCE) --from="markdown+raw_attribute" --citeproc --metadata-file="$(METADATA)" --metadata-file="$(THEME)" --bibliography="$(BIBLIOGRAPHY)" --table-of-contents

.PHONY: all check check-content check-links clean reproducibility

all: $(PDF_OUTPUT) $(HTML_OUTPUT)

$(PDF_OUTPUT): $(SOURCE) $(METADATA) $(BIBLIOGRAPHY) $(THEME) $(PDF_TEMPLATE)
	@mkdir -p "$(BUILD_DIR)"
	SOURCE_DATE_EPOCH="$(SOURCE_DATE_EPOCH)" $(PANDOC) $(COMMON_ARGS) \
		--template="$(PDF_TEMPLATE)" \
		--pdf-engine="$(PDF_ENGINE)" \
		--output="$@"

$(HTML_OUTPUT): $(SOURCE) $(METADATA) $(BIBLIOGRAPHY) $(THEME) $(HTML_TEMPLATE)
	@mkdir -p "$(BUILD_DIR)/web"
	SOURCE_DATE_EPOCH="$(SOURCE_DATE_EPOCH)" $(PANDOC) $(COMMON_ARGS) \
		--template="$(HTML_TEMPLATE)" \
		--standalone \
		--output="$@"

check-content: all
	$(PYTHON) scripts/check.py --build-dir="$(BUILD_DIR)" --theme="$(THEME)"

reproducibility:
	@tmp_dir="$$(mktemp -d)"; \
	trap 'rm -rf "$$tmp_dir"' EXIT; \
	$(MAKE) --no-print-directory all BUILD_DIR="$$tmp_dir/first" THEME="$(THEME)"; \
	$(MAKE) --no-print-directory all BUILD_DIR="$$tmp_dir/second" THEME="$(THEME)"; \
	cmp "$$tmp_dir/first/whitepaper.pdf" "$$tmp_dir/second/whitepaper.pdf"; \
	cmp "$$tmp_dir/first/web/index.html" "$$tmp_dir/second/web/index.html"; \
	echo "PASS reproducible PDF and web outputs."

check: check-content reproducibility

check-links: all
	$(PYTHON) scripts/check.py --build-dir="$(BUILD_DIR)" --theme="$(THEME)" --check-external-links

clean:
	rm -rf "$(BUILD_DIR)"
