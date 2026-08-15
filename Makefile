PYTHON ?= python3

.PHONY: sample run test dashboard clean

sample:
	$(PYTHON) scripts/generate_sample.py

run: sample
	PYTHONPATH=src $(PYTHON) -m complaintops.pipeline

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

dashboard:
	$(PYTHON) -m http.server 8000 -d dashboard

clean:
	rm -rf artifacts dashboard/data/results.json

