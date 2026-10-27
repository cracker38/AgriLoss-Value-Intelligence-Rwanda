# NISR 2026 Big Data Hackathon submission checklist

**Official reference:** [2026 Hackathon Competition — NISR](https://www.statistics.gov.rw/about/hackathon/2026-hackathon-competition)  
**Project fit:** Track 1 — Agricultural Productivity  
**Deadline shown by NISR:** 30 October 2026, 11:59 PM  
**Registration deadline shown by NISR:** 20 October 2026 (passed as of 27 October 2026)

Check the official page again before submitting in case NISR updates its dates or instructions.

## Submission package

- [x] README describing the problem, data, interpretation, and how to use the dashboard.
- [x] Project scripts and runtime requirements.
- [x] Aggregate data file at `public_data/dashboard_aggregates.json` and a link to the NISR SAS 2024 catalog in the README.
- [x] Public GitHub repository: <https://github.com/cracker38/AgriLoss-Value-Intelligence-Rwanda>
- [x] Deployed app: <https://agriloss-rwanda.streamlit.app/>
- [ ] Record and add a screen demonstration no longer than three minutes. A narration plan is in `docs/demo-recording-script.md`.
- [ ] Open the public GitHub link and deployed app in a signed-out browser and confirm both work at submission time.
- [ ] Confirm the aggregate release is acceptable for the intended public use. The current app labels it provisional because NISR disclosure review is not recorded.

## Participant and team eligibility

- [ ] Confirm the team has exactly two eligible undergraduate or master's students.
- [ ] Confirm at least one team member is a Rwandan citizen.
- [ ] Keep each team member's student card or other eligibility evidence ready. Do not commit identity documents to the public repository.
- [ ] Confirm neither team member is ineligible due to having been on a top-three team in an earlier NISR Big Data Hackathon.
- [ ] Confirm the team registered by 20 October 2026. If not, contact NISR immediately; do not assume late registration is accepted.

## Originality, sources, AI, and intellectual property

- [ ] Confirm this work has not been submitted to another competition or entity and is the team's original work.
- [ ] Cite every dataset, report, external source, code/library source, and other referenced material in the README.
- [ ] Review and finalize `docs/ai-use-disclosure.md`. NISR permits AI assistants, requires disclosure, and holds participants responsible for the submission.
- [ ] Read the official IP term before entering: NISR's competition page says entrants assign submitted-work intellectual property rights to NISR. Confirm every team member understands and accepts this condition before submission.
- [ ] Confirm the data-use terms and disclosure status for the NISR extracts and public aggregate release. The website warning currently says review is not recorded.

## Judging criteria (20 points each)

| Criterion | Current evidence | Last-mile improvement |
|---|---|---|
| Problem understanding and relevance | NISR SAS 2024 crop production and reported loss; aligned to Track 1. | Explain the specific follow-up question and validate it with intended users. |
| Data use and methodology | Source audit, documented cleaning, aggregate release, grouped local model evaluation. | No external dataset or survey-weighted estimates are implemented. Explain why the current scope is descriptive and avoid population claims. |
| Tech innovation | Python, Streamlit, Plotly, scikit-learn, and reproducible scripts. | Keep the model clearly exploratory; do not describe it as a forecast or alert system. |
| Usability and design | Public dashboard with independent season, province, and crop filters and interpretation notes. | Complete a short user check and screen recording; test a small screen if possible. |
| Tangible impact | Aggregates can help analysts identify possible agricultural productivity and post-harvest follow-up topics. | Present a realistic path to validation and stakeholder use; no measured impact exists yet. |

## Submission-day checks

1. Finish the recording and place the `.webm` or `.gif` in `demo/`.
2. Finalize the AI-use and source disclosures.
3. Confirm entry eligibility, registration, originality, and IP terms with both team members.
4. Review the hosted app's provisional-release notice and the current NISR data-use conditions.
5. Submit the public repository and app links through NISR's official submission channel before the published deadline.
