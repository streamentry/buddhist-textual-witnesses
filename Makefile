.PHONY: test catalog fetch validate-crosswalks render-crosswalks benchmark

fetch:
	./scripts/fetch_sources.sh

test:
	python3 -m unittest discover -s tests -v

validate-crosswalks:
	python3 scripts/validate_crosswalks.py

render-crosswalks:
	python3 scripts/render_crosswalks.py

catalog:
	python3 scripts/build_catalog.py --strict

benchmark: test validate-crosswalks
	python3 scripts/render_crosswalks.py --check
	@echo "Crosswalk benchmark is valid."
