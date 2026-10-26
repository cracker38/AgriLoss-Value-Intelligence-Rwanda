# Initial research design for SAS 2024

**Status:** analysis specification; no national estimate or model result is produced here.  
**Data period:** NISR Seasonal Agricultural Survey 2024, agricultural year 2023/24.

This specification narrows the first release to questions that the local files can support without filling missing values, inventing units, or treating a sample statistic as a national estimate. It uses the [NISR SAS 2024 data dictionary](https://microdata.statistics.gov.rw/index.php/catalog/113/data_dictionary), the [sampling documentation](https://microdata.statistics.gov.rw/index.php/catalog/113/sampling), the [NISR SAS 2024 annual report](https://statistics.gov.rw/sites/default/files/documents/2025-02/SAS%202024%20Annual.pdf), and the local [dataset audit](dataset-audit-2024.md).

## Observation grain and scope

- Production rows are crop-by-plot records. The observed key `Segment_ID` + `s2q1` + `s2q4` is unique in each local production extract.
- Screening, production, agricultural-practice, and fertilizer/pesticide files have different grains and season-specific schemas. Do not append all modules as if they were one table.
- `id` is a file-local export identifier. It is not a cross-file key. Join modules only after defining the correct survey identifiers and checking each module's multiplicity.
- Season C uses a restricted sample. Keep it separate from A and B unless the survey documentation establishes a valid pooled estimator.
- District comparisons require design-aware estimates. District names alone do not support a map.

## Survey-estimation method and current gate

NISR's 2024 handbook describes an area-frame sample of segments and plots, plus a large-scale-farmer list frame. The area-frame plot weight is based on inverse first- and second-stage selection probabilities, then adjusted for land-cover factors and overlap with the large-farm sample. The handbook's crop-yield method uses crop production and harvested area at plot level, forms a weighted district yield, and estimates crop production using that yield and weighted harvested area. The handbook provides the method; the current exports still require a verified mapping from `plot_weight` and the crop-specific harvested-area measure to that method.

`s2q2` is physical plot area in the production dictionary, while the handbook yield method needs harvested crop area. Screening extracts contain derived area fields, but those cannot be attached to production rows until the crop linkage and seasonal/perennial harvested-area treatment are verified. No weighted total, yield, or variance estimate is released until the local final weights, list-frame treatment, and estimator settings are confirmed.

The annual report documents that cultivated crop area is physical plot area multiplied by crop share, and that NISR used SPSS Complex Samples to account for stratification and clustering when estimating sampling errors and coefficients of variation. The local screening `crop_area` / `Crop_Area` fields match `Plot_size_ha × s3q2_1 / 100` within 0.0005 ha wherever all inputs are present. NISR treats harvested area as cultivated area for seasonal crops; perennial crops require an adjustment for the portion actually harvested. However, the exact production-to-screening crop match is only 44.1% for Season B (versus 99.94% for A and 100% for C), so the crop-area fields are not yet safe to attach to production rows. The local `plot_weight` still needs confirmation as the final adjusted weight across both sampling frames.

The Season B screening file has one row per candidate `(Segment_ID, s2q1)` plot key (28,562 rows/keys), while its production file has 35,584 crop rows over 17,261 such plot keys. This apparent grain difference needs a source-level explanation before a crop-area join is chosen.

## Candidate questions and indicators

| Question | Source fields | Initial treatment | Release gate |
|---|---|---|---|
| Which crops have the most reported production? | `s2q4`, `CropCategory`, `s2q21`, `s2q22`, `plot_weight`, `s1q3`, `Segment_ID` | Profile crop-by-plot records and valid observations; preserve `s2q21` and `s2q22` as separate measures. The handbook maps them to different harvest questions and says the `s2q22` crop-season total includes plots outside the segment. | Confirm their use in the indicator calculation, frame-specific weights, strata, clusters, and variance-estimation method before ranking or calling totals national estimates. |
| How does reported loss vary by crop, district, and season? | `s2q39`, `s2q4`, `s1q2`, `plot_weight`, `s1q3`, `Segment_ID` | Describe valid and blank responses and the distribution of reported values. Keep blank distinct from zero. The published `s2q39` label and handbook questionnaire do not state a unit. | Confirm the unit and denominator with NISR. Do not calculate a loss rate or present weighted totals until survey weights and the appropriate frame are verified. |
| Which loss causes or stages are reported? | `s2q41`–`s2q50` | Report each field separately with its own valid count and range. The handbook questionnaire specifies kg for these stage quantities, including `s2q47`; flag its negative values. | Confirm whether stages overlap. Do not sum stages into a total or treat them as independent causes. |
| What storage is reported, and how does it compare with storage-stage loss? | `s2q36`–`s2q38`, `s2q47` | Describe reported stored quantity, facility response, public-storage quantity, and storage-stage loss separately. Keep empty facility answers, undocumented `s2q37` values, and negative loss values visible as quality flags. | Confirm `s2q37` code anomalies and investigate negative `s2q47` values. Do not infer facility performance or intervention effects from cross-sectional association. |
| What production is already transformed or sold? | `s2q25`–`s2q28` | Describe transformed quantity and its reported uses, quantity sold, price availability, and reported price. Do not treat these fields as processor capacity, yield, or demand. | Confirm the zero-price convention and skip logic. A gross sales or preservation scenario requires a documented crop-specific reference price and explicit assumptions; it is not net benefit or profit. |
| How do reported production or loss vary with agricultural practices and inputs? | Production/loss fields plus verified `s3*` and `s4*` fields | Begin with descriptive, weighted comparisons only after the survey design is implemented. | These are observational associations. They do not estimate causal intervention effects and should not be worded as recommendations without additional evidence. |

NISR's production dictionary labels `s2q21` as total harvest for the season in kilograms and `s2q22` as total harvest for this crop during the current season in kilograms. The handbook's Phase II questionnaire states that the latter includes plots outside the segment, so retain the distinction. NISR labels `s2q36` as quantity stored in kilograms and `s2q38` as quantity in public storage in kilograms. The dictionary label for `s2q47` omits its unit, but the handbook questionnaire specifies the storage-stage quantity in kg. The total loss field `s2q39` remains without an explicit unit in both the dictionary and handbook questionnaire. See the [official Season C production dictionary](https://microdata.statistics.gov.rw/index.php/catalog/113/datafile/F10) and the [2024 metadata handbook](https://statistics.gov.rw/documents/sas-metadata-handbook-2024).

## Estimation and data-quality rules

1. Do not replace empty strings with zero. Report the valid denominator and missing count for every measure.
2. Do not use unweighted row counts or sums as Rwanda, province, or district population estimates.
3. Do not calculate yield from plot area until the area variable's scope and crop-area allocation are verified for crop-by-plot rows.
4. Do not silently discard the four duplicate Season C screening records. Retain them as flagged records until their source and intended duplicate handling are established.
5. Do not merge modules on `id`, or on a partial plot key, without a documented cardinality check.
6. Keep descriptive observations, model predictions, and scenario inputs/results in separate fields and labels.
7. Keep respondent-level microdata out of a public API. Public output requires aggregation and disclosure review under NISR's [Microdata Release Policy](https://statistics.gov.rw/documents/microdata-release-policy).

## ML decision

No supervised model is specified for production yet. `s2q39` is a candidate regression target only after its unit, denominator, and response process are confirmed. A future model must exclude `s2q41`–`s2q50`, establish that every feature is available at the intended prediction time, compare against a simple baseline, and split by survey segment (and farmer where appropriate). Keep Season C separate unless its restricted design can be handled validly. Do not construct a high-risk label using an arbitrary threshold. Processing-profit prediction is unsupported without processing costs, capacity, yield, and demand data.

## Prerequisites for implementation

1. Reproduce the local source audit and run its pytest suite.
2. Review the handbook's questionnaire appendices and the official questionnaire PDFs; confirm `s2q39`'s unit, skip logic, and response codes with NISR where the documents are silent.
3. Confirm the provenance and labels of the local Season B agricultural-practice file.
4. Verify that local `plot_weight` is the final adjusted weight, resolve the area-frame/large-scale-farmer treatment, and reproduce NISR's documented complex-sample variance method and finite-population correction.
5. Turn only cleared indicators into tested analytical functions, then persist their source version, definition, and processing run in SQLite.
