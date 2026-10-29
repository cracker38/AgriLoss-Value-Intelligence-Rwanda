# Intended use and impact validation plan

## Intended users

- Agricultural planners and MINAGRI / district teams working on post-harvest handling, storage, and agro-processing.
- NISR statisticians reviewing SAS 2024 production patterns.
- Cooperatives, processors, civil-society groups, and development partners who need a transparent first look before commissioning a study.

## Use pathway

1. **Triage:** On Start here, review the scope. In Crop workspace, choose a challenge, SAS season, and crop; enter your role, planning location, optional period, relevant local values/conditions, and optional separate province context. Review the crop-season evidence and field actions, preview the report, and download it. See the [eight-step user workflow](user-workflow.md).
2. **Verify:** Confirm the `s2q39` unit and skip logic. For collection and storage, review `s2q36`–`s2q38` and the transport/storage loss fields `s2q46`–`s2q47`. For processing and sales, review `s2q25`–`s2q28`; confirm zero and missing prices. Compare Season A practice/input associations only after checking their plot linkage and response definitions. Verify current prices and collection conditions locally. Re-estimate with verified weights before any population or geographic claim.
3. **Co-design:** Ask intended users whether a verified pattern supports a storage, collection, processing, or market question.
4. **Pilot and evaluate:** If stakeholders choose an intervention, evaluate its outcomes separately with an appropriate study design.

The workspace turns observed missingness, negative transport/storage values, and zero/missing prices into explicit data checks. It flags crop groups at or above the named-crop upper quartile for positive storage/transport loss shares within the selected season basis, and ties processing routes to reported food, drink, or other transformed use. The displayed routes are investigation ideas supported by sample evidence and documented Rwanda examples; they are not feasibility or investment recommendations. The entered planning location, period, role, local numeric values, and conditions generate local follow-up actions but do not filter or relabel the survey data. The public aggregate supports crop comparisons by SAS season; province remains a separate margin. User-entered prices and costs are not validated, and the current release does not estimate margins. Season A agricultural-practice and fertilizer/pesticide answers are joined to production plots after grain and weight checks; Season B and C module joins are not published. Season A comparisons are unweighted and observational. The market view uses historical SAS 2024 sales-channel and price responses, not a live market feed. The classifier is a retrospective experiment with an A-to-B cross-season holdout, not a future-loss forecast. The workflow does not create a combined priority score, identify causes, recommend investments, target farmers, or estimate changes in productivity.

## Practical evaluation before operational use

No participant sessions have been conducted. The team should run the [decision-support evaluation protocol](impact-evaluation-protocol.md), which contains matched task instructions, an evidence-and-actionability rubric, critical interpretation errors to watch for, and an anonymized [session results template](impact-evaluation-results-template.csv). It compares AgriLoss with a source-based workflow and measures task-level decision quality. The protocol is ready to run; it is not itself evidence that the tool improves decisions.

## Evidence needed for an impact claim

No impact has been measured. A formative task-score improvement would support a limited decision-support claim, not an outcome or farmer-impact claim. Before claiming that AgriLoss improves a decision or outcome, document a baseline and a follow-up measure, such as:

- Whether analysts can identify and explain a candidate pattern more quickly than with the source report alone.
- Whether the dashboard leads to a specific, validated analysis question accepted by an agricultural stakeholder.
- For a later intervention pilot, a separately designed outcome measure with a comparison strategy and survey-appropriate uncertainty.

Do not use dashboard page views, survey-row counts, or model scores as evidence that farmers' productivity or livelihoods improved.
