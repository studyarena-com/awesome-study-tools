.PHONY: all check format render links serve

all: check

check:
	python3 scripts/validate_catalog.py

format:
	python3 scripts/format_catalog.py

render:
	python3 scripts/render_catalog.py

links:
	python3 scripts/check_links.py

serve:
	python3 -m http.server --directory docs 8000
