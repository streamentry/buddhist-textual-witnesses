.PHONY: test catalog fetch validate-crosswalks render-crosswalks benchmark agama-fetch agama-segments resolve-crosswalks agama pali-fetch pali-units chinese-alignment-units alignment-candidates validate-alignments alignment

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

pali-fetch:
	./scripts/fetch_pali_bilara.sh .cache/bilara-pali

pali-units: pali-fetch
	@BILARA_SHA="$$(git ls-files -s upstream/suttacentral-bilara | awk '{print $$2}')"; \
	rm -rf generated/alignment-source/pali; \
	python3 scripts/build_pali_units.py \
		--bilara-root .cache/bilara-pali \
		--crosswalks data/crosswalks/first-20.json \
		--revision "$$BILARA_SHA" \
		--output generated/alignment-source/pali \
		--strict

chinese-alignment-units: agama-fetch
	rm -rf generated/alignment-source/chinese
	python3 scripts/build_chinese_alignment_units.py \
		--cbeta-root .cache/cbeta-agamas \
		--resolved-crosswalks generated/crosswalks/first-20-resolved.json \
		--output generated/alignment-source/chinese \
		--strict

alignment-candidates: pali-units chinese-alignment-units
	rm -rf generated/alignments
	python3 scripts/generate_alignment_candidates.py \
		--pali-units generated/alignment-source/pali/units.jsonl \
		--chinese-blocks generated/alignment-source/chinese/blocks.jsonl \
		--resolved-crosswalks generated/crosswalks/first-20-resolved.json \
		--output generated/alignments \
		--strict

validate-alignments:
	python3 scripts/validate_alignments.py \
		--pali-units generated/alignment-source/pali/units.jsonl \
		--chinese-blocks generated/alignment-source/chinese/blocks.jsonl \
		--candidates \
			generated/alignments/shared-formula-candidates.jsonl \
			generated/alignments/monotonic-candidates.jsonl \
		--reviewed data/alignments/reviewed.json data/alignments/model-reviewed.json

alignment: test alignment-candidates validate-alignments
	@echo "Pāli-Chinese alignment source layer and candidate queue are valid."
