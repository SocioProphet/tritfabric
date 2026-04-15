.PHONY: help venv validate shacl sparql

help:
	@printf "%s\\n" \\
	  "Targets:" \\
	  "  make venv     - create .venv and install deps" \\
	  "  make validate  - run SHACL + SPARQL sanity checks" \\
	  "  make shacl    - run SHACL validation (pyshacl)" \\
	  "  make sparql   - run SPARQL tests (rdflib)"

venv:
	python3 -m venv .venv
	./.venv/bin/python -m pip install -U pip wheel setuptools
	./.venv/bin/python -m pip install -r requirements.txt

validate: shacl sparql

shacl:
	./.venv/bin/python tools/validate.py --shacl 2>/dev/null || python3 tools/validate.py --shacl

sparql:
	./.venv/bin/python tools/validate.py --sparql 2>/dev/null || python3 tools/validate.py --sparql
