# Source data handling

Keep original survey files in their existing source folders and do not rewrite them during audits or ingestion. Do not commit respondent-level files or copy them into public deployment artifacts. The SAS 2024 source audit expects the 12 NISR JSON files in `nisrdataset/` and checks the Season B production CSV in `publicdataset/` as a duplicate representation.

The NISR catalog and release policy govern use and redistribution. Consult NISR's current conditions before sharing microdata or derived outputs. Public products should use aggregated, disclosure-reviewed statistics.
