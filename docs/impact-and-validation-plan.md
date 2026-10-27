# Intended use and impact validation plan

## Intended users

- NISR statisticians reviewing SAS 2024 production patterns.
- Agricultural planners, researchers, and extension teams formulating follow-up questions.
- Civil-society and development partners discussing evidence needs with those teams.

## Use pathway

1. **Triage:** In the Follow-up workspace, sort named crop groups by positive-response share, positive-response count, or missing-response share. Check each candidate alongside valid-response counts and missingness, then export a brief.
2. **Verify:** Confirm the `s2q39` unit, denominator, questionnaire logic, and release conditions. Re-estimate candidate findings using verified weights, strata, clusters, and survey-appropriate uncertainty.
3. **Co-design:** Ask intended users whether a verified pattern supports a relevant question about production or post-harvest practices.
4. **Pilot and evaluate:** If stakeholders choose an intervention, evaluate its outcomes separately with an appropriate study design.

The current dashboard supports the first step and prepares a follow-up brief; it does not perform the survey-aware estimation or stakeholder validation. Its sorting lenses are descriptive and do not create a combined priority score. It does not identify causes, recommend interventions, target farmers, or estimate changes in productivity.

## Practical evaluation before operational use

Run a small, documented usability review with intended agricultural data users. Ask each person to:

1. Use two review lenses and explain why their crop-group ordering differs.
2. Select a crop group and download its follow-up brief.
3. Explain the difference between positive-response share, valid response count, and missingness; explain why these are not national estimates and why `s2q39` is not labeled in kilograms.
4. Explain why season and province summaries do not filter the selected crop result.
5. Describe one follow-up analysis needed before using the pattern in planning.

Record task completion, misunderstandings, and requested changes without collecting unnecessary personal information. Fix confusing labels before sharing the app as a decision-support prototype.

## Evidence needed for an impact claim

No impact has been measured. Before claiming that AgriLoss improves a decision or outcome, document a baseline and a follow-up measure, such as:

- Whether analysts can identify and explain a candidate pattern more quickly than with the source report alone.
- Whether the dashboard leads to a specific, validated analysis question accepted by an agricultural stakeholder.
- For a later intervention pilot, a separately designed outcome measure with a comparison strategy and survey-appropriate uncertainty.

Do not use dashboard page views, survey-row counts, or model scores as evidence that farmers' productivity or livelihoods improved.
