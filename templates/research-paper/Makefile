PYTHON ?= python3
PROJECT ?= examples/reference-paper
BUILD_DIR ?= build/$(THEME)
THEME ?= neutral

.PHONY: all bootstrap-check check check-content check-links clean reproducibility

all:
	$(PYTHON) scripts/build.py --project="$(PROJECT)" --output="$(BUILD_DIR)" --theme="$(THEME)"

check-content: all
	$(PYTHON) scripts/check.py --project="$(PROJECT)" --build-dir="$(BUILD_DIR)" --theme="$(THEME)" --compile-arxiv

reproducibility:
	@tmp_dir="$$(mktemp -d)"; \
	trap 'rm -rf "$$tmp_dir"' EXIT; \
	$(PYTHON) scripts/build.py --project="$(PROJECT)" --output="$$tmp_dir/first" --theme="$(THEME)"; \
	$(PYTHON) scripts/build.py --project="$(PROJECT)" --output="$$tmp_dir/second" --theme="$(THEME)"; \
	cmp "$$tmp_dir/first/paper.pdf" "$$tmp_dir/second/paper.pdf"; \
	cmp "$$tmp_dir/first/web/index.html" "$$tmp_dir/second/web/index.html"; \
	cmp "$$tmp_dir/first/provenance.json" "$$tmp_dir/second/provenance.json"; \
	cmp "$$(find "$$tmp_dir/first/arxiv" -type f -name '*.tar.gz')" "$$(find "$$tmp_dir/second/arxiv" -type f -name '*.tar.gz')"; \
	echo "PASS reproducible PDF, web, provenance, and arXiv-source outputs."

bootstrap-check:
	@tmp_dir="$$(mktemp -d)"; \
	trap 'rm -rf "$$tmp_dir"' EXIT; \
	$(PYTHON) scripts/bootstrap.py --destination="$$tmp_dir/project" --title="Bootstrap smoke paper" --author="Beacon Maintainers" --project-id="bootstrap-smoke" --theme="$(THEME)"; \
	$(PYTHON) scripts/build.py --project="$$tmp_dir/project" --output="$$tmp_dir/build" --theme="$(THEME)"; \
	$(PYTHON) scripts/check.py --project="$$tmp_dir/project" --build-dir="$$tmp_dir/build" --theme="$(THEME)" --compile-arxiv; \
	echo "PASS standalone project bootstrap."

check: check-content reproducibility bootstrap-check

check-links: all
	$(PYTHON) scripts/check.py --project="$(PROJECT)" --build-dir="$(BUILD_DIR)" --theme="$(THEME)" --compile-arxiv --check-external-links

clean:
	rm -rf "build"
