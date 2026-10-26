# SAS 2024 dataset audit

**Audit date:** 2026-10-25  
**Scope:** repository inventory, all 12 local NISR-named JSON files, the additional production CSV, schema and record checks, and comparison with NISR's SAS 2024 microdata metadata.

## Executive summary

The workspace contains 12 JSON files under `dataset/nisrdataset/`, plus a Season B production CSV under `dataset/publicdataset/`. The JSON files contain **248,778 rows** and about **354.9 MB** of source data. The repository now also includes this audit, its schema and field-quality inventories, a standard-library audit command, unit tests, and a project README. There is not yet an API, dashboard, database, trained model, notebook, or verified complete questionnaire dictionary.

The companion [schema inventory](schema-inventory.json) records each file's row count, size, and ordered columns. The [field-quality summary](field-quality-summary.csv) contains one row for each of 774 file/field pairs, with empty-string and null counts, distinct-value counts, and diagnostic numeric-parse ranges. Numeric parsing in that CSV is syntactic only; it does not mean the field is a quantitative measure. `scripts/audit_sas_2024.py` regenerates these files and reports structural checks, crop-area arithmetic, candidate production-screening linkage, and the Season B JSON/CSV mirror; its unit tests are under `tests/`.

The core production files are useful for studying crop output, storage, sales, processing/use, and reported loss. The production questionnaire exposes a total lost-quantity variable (`s2q39`) and separate loss quantities for theft, pests, animals, fallen stalks, harvest, transport, storage, processing, packaging, and sales (`s2q41`–`s2q50`). NISR's April 2024 metadata handbook appendix confirms the stage quantities, including storage loss, are in kg; the `s2q39` total-loss question still has no explicit unit in the handbook. The local `s2q47` values include negative quantities, and stage-field sums exceed `s2q39` numerically in a substantial number of rows. Do not yet publish loss rates or sum the stage fields.

The design is a probability survey with weights and clustered/stratified sampling. Unweighted row sums and raw row counts are not national estimates. Season C is a specially restricted sample and should not be compared directly with Seasons A and B without design-aware estimates.

## Workspace and source files

| Season | Module | Local rows | JSON columns, including `id` |
|---|---|---:|---:|
| A | Screening | 54,382 | 46 |
| A | Production | 39,330 | 96 |
| A | Agricultural practice | 17,506 | 59 |
| A | Fertilizer/pesticide | 22,105 | 64 |
| B | Screening | 28,562 | 46 |
| B | Production | 35,584 | 98 |
| B | Agricultural practice | 17,261 | 53 |
| B | Fertilizer/pesticide | 19,965 | 64 |
| C | Screening | 8,195 | 42 |
| C | Production | 1,949 | 97 |
| C | Agricultural practice | 1,632 | 48 |
| C | Fertilizer/pesticide | 2,307 | 61 |

The additional `dataset/publicdataset/sas_2024_seasonB_production.csv` has 35,584 rows and 98 columns. Its header and every cell match `sas_2024_seasonB_production.json` in order. It is a duplicate representation, not an additional sample.

### Source alignment

NISR's SAS 2024 microdata catalog lists 11 files. The local row counts match the catalog's case counts for the 11 corresponding files; for those files, the local JSON schema has one extra column, `id`, beyond the catalog's listed variable count. The local `sas_2024_seasonB_agricultural_practice.json` (17,261 rows, 53 columns) is not listed in that catalog dictionary. Its filename and content look consistent with the other practice modules, but its exact source/version and variable labels remain to be verified before treating it as an official matched release.

Schema comparison confirms that 46 non-`id` field names are shared by the local A, B, and C agricultural-practice extracts. Season B includes `s4q18_4`, which is absent from both A and C, and five `s4q11_2_*` fields that are absent from C. It omits seven `s4q10_2_*`/`s4q12_2_*` fields present in A and `s4q12_2` present in C. These are schema differences only; the B file's labels, response options, and provenance are still unverified.

The source is the NISR [Rwanda Seasonal Agricultural Survey 2024 catalog](https://www.microdata.statistics.gov.rw/index.php/catalog/113), including its [data dictionary](https://www.microdata.statistics.gov.rw/index.php/catalog/113/data_dictionary). NISR describes the survey year as 2023/24: Season A spans September 2023–February 2024, Season B March–June 2024, and Season C July–September 2024 ([NISR annual report](https://www.statistics.gov.rw/statistical-publications/agriculture-environment/seasonal-agricultural-survey-2024-annual-report-2024)). NISR's [2024 metadata handbook](https://statistics.gov.rw/documents/sas-metadata-handbook-2024) includes weighting and indicator methodology and Phase I and Phase II questionnaire appendices.

## Sampling, observation level, and join keys

NISR documents a multiple-frame design: an area frame and a list frame for large-scale farmers (LSFs), with a stratified two-stage design. The public sampling description says 1,200 segments are selected for the area sample, plots are selected through sample points, and the LSF frame complements the area frame. Season C is shorter and uses a restricted set of sub-strata; 946 segments are described for its sample ([NISR sampling metadata](https://www.microdata.statistics.gov.rw/index.php/catalog/113/sampling)). The local Season C screening file has 946 distinct `Segment_ID` values, while the production file has 555; the modules therefore do not share a common row denominator.

The files are module-level extracts, not 12 interchangeable tables of farmers:

- Production records are crop-by-plot records. In each local production file, `Segment_ID` + `s2q1` (plot number) + `s2q4` (crop name) is unique. Different crops in one plot are separate records.
- Screening records hold screening/land-use and crop-area information at a different grain. Several fields encode selections as comma-separated codes, and `CropCategory` may be blank.
- Agricultural-practice records are plot-oriented. Fertilizer/pesticide records repeat plot identifiers where multiple input records are present.
- `id` is a sequential, file-local export row identifier. It resets across files and is not a cross-file join key. Use survey identifiers and an explicitly defined module grain.

All files contain district names; all five provinces and all 30 districts appear in each file. `Segment_ID`, `s1q3` (stratum), and `plot_weight` are important for respecting survey structure. NISR's handbook describes a two-stage area-frame plot weight, adjusted for land-cover factors and overlap with the large-farm sample. The annual report says NISR used SPSS Complex Samples to account for stratification and clustering when calculating sampling errors and coefficients of variation. Before estimating, verify that the local `plot_weight` is the final adjusted weight for each record and determine how list-frame large-scale-farmer records and the report's finite-population correction are represented. Do not simply sum weights and label the result a national estimate ([NISR SAS 2024 annual report](https://statistics.gov.rw/sites/default/files/documents/2025-02/SAS%202024%20Annual.pdf)).

### Weighting method status

NISR's annual report says SPSS Complex Samples was used to account for stratification and clustering when calculating sampling errors and coefficients of variation, and documents the finite-population correction. The local `plot_weight` still needs confirmation as the final adjusted weight across area-frame and large-farmer records.

The annual report defines cultivated crop area from physical plot area and estimated crop share. In the local screening files, `crop_area` (A/B) and `Crop_Area` (C) match `Plot_size_ha × s3q2_1 / 100` for every row where all three values are populated, within an absolute tolerance of 0.0005 ha. The largest observed absolute differences are 0.00046 ha in A, 0.00040 ha in B, and 0.0000006 ha in C. This does not make the field harvested area for every crop: NISR treats harvested area as cultivated area for seasonal crops, while perennial-crop harvested area is adjusted for the share actually harvested. The production-screening crop linkage and perennial harvest-area calculation remain to be confirmed before yield estimates.

The handbook describes multiple-frame sampling with a two-stage area sample and a large-scale-farmer list frame. Area-frame plot weights invert the segment and plot selection probabilities; the final weight then receives land-cover corrections and adjustments for overlap with the large-farm sample. The handbook describes yield estimation from crop production and harvested area at plot level, aggregation to a weighted district yield, and crop production estimation from that yield and harvested crop area. This is the correct methodological direction, but the local `plot_weight` field has not yet been verified as the handbook's final adjusted weight for every frame. The survey's exact variance-estimation specification and local harvested-area field mapping also remain to be checked before implementation.

## Verified variable map

Variable names below are from the local files; labels are cross-checked against NISR's catalog for the corresponding modules.

### Geography and plot context

| Local field(s) | Meaning / use | Notes |
|---|---|---|
| `Segment_ID` | Survey segment identifier (`IDQUEST` in catalog metadata) | Cluster/segment link; not a farmer name. |
| `s1q1`, `s1q2`, `s1q3` | Province, district, stratum | Categorical strings, not numbers. |
| `s1q4`, `s1q6`, `s2q1` | Segment/LSF number, farmer ID/LSF ID, plot number | Do not expose detailed microdata publicly. |
| `s1q7`–`s1q9`, `s1q14`, `s1q17` | Farmer type, gender, age, respondent status, respondent relationship | Potentially sensitive microdata fields. |
| `s2q2` | Physical plot area in square metres in the production dictionary | Keep distinct from crop area; do not use directly as a crop-specific yield denominator. |
| `plot_weight` | Plot weight | Preserve it. Use with strata/cluster/frame information for survey estimates. |
| `s2q2_ha` | Hectare-valued plot-area field in selected practice/input extracts | Present in the local A/B practice and fertilizer/pesticide files and C practice file; absent from production and screening. It is not a crop-specific area join key. |
| `Plot_size_ha`, `s3q2_1`, `crop_area` / `Crop_Area` | Physical plot area (ha), crop share (%), and cultivated crop area in screening extracts | Local area fields match `Plot_size_ha × s3q2_1 / 100` within 0.0005 ha. C uses capitalized `Crop_Area`; neither spelling is a documented harvested-area measure. |

### Production, use, storage, and losses

The production module is the most relevant dataset for the project's core questions:

| Field(s) | NISR label / unit in catalog | Analytical caution |
|---|---|---|
| `s2q4`, `CropCategory` | Crop name/category | `CropCategory` is broader than crop name; some crops in one category can occur in one plot. |
| `s2q19_1`, `s2q19_3`, `s2q20_2` | Harvest unit, quantity already harvested in kg, quantity remaining to be harvested in kg | Keep original unit and standardized kilogram value distinct. |
| `s2q21` | Total quantity of harvest for this season (kg) | Handbook question 2.3.3; keep distinct from the wider crop-season total. |
| `s2q22` | Total quantity of harvest for this crop during the current season (kg) | Handbook question 2.3.4 explicitly includes plots outside the segment. Not interchangeable with `s2q21`; confirm its role before weighting or deriving yield. |
| `s2q25`, `s2q25_1`–`s2q25_3` | Quantity transformed; transformed quantity used as food, drink, or another way (kg) | Describes reported use/processing, not processor capacity, product yield, or profit. |
| `s2q26`–`s2q28` | Quantity sold (kg), market, selling price (RWF/kg) | Price is missing in many records and some zero-price values coexist with positive sales. |
| `s2q29`–`s2q35` | Household use, wages, rent, gifts, exchange, seed, fodder | Use as separate disposition fields; validate reconciliation before summing. |
| `s2q36`–`s2q38` | Quantity stored (kg), facility, quantity in public storage (kg) | The handbook lists `s2q37` response codes 1–4, but local A/B files mix labels with numeric values 12, 13, and 14; NISR's B metadata shows one value 12 with no category label. Do not map those anomalies to a facility type. |
| `s2q39` | Quantity of this crop lost | Catalog metadata calls it continuous/numeric but does not state the unit in its label; the handbook's Phase II questionnaire also gives no unit for total losses. The handbook includes total losses among production uses but that context does not confirm this field's unit. Do not present it as kg until NISR confirms the unit. |
| `s2q41`–`s2q50` | Loss quantity by theft, pest/insect damage, birds/animals, fallen stalks, harvest, transport, storage, processing, packaging, and sales | The handbook's Phase II questionnaire gives the stage quantities in kg, including storage (`s2q47`). Confirm whether categories are mutually exclusive before adding them. |

Agricultural-practice fields include erosion degree, anti-erosion work, land consolidation, agricultural equipment, and irrigation. Fertilizer/pesticide modules include reported use and product/application details. These can support descriptive associations, but not causal claims.

## Data quality findings

### Serialization and missingness

- Every local file is a JSON array of flat objects with a consistent key set within that file. All values are JSON strings; there are no JSON `null` values. Blank responses are empty strings (`""`), so blank means “not populated” and must not be converted to zero without field-specific justification.
- In all files the `id` field is unique. Four Season C screening rows are exact duplicates of another row when `id` is ignored; those should be investigated/deduplicated by a documented rule, not silently dropped.
- Schemas differ across seasons: variable counts change, and some names/casing differ. Season C production, for example, does not have an identical schema to A or B. Build season-aware schema mappings rather than concatenating raw JSON by column position.

### Total reported-loss field (`s2q39`)

The local parse agrees with NISR's published valid/missing case counts and raw means for `s2q39` ([Season A metadata](https://www.microdata.statistics.gov.rw/index.php/catalog/113/datafile/F3/V183), [Season B metadata](https://www.microdata.statistics.gov.rw/index.php/catalog/113/datafile/F6/V388), [Season C metadata](https://www.microdata.statistics.gov.rw/index.php/catalog/113/datafile/F10/V635)).

| Season | Production rows | `s2q39` populated | Blank | Positive values | Zero values | Catalog raw mean* |
|---|---:|---:|---:|---:|---:|---:|
| A | 39,330 | 34,349 | 4,981 (12.7%) | 3,165 | 31,184 | 58.4 |
| B | 35,584 | 34,679 | 905 (2.5%) | 2,192 | 32,487 | 30.3 |
| C | 1,949 | 1,949 | 0 | 164 | 1,785 | 5.8 |

\*The catalog reports an arithmetic mean over its valid microdata cases, not a national, survey-weighted estimate. The unit is not stated in the published `s2q39` label. Season C's restricted sample makes a direct A/B/C comparison inappropriate without proper survey estimation.

### Loss field consistency checks

- NISR's own metadata gives `s2q47` (storage loss) minimums of **-340 in A**, **-3 in B**, and **-2 in C** ([A](https://www.microdata.statistics.gov.rw/index.php/catalog/113/datafile/F3/V191), [B](https://www.microdata.statistics.gov.rw/index.php/catalog/113/datafile/F6/V396), [C](https://www.microdata.statistics.gov.rw/index.php/catalog/113/datafile/F10/V643)). The local files contain 142, 108, and 6 negative values, respectively. Although NISR metadata includes them as valid numeric values, negative quantities are semantically surprising; retain and flag them pending a definition/source check rather than silently clipping or zeroing them.
- The raw numeric sum of `s2q41`–`s2q50` exceeds `s2q39` for 8,069 / 34,349 A records (23.5%), 6,209 / 34,679 B records (17.9%), and 419 / 1,949 C records (21.5%). The stage fields are in kg, while the unit of `s2q39` remains unconfirmed; this is a diagnostic comparison, not proof that either value is invalid. Do not sum stages into a “total loss” until the instrument establishes whether categories overlap or use different denominators.
- `s2q39` exceeds `s2q21` in 199 A, 46 B, and 2 C records, but never exceeds `s2q22` among rows where both are populated. The handbook says the broader `s2q22` crop-season total includes plots outside the segment; this supports keeping the two harvest measures distinct but does not establish the correct loss-rate denominator. Resolve that denominator before calculating a percentage.

### Storage, prices, weights, and other flags

- `s2q37` is populated in 1,598 A, 972 B, and 19 C production records. The handbook documents codes 1–4 (own, public, cooperative/private, other). A/B exports contain human-readable labels plus anomalous values `12`, `13`, and `14` (one each in A; one `12` in B); [NISR's B metadata](https://microdata.statistics.gov.rw/index.php/catalog/113/datafile/F6/V386) also lists a `12` response with no category. Keep these flagged and unmapped pending clarification. Among rows with positive `s2q36` storage quantity, `s2q37` is blank in 254 A and 158 B records; C has 0 such blanks among 19 records.
- `s2q28` has zero price alongside positive `s2q26` sales in 99 A and 300 B rows. Confirm whether zero means a true zero-price transaction, a missing-value convention, or an export issue before valuing sales/losses.
- Screening `plot_weight` is zero in 161 A and 185 B rows. Season A screening also has one row without `Segment_ID` and another row with province coded `0`. These are quality flags whose meaning should be checked against the sampling/extract rules.
- The production field `s2q2` is labeled plot area in square metres. Values above 1,000,000 m² (100 ha) occur in 65 A and 52 B records. Because the design includes an LSF list frame, this is not automatically invalid, but the measure and extreme records should be checked before yield calculations.

## Production-to-screening area linkage

The annual report defines cultivated crop area from physical plot area multiplied by the estimated crop share. This matches the local `crop_area` / `Crop_Area` arithmetic described above within 0.0005 ha. NISR treats harvested area as cultivated area for seasonal crops; perennial crops require adjusting for the share actually harvested ([NISR SAS 2024 annual report](https://statistics.gov.rw/sites/default/files/documents/2025-02/SAS%202024%20Annual.pdf)).

A diagnostic exact-label match of production `Segment_ID + s2q1 + s2q4` to screening `Segment_ID + s2q1 + s3q1` found 39,306 / 39,330 A production rows (99.94%), 15,691 / 35,584 B rows (44.1%), and 1,949 / 1,949 C rows (100%). `plot_weight` values are equal between modules for all candidate-matched rows. The candidate screening crop key is repeated 3,587 times in A, four times in C, and not at all in B, so matching is not universally one-to-one. The apparent row grain also differs: B screening has 28,562 rows and 28,562 unique `(Segment_ID, s2q1)` keys, while B production has 35,584 crop rows over 17,261 such plot keys; A and C screening contain repeated plot keys. This is an observed schema/grain difference, not proof of missing data or a valid alternative join. The check is diagnostic only. Do not attach screening area to B production rows for yield calculations until NISR's B module grain and crop coverage are resolved.

## Best-supported initial analyses

1. **Production and productivity:** estimate crop production and yield from the appropriate plot-level harvest and area variables, using the survey weights and correct frame/stratum/cluster treatment. Keep `s2q21` and `s2q22` distinct until their scopes are verified.
2. **Reported loss patterns:** summarize `s2q39` and the stage fields separately by crop, district, farmer type, and season. Show valid sample sizes, missingness, and the unit/denominator. Treat zero and blank differently.
3. **Storage:** describe storage quantity/facility (`s2q36`–`s2q38`) alongside reported storage-stage loss (`s2q47`), after resolving codes, blanks, and negative values.
4. **Existing processing/use and markets:** describe transformation quantities (`s2q25`), disposition, sales (`s2q26`), and reported prices (`s2q28`). A transparent gross-value scenario may be possible for rows with valid prices, but not net benefit or profitability.
5. **Practice/input associations:** explore how production and reported losses vary with observed practices, irrigation, erosion, and input use. These are cross-sectional associations, not intervention effects.

The files do **not** provide verified storage moisture/temperature, facility capacity/location, cooperative collection volumes, processor capacity, processing yields, processing costs, product demand, transport network, or sufficiently rich time series. They cannot support causal claims that an intervention reduces loss, facility siting, demand forecasts, or processing-profit predictions by themselves. There are district labels but no coordinates or district-boundary file; maps require a separately sourced, documented boundary dataset.

## Machine-learning readiness

The defensible candidate target is **reported crop loss (`s2q39`)**, after confirming its unit, response logic, denominator, and missingness. A baseline regression and a descriptive binary “reported any loss” analysis could be investigated. Neither is ready to be presented as a deployable risk forecast yet.

Key controls if modeling proceeds:

- Exclude `s2q41`–`s2q50` when predicting `s2q39`; they may directly encode the target's components.
- Decide which production fields would genuinely be available at prediction time; avoid using post-outcome or same-questionnaire fields as predictors.
- Split by `Segment_ID` (and consider farmer/plot grouping) to avoid records from the same sampling cluster leaking across train/test sets.
- Respect the survey weights and strata when evaluating population-facing results; report a baseline and uncertainty.
- Keep Season C separate or validate the effect of its different sample before pooling it with A/B.
- Do not define “high risk” with an arbitrary cutoff. Begin with descriptive baselines and only choose a classification threshold if a defensible decision rule exists.

Processing-profit ML is not supported because costs, yields, capacity, and demand are absent. Scenario analysis with explicitly adjustable assumptions is appropriate instead.

## Prioritized next work

1. Archive the official 2024 SAS metadata handbook and questionnaires with checksums; confirm `s2q39`'s unit, response codes, skip patterns, and the Season B practice file's provenance with NISR.
2. Produce a full field-level dictionary and data-quality report for all 12 modules, including missingness by field, domain/code frequencies, value ranges, weight checks, and duplicate-key checks at each module's actual grain.
3. Define canonical season-aware schemas and documented row grains. Keep raw JSON immutable; treat the B CSV as a duplicate source representation.
4. Build survey-aware descriptive indicators for production, storage, losses, and current processing/use. Validate row-level arithmetic and denominators before reporting crop/district rankings.
5. Only after these checks, design an idempotent SQLite ingestion layer and build a baseline model experiment. API and dashboard design should consume the validated indicators, not invent them.

## Runtime/repository readiness

The current machine has Node.js 24.12.0 but no Python runtime (`py -0p` reports no installed Python). A Python standard-library audit command and unit tests have been added, but they have not yet been executed. Until Python is available, the existing metadata outputs have not been regenerated by that command.

Read-only checks against the local files confirmed that all 12 JSON files parse as arrays of consistently shaped objects, each `id` is unique within its file, and all 248,778 rows use strings rather than JSON nulls or other JSON value types. The Season C screening extract has four duplicate rows when the file-local `id` is excluded. The Season B production CSV exactly matches its JSON counterpart across 35,584 rows and 3,487,232 cells. The production key `Segment_ID` + `s2q1` + `s2q4` is unique in each season.

The reported-loss and consistency figures above were rechecked from the three production JSON files. These checks are unweighted data diagnostics, not national estimates. No model, national estimate, backend, frontend, or production database has been created.

NISR's [Microdata Release Policy](https://statistics.gov.rw/documents/microdata-release-policy) states that anonymized microdata access is governed to protect respondent confidentiality. Keep these row-level files out of public deployment; publish appropriately aggregated, disclosure-reviewed indicators and cite the survey/source.
