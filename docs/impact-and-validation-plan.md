# Intended use and impact validation plan

## Intended users

- Agricultural planners and MINAGRI / district teams working on post-harvest handling, storage, and agro-processing.
- NISR statisticians reviewing SAS 2024 production patterns.
- Cooperatives, processors, civil-society groups, and development partners who need a transparent first look before commissioning a study.

## Use pathway

1. **Triage:** On Start here, review sample indicators. In the Crop workspace, choose a track and crop, inspect the rank and valid denominator, optionally select a province as separate context, record a local condition, and export a brief with evidence checks.
2. **Verify:** Confirm the `s2q39` unit and skip logic. For collection and storage, review `s2q36`–`s2q38` and the transport/storage loss fields `s2q46`–`s2q47`. For processing and sales, review `s2q25`–`s2q28`; confirm zero and missing prices. Compare Season A practice/input associations only after checking their plot linkage and response definitions. Verify current prices and collection conditions locally. Re-estimate with verified weights before any population or geographic claim.
3. **Co-design:** Ask intended users whether a verified pattern supports a storage, collection, processing, or market question.
4. **Pilot and evaluate:** If stakeholders choose an intervention, evaluate its outcomes separately with an appropriate study design.

The workspace turns observed missingness, negative transport/storage values, and zero/missing prices into explicit data checks. It links Season A agricultural-practice and fertilizer/pesticide answers to production plots after grain and weight checks; Season B and C module joins are not published. Season A comparisons are unweighted and observational. The market view uses historical SAS 2024 sales-channel and price responses, not a live market feed. The user-entered local condition adds a question for verification; it is not survey evidence. Province values remain separate from crop values. The classifier is a retrospective experiment with an A-to-B cross-season holdout, not a future-loss forecast. The workflow does not create a combined priority score, identify causes, recommend investments, target farmers, or estimate changes in productivity.

## Practical evaluation before operational use

Run a small, documented usability review with intended agricultural data users. Ask each person to:

1. Use two review lenses and explain why their crop-group ordering differs.
2. Select a crop and province, enter a local condition, and download the tailored brief.
3. Explain which figures are crop evidence and which are province context, and why they are not linked.
4. Explain the difference between positive-response share, valid response count, and missingness; explain why these are not national estimates and why `s2q39` is not labeled in kilograms.
5. Describe one follow-up analysis needed before using the pattern in planning. Identify the market figures as historical SAS 2024 reports, distinguish Season A associations from causal evidence, and explain why the classifier does not forecast future loss.

Record task completion, time to complete, misunderstandings (especially whether users infer crop-by-province relationships or interpret a follow-up check as an investment recommendation), and requested changes. Do not retain free-text notes or unnecessary personal information. Fix confusing labels before sharing the app as a decision-support prototype.

## Evidence needed for an impact claim

No impact has been measured. Before claiming that AgriLoss improves a decision or outcome, document a baseline and a follow-up measure, such as:

- Whether analysts can identify and explain a candidate pattern more quickly than with the source report alone.
- Whether the dashboard leads to a specific, validated analysis question accepted by an agricultural stakeholder.
- For a later intervention pilot, a separately designed outcome measure with a comparison strategy and survey-appropriate uncertainty.

Do not use dashboard page views, survey-row counts, or model scores as evidence that farmers' productivity or livelihoods improved.
