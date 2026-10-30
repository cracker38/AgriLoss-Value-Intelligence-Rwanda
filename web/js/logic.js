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
  const SEARCH_ALIASES = {
    bean: ["bush bean", "climbing bean"],
    beans: ["bush bean", "climbing bean"],
    "bush beans": ["bush bean"],
    banana: ["cooking banana", "dessert banana", "banana for beer"],
    bananas: ["cooking banana", "dessert banana", "banana for beer"],
    beer: ["banana for beer"],
    potato: ["irish potato", "sweet potato"],
    potatoes: ["irish potato", "sweet potato"],
    "irish potatoes": ["irish potato"],
    rice: ["paddy rice"],
    paddy: ["paddy rice"],
    maize: ["maize"],
    corn: ["maize"],
    cassava: ["cassava"],
    wheat: ["wheat"],
    sorghum: ["sorghum"],
    ibigori: ["maize"],
    ibirayi: ["irish potato"],
    imyumbati: ["cassava"],
    umuceri: ["paddy rice"],
    ibishyimbo: ["bush bean", "climbing bean"],
    priority: ["maize", "bush bean", "climbing bean", "irish potato", "paddy rice", "cassava", "wheat", "cooking banana"],
    nst2: ["maize", "bush bean", "climbing bean", "irish potato", "paddy rice", "cassava", "wheat", "cooking banana"],
  };

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

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
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

  function aliasHits(query) {
    const needle = String(query || "").trim().toLowerCase();
    const names = new Set();
    Object.entries(SEARCH_ALIASES).forEach(([key, values]) => {
      if (needle === key || key.includes(needle) || needle.includes(key)) {
        values.forEach((name) => names.add(name));
      }
    });
    return names;
  }

  function searchScore(crop, query) {
    const needle = String(query || "").trim().toLowerCase();
    const name = String(crop.crop || "").toLowerCase();
    let score = 0;
    if (name === needle) score = 100;
    else if (name.startsWith(needle)) score = 82;
    else if (name.includes(needle)) score = 64;
    else if (aliasHits(query).has(name)) score = 58;
    else return 0;
    if (crop.is_priority_crop) score += 4;
    if (isNumber(crop.records)) score += Math.min(6, Math.log10(crop.records + 1));
    return score;
  }

  function searchCrops(crops, query) {
    const needle = String(query || "").trim().toLowerCase();
    const rows = namedCrops(crops);
    if (!needle) return rows;
    return rows
      .map((row) => ({ row, score: searchScore(row, needle) }))
      .filter((item) => item.score > 0)
      .sort((a, b) => b.score - a.score || a.row.crop.localeCompare(b.row.crop))
      .map((item) => item.row);
  }

  function cropByName(crops, name) {
    const decoded = decodeURIComponent(String(name || "")).trim();
    return namedCrops(crops).find((row) => row.crop.toLowerCase() === decoded.toLowerCase()) || null;
  }

  function cropPathway(crop) {
    const values = [
      { id: "storage", label: "Stored more often than processed or sold", short: "Storage-led", share: crop.stored_positive_share },
      { id: "processing", label: "Processed at home more often than stored or sold", short: "Processing-led", share: crop.transformed_positive_share },
      { id: "sales", label: "Sold more often than stored or processed", short: "Sales-led", share: crop.sold_positive_share },
    ].filter((item) => isNumber(item.share));
    if (!values.length) {
      return { id: "unknown", short: "Limited answers", label: "Not enough complete answers to describe after-harvest use.", lead: null, values: [] };
    }
    values.sort((a, b) => b.share - a.share);
    const lead = values[0];
    const second = values[1];
    const gap = second ? lead.share - second.share : lead.share;
    if (lead.share < 0.08) {
      return { id: "thin", short: "Low reported use", label: "Few complete answers reported storing, processing, or selling this harvest.", lead, values, gap };
    }
    if (second && gap < 0.08) {
      return {
        id: "mixed",
        short: "Mixed use",
        label: `${lead.short.replace("-led", "")} and ${second.short.replace("-led", "")} both show up often in this sample.`,
        lead,
        values,
        gap,
      };
    }
    return { id: lead.id, short: lead.short, label: lead.label, lead, values, gap };
  }

  function contrastLines(crop, overall) {
    if (!overall) return [];
    const pairs = [
      ["stored", crop.stored_positive_share, overall.stored_positive_share],
      ["processed", crop.transformed_positive_share, overall.transformed_positive_share],
      ["sold", crop.sold_positive_share, overall.sold_positive_share],
    ];
    return pairs
      .map(([name, cropShare, allShare]) => {
        if (!isNumber(cropShare) || !isNumber(allShare) || allShare <= 0) return null;
        if (cropShare >= allShare * 1.6 && cropShare - allShare >= 0.04) {
          return `${percent(cropShare)} ${name} — higher than the overall sample (${percent(allShare)}).`;
        }
        if (cropShare <= allShare * 0.5 && allShare - cropShare >= 0.04) {
          return `${percent(cropShare)} ${name} — lower than the overall sample (${percent(allShare)}).`;
        }
        return null;
      })
      .filter(Boolean);
  }

  function qualityFlags(crop) {
    const flags = [];
    if (crop.stored_missing_records) flags.push(`${count(crop.stored_missing_records)} missing storage answers`);
    if (crop.storage_loss_negative_records) flags.push(`${count(crop.storage_loss_negative_records)} negative storage-loss values`);
    if (crop.sold_with_zero_price_records) flags.push(`${count(crop.sold_with_zero_price_records)} sales with a zero price`);
    if (crop.sold_with_missing_price_records) flags.push(`${count(crop.sold_with_missing_price_records)} sales with no price`);
    if (crop.public_stored_positive_records) flags.push(`${count(crop.public_stored_positive_records)} public-storage reports`);
    return flags;
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
    const pathway = cropPathway(crop);
    if (track === "storage") {
      if (pathway.id === "sales" || pathway.id === "processing") {
        checks.push(`${crop.crop} is ${pathway.short.toLowerCase()} in this sample. Confirm whether storage is even the local bottleneck before planning a store.`);
      }
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
      if (pathway.id === "storage") {
        checks.push(`${crop.crop} is storage-led in this sample. Confirm that processing or sales is the local issue before planning equipment.`);
      }
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
    return [...new Set(checks)];
  }

  function followUpSignal(crop, overall, track) {
    const reasons = [];
    let points = 0;
    const path = cropPathway(crop);
    if (crop.is_priority_crop) {
      points += 2;
      reasons.push("This crop is among NST2 priority food crops (maize, beans, potatoes, rice, cassava, wheat, bananas).");
    }
    if (track === "storage") {
      if (
        isNumber(crop.stored_positive_share) &&
        isNumber(overall && overall.stored_positive_share) &&
        crop.stored_positive_share >= overall.stored_positive_share * 1.5 &&
        crop.stored_positive_share - overall.stored_positive_share >= 0.03
      ) {
        points += 2;
        reasons.push("Stored harvest is reported more often than in the overall sample.");
      }
      if (isNumber(crop.storage_loss_positive_share) && crop.storage_loss_positive_share >= 0.02) {
        points += 1;
        reasons.push("Storage-stage loss answers are not rare in this crop group.");
      }
      if (path.id === "processing" || path.id === "sales") {
        reasons.push("After-harvest use is not storage-led. Confirm storage is the local bottleneck.");
      }
    } else {
      if (
        isNumber(crop.transformed_positive_share) &&
        isNumber(overall && overall.transformed_positive_share) &&
        crop.transformed_positive_share >= overall.transformed_positive_share * 1.4 &&
        crop.transformed_positive_share - overall.transformed_positive_share >= 0.08
      ) {
        points += 2;
        reasons.push("Home processing is reported more often than in the overall sample.");
      }
      if (
        isNumber(crop.sold_positive_share) &&
        isNumber(overall && overall.sold_positive_share) &&
        crop.sold_positive_share >= Math.max(0.7, overall.sold_positive_share)
      ) {
        points += 1;
        reasons.push("Sales are reported often. Check today’s buyers before treating this as a processing plan.");
      }
      if (path.id === "storage") {
        reasons.push("This crop is storage-led in the sample. Confirm processing is the local issue.");
      }
    }
    if ((crop.stored_missing_records || 0) > 0 || (crop.sold_with_zero_price_records || 0) > 0) {
      reasons.push("Data-quality flags still need a local check.");
    }
    const band = points >= 4 ? "High sample signal" : points >= 2 ? "Moderate sample signal" : "Low sample signal";
    return { points, band, reasons, path };
  }

  function reviewSignal(crop, sortLabel, rank, total) {
    return `${crop.crop} is ${rank} of ${total} named crop groups for “${sortLabel}”. This is a sample signal for follow-up, not a ranking of farmers or a list of projects to build.`;
  }

  function provinceContextText(province) {
    if (!province) return "No province selected. Province numbers are a separate sample summary and are not joined to this crop.";
    return `${province.province}: ${count(province.records)} survey records, and ${percent(province.stored_positive_share)} of complete storage answers reported storing some harvest. These province numbers are not combined with this crop.`;
  }

  function followUpBrief({ crop, track, sortLabel, rank, total, releaseNote, province, localCondition, localNotes, overall }) {
    const title = track === "storage" ? "After harvest: collection and storage" : "Processing and adding value";
    const why = track === "storage" ? storageReading(crop) : valueReading(crop);
    const checks = followUpChecks(crop, track, localCondition || "Not specified");
    const pathway = cropPathway(crop);
    const signal = followUpSignal(crop, overall, track);
    const priority = crop.is_priority_crop
      ? "Yes — this crop is among national priority food crops (maize, beans, potatoes, rice, cassava, wheat, bananas)."
      : "Not listed here as a national priority food crop.";
    return `# AgriLoss follow-up note: ${crop.crop}

## Challenge
${title}

## After-harvest pattern in this sample
${pathway.short}: ${pathway.label}

## Sample follow-up signal
${signal.band} (${signal.points} of 5 sample points). Not a ranking of farmers.
${signal.reasons.map((item) => `- ${item}`).join("\n") || "- No extra sample flags beyond the crop being in the published file."}

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

  function isFeatureCrop(row) {
    const name = String(row.crop || "").toLowerCase();
    if (name.includes("other") || name.includes("specify")) return false;
    return (row.records || 0) >= 400;
  }

  function featuredStories(crops, overall) {
    const focus = namedCrops(crops).filter(isFeatureCrop);
    const stored = rankCrops(focus, "stored_positive_share")[0];
    const processed = rankCrops(focus, "transformed_positive_share")[0];
    const sold = rankCrops(focus, "sold_positive_share")[0];
    return [
      stored && {
        crop: stored,
        kicker: "Highest storage share",
        title: stored.crop,
        text: `${percent(stored.stored_positive_share)} of complete storage answers reported storing some harvest${overall ? `, against ${percent(overall.stored_positive_share)} in the overall sample` : ""}.`,
        href: `#/crop/${slug(stored.crop)}?track=storage`,
      },
      processed && {
        crop: processed,
        kicker: "Highest processing share",
        title: processed.crop,
        text: `${percent(processed.transformed_positive_share)} of complete processing answers reported transforming some harvest.`,
        href: `#/crop/${slug(processed.crop)}?track=value`,
      },
      sold && {
        crop: sold,
        kicker: "Highest sales share",
        title: sold.crop,
        text: `${percent(sold.sold_positive_share)} of complete sales answers reported a sale. That is a market signal in the sample, not a factory plan.`,
        href: `#/crop/${slug(sold.crop)}?track=value`,
      },
    ].filter(Boolean);
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
    escapeHtml,
    namedCrops,
    rankCrops,
    searchCrops,
    cropByName,
    cropPathway,
    contrastLines,
    qualityFlags,
    storageReading,
    valueReading,
    followUpChecks,
    followUpSignal,
    reviewSignal,
    followUpBrief,
    seasonRowsForCrop,
    practicesForCrop,
    marketsForCrop,
    provinceContextText,
    featuredStories,
  };
})(window);
