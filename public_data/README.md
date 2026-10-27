# Public dashboard data

Only an aggregate dashboard release belongs in this directory. Never put source JSON extracts, respondent rows, SQLite staging databases, or row-level model inputs here.

Build a local candidate from authorized source files with:

```powershell
py -3 -m scripts.build_public_dashboard
```

The candidate is written to the Git-ignored `artifacts/dashboard_release_candidate.json`. It contains independent season, province, and crop summaries; small crop/province groups are pooled. This is a review candidate, not an approved release. The minimum group-size rule is not a substitute for NISR's current data-use and disclosure review.

The standard release path is to complete NISR data-use and disclosure review, then place the approved file at `public_data/dashboard_aggregates.json`, record the approval in its `review` object (`status`, `reviewed_by`, `reviewed_on`, and `reference`), and set `release_status` to `approved`.

The repository owner may explicitly direct publication before that review is recorded. In that case, preserve the pending status and use `release_status: "owner_authorized_unreviewed"` with a `publication_authorization` object that sets `authorized` to `true` and `review_status` to `not_recorded`. The hosted dashboard displays a prominent provisional-release warning. This owner override does not state or imply NISR approval.

When an authorized aggregate file is present, `app.py` uses the aggregate-only dashboard and does not load the local respondent-level extracts. The public aggregate view intentionally omits cross-filtering and individual model scores.
