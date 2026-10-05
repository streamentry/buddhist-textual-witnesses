.PHONY: test catalog fetch

fetch:
	./scripts/fetch_sources.sh

test:
	python3 -m unittest discover -s tests -v

catalog:
	python3 scripts/build_catalog.py --strict
