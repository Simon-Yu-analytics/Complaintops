PYTHON ?= python3
NODE ?= node

.PHONY: all sample run test test-js verify check visualizations report validate-artifacts artifacts dashboard clean

all: check

sample:
	$(PYTHON) scripts/generate_sample.py

run: sample
	PYTHONPATH=src $(PYTHON) -m complaintops.pipeline

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

test-js:
	$(NODE) tests/dashboard.test.js

verify: test run
	$(PYTHON) -m compileall -q src scripts tests

check: verify test-js

visualizations: run
	PYTHONPATH=src $(PYTHON) scripts/generate_visualizations.py

report: visualizations
	$(PYTHON) scripts/generate_report.py

validate-artifacts:
	$(PYTHON) scripts/validate_artifacts.py

artifacts: report validate-artifacts

dashboard:
	$(PYTHON) -m http.server 8000 -d dashboard

clean:
	rm -rf artifacts dashboard/data/results.json
