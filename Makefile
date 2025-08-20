ifneq (,$(wildcard .env))
  include .env
  export
endif

# Defaults if not in .env
DB_PATH ?= ./data/mitigation.db
CSV_OUT ?= ./data/companies.csv
VENV    ?= .venv
PYTHON  := $(VENV)/bin/python
ACTIVATE:= . $(VENV)/bin/activate

EMAIL_MAX_PAGES ?= 5
EMAIL_SLEEP_S   ?= 0.25
EMAIL_LIMIT     ?= 200

.PHONY: help venv crawl ui clean-db reset print-env emails

help:
	@echo "make crawl     - Run mitigator"
	@echo "make ui        - Launch Streamlit"
	@echo "make clean-db  - Delete DB/CSV at DB_PATH/CSV_OUT"
	@echo "make reset     - Clean DB, crawl, then UI"
	@echo "make print-env - Show resolved paths"

venv:
	python3 -m venv $(VENV)
	$(ACTIVATE) && pip install --upgrade pip
	$(ACTIVATE) && pip install -e . streamlit pandas sqlalchemy

crawl:
	$(ACTIVATE) && $(PYTHON) -m mitigator.cli

ui:
	$(ACTIVATE) && streamlit run src/streamlit/app.py

clean-db:
	@echo "Removing: $(DB_PATH) $(CSV_OUT)"
	rm -f $(DB_PATH) $(CSV_OUT)

reset: clean-db crawl ui

print-env:
	@echo "DB_PATH=$(DB_PATH)"
	@echo "CSV_OUT=$(CSV_OUT)"

emails:
	$(ACTIVATE) && EMAIL_MAX_PAGES=$(EMAIL_MAX_PAGES) EMAIL_SLEEP_S=$(EMAIL_SLEEP_S) EMAIL_LIMIT=$(EMAIL_LIMIT) \
	$(PYTHON) -m mitigator.enrich_emails