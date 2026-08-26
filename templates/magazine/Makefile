PYTHON ?= python3
PROJECT ?= scaffold
THEME ?= neutral
BUILD_DIR ?= build/$(THEME)

.PHONY: all bootstrap-test check check-all clean reproducibility

all:
	$(PYTHON) scripts/build.py --project="$(PROJECT)" --output="$(BUILD_DIR)" --theme="$(THEME)"

check: all
	$(PYTHON) scripts/check.py --project="$(PROJECT)" --build="$(BUILD_DIR)" --theme="$(THEME)"

reproducibility:
	@tmp_dir="$$(mktemp -d)"; \
	trap 'rm -rf "$$tmp_dir"' EXIT; \
	$(PYTHON) scripts/build.py --project="$(PROJECT)" --output="$$tmp_dir/first" --theme="$(THEME)"; \
	$(PYTHON) scripts/build.py --project="$(PROJECT)" --output="$$tmp_dir/second" --theme="$(THEME)"; \
	cmp "$$tmp_dir/first/magazine.pdf" "$$tmp_dir/second/magazine.pdf"; \
	cmp "$$tmp_dir/first/magazine-print.pdf" "$$tmp_dir/second/magazine-print.pdf"; \
	cmp "$$tmp_dir/first/web/index.html" "$$tmp_dir/second/web/index.html"; \
	cmp "$$tmp_dir/first/publication-manifest.json" "$$tmp_dir/second/publication-manifest.json"; \
	cmp "$$tmp_dir/first/provenance.json" "$$tmp_dir/second/provenance.json"; \
	echo "PASS reproducible magazine artifact bundle."

bootstrap-test:
	@tmp_dir="$$(mktemp -d)"; \
	trap 'rm -rf "$$tmp_dir"' EXIT; \
	$(PYTHON) scripts/bootstrap.py --destination="$$tmp_dir/project" --title="Bootstrap Magazine" --publisher="Bootstrap Publisher" --edition="07"; \
	$(PYTHON) scripts/build.py --project="$$tmp_dir/project" --output="$$tmp_dir/output" --theme="neutral"; \
	$(PYTHON) scripts/check.py --project="$$tmp_dir/project" --build="$$tmp_dir/output" --theme="neutral"; \
	pdftotext "$$tmp_dir/output/magazine.pdf" - | rg --fixed-strings "Bootstrap Magazine"; \
	rg --fixed-strings "Bootstrap Publisher" "$$tmp_dir/output/web/index.html" >/dev/null; \
	echo "PASS bootstrap customization evidence."

check-all:
	$(MAKE) --no-print-directory check reproducibility THEME="neutral"
	$(MAKE) --no-print-directory check reproducibility THEME="egohygiene"
	$(MAKE) --no-print-directory bootstrap-test

clean:
	rm -rf "build"
