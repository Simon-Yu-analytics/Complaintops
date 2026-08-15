# Data policy

`data/sample/complaints.csv` is deterministic synthetic data generated locally
by `scripts/generate_sample.py`. Git ignores the reproducible CSV. It mirrors
the fields used by the public CFPB
Consumer Complaint Database without containing consumer narratives or personal
information.

Real extracts belong in `data/raw/`, which is intentionally excluded from Git.
Run the downloader in `complaintops.data.download_cfpb_sample` from a networked
environment and review the CFPB data-use notice before analysis.
