ATTACHMENTS := \
	project-summary-abstract \
	project-narrative \
	specific-aims \
	research-strategy \
	bibliography-references

TEX_SOURCES := $(addprefix attachments/,$(addsuffix .tex,$(ATTACHMENTS)))

.PHONY: all check clean

all:
	@mkdir -p build
	@latexmk -r latexmkrc -pdf $(TEX_SOURCES)

check: all
	@python3 scripts/check.py

clean:
	@latexmk -r latexmkrc -C $(TEX_SOURCES)
	@rm -rf build
