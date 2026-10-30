(function (global) {
  const POOLED = "Other or unreported crops (pooled)";
  const NST2 = new Set([
    "Maize",
    "Bush bean",
    "Climbing bean",
    "Irish potato",
    "Paddy rice",
    "Cassava",
    "Wheat",
    "Cooking banana",
    "Dessert banana",
    "Banana for beer",
  ]);
  const STORAGE_SORTS = [
    { id: "stored_share", label: "Most often stored", field: "stored_positive_share" },
    { id: "storage_loss", label: "Most storage-stage loss reports", field: "storage_loss_positive_share" },
    { id: "stored_count", label: "Most records that stored some harvest", field: "stored_positive_records" },
    { id: "stored_missing", label: "Most missing storage answers", field: "stored_missing_share" },
  ];
  const VALUE_SORTS = [
    { id: "transformed", label: "Most often processed at home", field: "transformed_positive_share" },
    { id: "sold", label: "Most often sold", field: "sold_positive_share" },
    { id: "harvest", label: "Highest typical harvest reported", field: "median_reported_harvest_kg" },
  ];

  function isNumber(value) {
    return typeof value === "number" && Number.isFinite(value);
  }

  function percent(value) {
    return isNumber(value) ? `${(value * 100).toFixed(1)}%` : "—";
  }

  function kg(value) {
    return isNumber(value) ? `${Math.round(value).toLocaleString()} kg` : "—";
  }

  function count(value) {
    return isNumber(value) ? Math.round(value).toLocaleString() : "0";
  }

  function slug(name) {
    return encodeURIComponent(String(name));
  }

  function namedCrops(crops) {
    return (crops || [])
      .filter((row) => row.crop && row.crop !== POOLED)
      .filter(
        (row) =>
          isNumber(row.stored_positive_share) ||
          isNumber(row.transformed_positive_share) ||
          isNumber(row.sold_positive_share) ||
          isNumber(row.positive_reported_loss_share)
      )
      .map((row) => ({
        ...row,
        stored_missing_share: row.records ? (row.stored_missing_records || 0) / row.records : null,
        is_priority_crop: NST2.has(row.crop),
      }));
  }

  function rankCrops(crops, field) {
    return namedCrops(crops)
      .filter((row) => isNumber(row[field]))
      .sort((a, b) => {
        if (b[field] !== a[field]) return b[field] - a[field];
        return (b.records || 0) - (a.records || 0);
      });
  }

  function searchCrops(crops, query) {
    const needle = String(query || "").trim().toLowerCase();
    const rows = namedCrops(crops);
    if (!needle) return rows;
    return rows.filter((row) => {
      const hay = `${row.crop} ${row.is_priority_crop ? "priority nst2 maize beans rice" : ""}`.toLowerCase();
      return hay.includes(needle);
    });
  }

  function cropByName(crops, name) {
    return namedCrops(crops).find((row) => row.crop === name) || null;
  }

  function storageReading(crop) {
    const parts = [
      `In the 2024 agricultural survey sample, ${crop.crop} stored some harvest in ${percent(crop.stored_positive_share)} of complete storage answers (${count(crop.stored_positive_records)} of ${count(crop.stored_reported_records)}). When something was stored, the middle amount was ${kg(crop.stored_median_positive_kg)}.`,
      `Loss during storage was reported in ${percent(crop.storage_loss_positive_share)} of complete storage-loss answers (${count(crop.storage_loss_positive_records)} records). ${count(crop.storage_loss_negative_records)} answers have a negative number; those stay visible as a data-quality flag.`,
    ];
    if (crop.public_stored_positive_records) {
      parts.push(
        `${count(crop.public_stored_positive_records)} records reported using public storage. That is a small count and is not a reason to place a warehouse.`
      );
    }
    if (crop.stored_positive_share === 0 && crop.storage_loss_positive_share > 0) {
      parts.push(
        "This crop group shows storage-stage loss but almost no stored quantity. Check how the questions were skipped before calling this a storage gap."
      );
    }
    parts.push("These figures describe survey records. They are not Rwanda’s national food-loss rate.");
    return parts.join(" ");
  }

  function valueReading(crop) {
    return [
      `In the 2024 agricultural survey sample, ${crop.crop} was processed or transformed in ${percent(crop.transformed_positive_share)} of complete processing answers (${count(crop.transformed_positive_records)} records). When processing was reported, the middle amount was ${kg(crop.transformed_median_positive_kg)}.`,
      `${percent(crop.sold_positive_share)} of complete sales answers reported a sale (${count(crop.sold_positive_records)} records). When a sale was reported, the middle amount was ${kg(crop.sold_median_positive_kg)}.`,
      `Among records with a sale, ${count(crop.sold_with_positive_price_records)} also reported a price, ${count(crop.sold_with_zero_price_records)} reported a zero price, and ${count(crop.sold_with_missing_price_records)} had no price. Zero prices next to sales need a check before anyone values the crop.`,
      `The middle harvest reported was ${kg(crop.median_reported_harvest_kg)} per crop record. That is not yield, profit, or factory demand.`,
    ].join(" ");
  }

  function followUpChecks(crop, track, localCondition) {
    const checks = [];
    if (track === "storage") {
      if (crop.stored_missing_records) {
        checks.push(`Check missing storage answers: ${count(crop.stored_missing_records)} crop records have no stored-quantity answer.`);
      }
      if (crop.storage_loss_negative_records) {
        checks.push(`Review ${count(crop.storage_loss_negative_records)} negative storage-loss numbers before using them.`);
      }
      if (crop.public_stored_positive_records) {
        checks.push("Compare reported public-storage use with local stores and collection points.");
      }
      if (!checks.length) {
        checks.push("Compare this survey snapshot with local storage space and peak-season volumes. The survey does not measure store size.");
      }
      const extra = {
        "Storage capacity": "Compare the survey snapshot with local storage space and peak-season volume. The survey does not measure store size.",
        "Collection or transport": "Check collection distances, transport costs, and road access locally. Those are not in this survey summary.",
        "Facility condition": "Inspect store condition locally. Survey answers about facility type do not measure condition.",
        "Other / unknown": "Check the extra local issue in the field. It is not measured in this survey summary.",
      };
      if (extra[localCondition]) checks.push(extra[localCondition]);
    } else {
      if (crop.sold_with_zero_price_records) {
        checks.push(`Check ${count(crop.sold_with_zero_price_records)} sales with a zero price before valuing output.`);
      }
      if (crop.sold_with_missing_price_records) {
        checks.push(`Check price coverage: ${count(crop.sold_with_missing_price_records)} sales have no reported price.`);
      }
      checks.push("Confirm today’s buyer prices, demand, processing yield, and costs with local operators. The 2024 survey is historical and does not show profit.");
      const extra = {
        "Processing equipment / capacity": "Check equipment, conversion yield, and running costs with processors. The survey does not measure them.",
        "Product quality / yield": "Check buyer quality rules and processing yield with operators. Those are not in this summary.",
        "Market access / prices": "Check today’s buyer prices and sales outlets locally. Survey prices are from 2024, not a live market feed.",
        "Other / unknown": "Check the extra local issue in the field. It is not measured in this survey summary.",
      };
      if (extra[localCondition]) checks.push(extra[localCondition]);
    }
    return checks;
  }

  function reviewSignal(crop, sortLabel, rank, total) {
    return `${crop.crop} is ${rank} of ${total} named crop groups for “${sortLabel}”. This is a sample signal for follow-up, not a ranking of farmers or a list of projects to build.`;
  }

  function provinceContextText(province) {
    if (!province) return "No province selected. Province numbers are a separate sample summary and are not joined to this crop.";
    return `${province.province}: ${count(province.records)} survey records, and ${percent(province.stored_positive_share)} of complete storage answers reported storing some harvest. These province numbers are not combined with this crop.`;
  }

  function followUpBrief({ crop, track, sortLabel, rank, total, releaseNote, province, localCondition, localNotes }) {
    const title = track === "storage" ? "After harvest: collection and storage" : "Processing and adding value";
    const why = track === "storage" ? storageReading(crop) : valueReading(crop);
    const checks = followUpChecks(crop, track, localCondition || "Not specified");
    const priority = crop.is_priority_crop
      ? "Yes — this crop is among national priority food crops (maize, beans, potatoes, rice, cassava, wheat, bananas)."
      : "Not listed here as a national priority food crop.";
    return `# AgriLoss follow-up note: ${crop.crop}

## Challenge
${title}

## Why this crop is on the list
${reviewSignal(crop, sortLabel, rank, total)}

## What the 2024 survey sample shows
${why}

## Place context
${provinceContextText(province)}

## Local issue you entered
- Issue: ${localCondition || "Not specified"}
- Notes: ${localNotes || "None"}

## What to check next
${checks.map((item) => `- ${item}`).join("\n")}

## Sample snapshot
- Crop: ${crop.crop}
- National priority food crop: ${priority}
- Survey records: ${count(crop.records)}
- Stored some harvest: ${count(crop.stored_positive_records)} · ${percent(crop.stored_positive_share)} of complete answers
- Storage-stage loss: ${count(crop.storage_loss_positive_records)} · ${percent(crop.storage_loss_positive_share)}
- Processed some harvest: ${count(crop.transformed_positive_records)} · ${percent(crop.transformed_positive_share)}
- Sold some harvest: ${count(crop.sold_positive_records)} · ${percent(crop.sold_positive_share)}
- Typical harvest reported: ${kg(crop.median_reported_harvest_kg)}

## What this note is not
This is not a national estimate, a ranking of farmers, a cause of loss, or advice to build a store or factory.

Source: NISR Rwanda Seasonal Agricultural Survey 2024. Status: ${releaseNote}
`;
  }

  function seasonRowsForCrop(seasonCrops, cropName) {
    return (seasonCrops || []).filter((row) => row.crop === cropName);
  }

  function practicesForCrop(practiceRows, cropName, practiceName) {
    return (practiceRows || []).filter(
      (row) => row.crop === cropName && (!practiceName || row.practice === practiceName)
    );
  }

  function marketsForCrop(marketRows, cropName) {
    return (marketRows || []).filter((row) => row.crop === cropName);
  }

  global.AgriLoss = {
    POOLED,
    NST2,
    STORAGE_SORTS,
    VALUE_SORTS,
    percent,
    kg,
    count,
    slug,
    namedCrops,
    rankCrops,
    searchCrops,
    cropByName,
    storageReading,
    valueReading,
    followUpChecks,
    reviewSignal,
    followUpBrief,
    seasonRowsForCrop,
    practicesForCrop,
    marketsForCrop,
    provinceContextText,
  };
})(window);
