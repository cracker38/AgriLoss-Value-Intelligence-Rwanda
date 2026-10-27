# Public dashboard data

Only a disclosure-reviewed aggregate release belongs in this directory. Never put source JSON extracts, respondent rows, SQLite staging databases, or row-level model inputs here.

Build a local candidate from authorized source files with:

```powershell
py -3 -m scripts.build_public_dashboard
```

The candidate is written to the Git-ignored `artifacts/dashboard_release_candidate.json`. It contains independent season, province, and crop summaries; small crop/province groups are pooled. This is a review candidate, not an approved release. The minimum group-size rule is not a substitute for NISR's current data-use and disclosure review.

After the required review is complete, place the approved file at `public_data/dashboard_aggregates.json` and record the approval in its `review` object (`status`, `reviewed_by`, `reviewed_on`, and `reference`) and set `release_status` to `approved`. The app refuses to serve this public mode without those fields. Only then should the aggregate file be committed to the hosted repository.

When the approved file is present, `app.py` uses the aggregate-only dashboard and does not load the local respondent-level extracts. The public aggregate view intentionally omits cross-filtering and individual model scores.
