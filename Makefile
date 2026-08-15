PYTHON ?= python3

.PHONY: all sample run test verify dashboard clean

all: verify

sample:
	$(PYTHON) scripts/generate_sample.py

run: sample
	PYTHONPATH=src $(PYTHON) -m complaintops.pipeline

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

verify: test run
	$(PYTHON) -m compileall -q src scripts tests

dashboard:
	$(PYTHON) -m http.server 8000 -d dashboard

clean:
	rm -rf artifacts dashboard/data/results.json
