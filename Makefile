# Paths (adjust if your venv or files are in different locations)
VENV=.venv
PYTHON=$(VENV)/bin/python
ACTIVATE=. $(VENV)/bin/activate

# Default target
.PHONY: help
help:
	@echo "make venv      - Create virtual environment and install deps"
	@echo "make crawl     - Run mitigator data collection"
	@echo "make ui        - Launch Streamlit UI"
	@echo "make clean-db  - Delete mitigation database and CSV"
	@echo "make reset     - Clean DB, rerun crawl, launch UI"

.PHONY: venv
venv:
	python3 -m venv $(VENV)
	$(ACTIVATE) && pip install --upgrade pip
	$(ACTIVATE) && pip install -e . streamlit pandas sqlalchemy

.PHONY: crawl
crawl:
	$(ACTIVATE) && $(PYTHON) -m mitigator.cli

.PHONY: ui
ui:
	$(ACTIVATE) && streamlit run src/streamlit/app.py

.PHONY: clean-db
clean-db:
	rm -f data/mitigation.db data/companies.csv

.PHONY: reset
reset: clean-db crawl ui
