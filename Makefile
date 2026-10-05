.PHONY: test catalog fetch validate-crosswalks render-crosswalks benchmark agama-fetch agama-segments resolve-crosswalks agama

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

agama-fetch:
	./scripts/fetch_cbeta_agamas.sh .cache/cbeta-agamas

agama-segments: agama-fetch
	@CBETA_SHA="$$(git ls-files -s upstream/cbeta-xml-p5 | awk '{print $$2}')"; \
	python3 scripts/build_agama_segments.py \
		--cbeta-root .cache/cbeta-agamas \
		--config config/agama-segmentation.json \
		--revision "$$CBETA_SHA" \
		--output generated/agama-segments \
		--strict

resolve-crosswalks: agama-segments
	python3 scripts/resolve_crosswalk_segments.py \
		--segments generated/agama-segments \
		--input data/crosswalks/first-20.json \
		--output generated/crosswalks/first-20-resolved.json \
		--strict

agama: test resolve-crosswalks
	@echo "CBETA Agama segmentation and crosswalk resolution are valid."
