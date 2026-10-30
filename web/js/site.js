(function () {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  let data = null;
  let context = null;
  let charts = [];

  const ROUTES = [
    ["#/", "Home"],
    ["#/crops", "Find a crop"],
    ["#/storage", "Storage"],
    ["#/processing", "Processing"],
    ["#/compare", "Compare"],
    ["#/practices", "Practices & markets"],
    ["#/plan", "Plan a follow-up"],
    ["#/about", "About the numbers"],
  ];

  function releaseNote() {
    if (!data) return "";
    if (data.release_status === "owner_authorized_unreviewed") {
      return "provisional grouped summary; not an official NISR statistic";
    }
    const review = data.review || {};
    return `reviewed by ${review.reviewed_by || "—"} on ${review.reviewed_on || "—"}`;
  }

  function destroyCharts() {
    charts.forEach((chart) => chart.destroy());
    charts = [];
  }

  function barChart(canvasId, labels, values, label, percentAxis) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !window.Chart) return;
    const chart = new Chart(canvas, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label,
          data: values,
          backgroundColor: labels.map((_, index) => (index % 2 ? "#d4a017" : "#157a56")),
          borderRadius: 10,
          maxBarThickness: 42,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: {
            grid: { color: "rgba(16,35,27,0.06)" },
            ticks: {
              callback: (value) => (percentAxis ? `${Math.round(value * 100)}%` : Number(value).toLocaleString()),
            },
          },
        },
      },
    });
    charts.push(chart);
  }

  function meter(share) {
    const width = typeof share === "number" ? Math.max(2, Math.min(100, share * 100)) : 0;
    return `<div class="meter" aria-hidden="true"><span style="width:${width}%"></span></div>`;
  }

  function toast(message) {
    document.querySelectorAll(".toast").forEach((node) => node.remove());
    const note = document.createElement("div");
    note.className = "toast";
    note.textContent = message;
    document.body.appendChild(note);
    setTimeout(() => note.remove(), 2800);
  }

  function navHtml(hash) {
    return ROUTES.map(([href, label]) => {
      const active = hash === href || (href !== "#/" && hash.startsWith(href));
      return `<a href="${href}" class="${active ? "active" : ""}">${label}</a>`;
    }).join("");
  }

  function parseRoute() {
    const raw = location.hash || "#/";
    const [path, query = ""] = raw.split("?");
    const params = Object.fromEntries(new URLSearchParams(query));
    const parts = path.replace(/^#\//, "").split("/").filter(Boolean);
    return { path: path || "#/", parts, params };
  }

  function headerSearch(query) {
    const box = $("#search-results");
    if (!box) return;
    if (!query) {
      box.classList.remove("open");
      box.innerHTML = "";
      return;
    }
    const hits = AgriLoss.searchCrops(data.by_crop, query).slice(0, 8);
    box.classList.add("open");
    if (!hits.length) {
      box.innerHTML = `<div class="empty">No crop matches “${query}”.</div>`;
      return;
    }
    box.innerHTML = hits
      .map(
        (crop, index) =>
          `<a href="#/crop/${AgriLoss.slug(crop.crop)}" class="${index === 0 ? "active" : ""}"><strong>${crop.crop}</strong><br><small>${AgriLoss.count(crop.records)} records · stored ${AgriLoss.percent(crop.stored_positive_share)} · sold ${AgriLoss.percent(crop.sold_positive_share)}</small></a>`
      )
      .join("");
  }

  function homePage() {
    const overall = data.overall;
    const crops = AgriLoss.namedCrops(data.by_crop);
    const stored = AgriLoss.rankCrops(data.by_crop, "stored_positive_share")[0];
    const processed = AgriLoss.rankCrops(data.by_crop, "transformed_positive_share")[0];
    return `
      <section class="hero">
        <div class="eyebrow">NISR 2026 hackathon · Agricultural productivity</div>
        <h1>See what happens after harvest, crop by crop.</h1>
        <p>AgriLoss uses Rwanda’s 2024 Seasonal Agricultural Survey to help farmers, cooperatives, and planners see which crops were stored, processed, or sold — and what to check next. It does not rank farmers or tell anyone to build a store.</p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="#/crops">Search crops</a>
          <a class="btn btn-ghost" href="#/storage">After-harvest storage</a>
          <a class="btn btn-ghost" href="#/processing">Processing and sales</a>
        </div>
        <div class="quick-chips">
          ${["Maize", "Bush bean", "Cassava", "Irish potato", "Paddy rice", "Cooking banana"].map((name) => `<a class="chip" href="#/crop/${AgriLoss.slug(name)}">${name}</a>`).join("")}
        </div>
      </section>
      <div class="notice">This website shows grouped survey summaries from real SAS 2024 records. They are not official national estimates. ${releaseNote()}.</div>
      <section class="section">
        <div class="section-head"><h2>How to use AgriLoss</h2></div>
        <div class="grid grid-3 steps">
          <article class="card"><div class="step-num">1</div><h3>Find your crop</h3><p>Search maize, beans, cassava, or any named crop in the 2024 survey sample.</p></article>
          <article class="card"><div class="step-num">2</div><h3>See what happened after harvest</h3><p>Read, in simple words, how often that crop was stored, processed, or sold.</p></article>
          <article class="card"><div class="step-num">3</div><h3>Download a follow-up note</h3><p>Add your local situation and take a short note to a meeting. It does not approve a project.</p></article>
        </div>
      </section>
      <section class="section grid grid-3">
        <article class="card"><div class="icon-bubble">1</div><h3>Who it is for</h3><p>Farmers, cooperatives, agricultural planners, researchers, and partners who need a first, honest look at the survey.</p></article>
        <article class="card"><div class="icon-bubble">2</div><h3>What you can do</h3><p>Search a crop, compare storage and processing, add your local situation, and download a short follow-up note.</p></article>
        <article class="card"><div class="icon-bubble">3</div><h3>What you should not do</h3><p>Do not treat these shares as Rwanda’s national loss rate, score farmers, or decide where to build a warehouse from this page.</p></article>
      </section>
      <section class="section">
        <h2>What the 2024 survey recorded</h2>
        <div class="grid grid-4">
          <div class="card"><div class="stat-label">Crop records in the sample</div><div class="stat-value">${AgriLoss.count(overall.records)}</div><div class="stat-note">One record is one crop on one plot, not one farmer.</div></div>
          <div class="card"><div class="stat-label">Stored some harvest</div><div class="stat-value">${AgriLoss.percent(overall.stored_positive_share)}</div><div class="stat-note">${AgriLoss.count(overall.stored_positive_records)} complete storage answers.</div></div>
          <div class="card"><div class="stat-label">Processed some harvest</div><div class="stat-value">${AgriLoss.percent(overall.transformed_positive_share)}</div><div class="stat-note">${AgriLoss.count(overall.transformed_positive_records)} complete processing answers.</div></div>
          <div class="card"><div class="stat-label">Sold some harvest</div><div class="stat-value">${AgriLoss.percent(overall.sold_positive_share)}</div><div class="stat-note">${AgriLoss.count(overall.sold_positive_records)} complete sales answers.</div></div>
        </div>
      </section>
      <section class="section grid grid-2">
        <article class="card">
          <h3>After harvest: collection and storage</h3>
          <p>NST2 aims to cut food-crop losses after harvest from 13.8% to 4.8%. This site does not measure that target. It shows which crops in the survey already report storing harvest or losing it in storage.</p>
          <p style="margin-top:.7rem">${stored ? `<strong>${stored.crop}</strong> has the highest share of storage answers in this sample (${AgriLoss.percent(stored.stored_positive_share)}).` : ""}</p>
          <p style="margin-top:.9rem"><a class="btn btn-dark" href="#/storage">Open storage</a></p>
        </article>
        <article class="card">
          <h3>Processing and adding value</h3>
          <p>Some harvest is turned into food or drink at home, and some is sold. That is a starting point for value-addition follow-up — not a business plan.</p>
          <p style="margin-top:.7rem">${processed ? `<strong>${processed.crop}</strong> has the highest share of processing answers in this sample (${AgriLoss.percent(processed.transformed_positive_share)}).` : ""}</p>
          <p style="margin-top:.9rem"><a class="btn btn-dark" href="#/processing">Open processing</a></p>
        </article>
      </section>
      <section class="section">
        <div class="section-head">
          <div>
            <h2>Named crops in this release</h2>
            <p class="stat-note">${crops.length} crop groups have enough complete answers to publish a share.</p>
          </div>
          <a class="btn btn-line" href="#/crops">See all crops</a>
        </div>
        <div class="crop-list">
          ${crops.slice(0, 8).map(cropCard).join("")}
        </div>
      </section>
    `;
  }

  function cropCard(crop) {
    return `<a class="crop-row" href="#/crop/${AgriLoss.slug(crop.crop)}">
      <div><strong>${crop.crop}</strong>${crop.is_priority_crop ? '<span class="pill">National priority crop</span>' : ""}<small style="display:block;color:var(--muted)">${AgriLoss.count(crop.records)} survey records</small></div>
      <div><span class="stat-label">Stored</span><div>${AgriLoss.percent(crop.stored_positive_share)}</div>${meter(crop.stored_positive_share)}</div>
      <div><span class="stat-label">Processed</span><div>${AgriLoss.percent(crop.transformed_positive_share)}</div>${meter(crop.transformed_positive_share)}</div>
      <div><span class="stat-label">Sold</span><div>${AgriLoss.percent(crop.sold_positive_share)}</div>${meter(crop.sold_positive_share)}</div>
    </a>`;
  }

  function cropsPage(params) {
    const query = params.q || "";
    const filter = params.filter || "all";
    let rows = AgriLoss.searchCrops(data.by_crop, query);
    if (filter === "priority") rows = rows.filter((row) => row.is_priority_crop);
    rows = rows.sort((a, b) => a.crop.localeCompare(b.crop));
    return `
      <section class="hero">
        <div class="eyebrow">Crop directory</div>
        <h1>Find a crop in the 2024 survey.</h1>
        <p>Type a crop name. You will see how often that crop was stored, processed, or sold in this sample.</p>
      </section>
      <section class="section">
        <form class="filters" id="crop-filter-form">
          <input name="q" value="${query.replace(/"/g, "&quot;")}" placeholder="Search maize, beans, cassava…" aria-label="Search crops">
          <select name="filter" aria-label="Filter crops">
            <option value="all" ${filter === "all" ? "selected" : ""}>All named crops</option>
            <option value="priority" ${filter === "priority" ? "selected" : ""}>National priority food crops</option>
          </select>
          <button class="btn btn-dark" type="submit">Search</button>
        </form>
        <div class="crop-list" id="crop-list">${rows.map(cropCard).join("") || `<div class="card">No crops match that search.</div>`}</div>
      </section>
    `;
  }

  function trackPage(track) {
    const sorts = track === "storage" ? AgriLoss.STORAGE_SORTS : AgriLoss.VALUE_SORTS;
    const route = parseRoute();
    const sortId = route.params.sort || sorts[0].id;
    const sort = sorts.find((item) => item.id === sortId) || sorts[0];
    const ranked = AgriLoss.rankCrops(data.by_crop, sort.field);
    const title = track === "storage" ? "After harvest: collection and storage" : "Processing and adding value";
    const intro =
      track === "storage"
        ? "This page uses the survey questions on stored quantity and loss during storage. It does not measure Rwanda’s national post-harvest loss target."
        : "This page uses the survey questions on harvest that was processed and harvest that was sold. It is not a mill or factory siting tool.";
    return `
      <section class="hero">
        <div class="eyebrow">${track === "storage" ? "Track: storage" : "Track: processing"}</div>
        <h1>${title}</h1>
        <p>${intro}</p>
      </section>
      <section class="section">
        <div class="sort-chips" id="sort-chips">
          ${sorts.map((item) => `<a class="${item.id === sort.id ? "active" : ""}" href="#/${track === "storage" ? "storage" : "processing"}?sort=${item.id}">${item.label}</a>`).join("")}
        </div>
        <form class="filters hidden" id="sort-form">
          <label>Sort crops by
            <select name="sort">${sorts.map((item) => `<option value="${item.id}" ${item.id === sort.id ? "selected" : ""}>${item.label}</option>`).join("")}</select>
          </label>
        </form>
        <div class="crop-list">
          ${ranked.map((crop, index) => `<a class="crop-row" href="#/crop/${AgriLoss.slug(crop.crop)}?track=${track}&sort=${sort.id}">
            <div><strong>${index + 1}. ${crop.crop}</strong>${crop.is_priority_crop ? '<span class="pill">National priority crop</span>' : ""}</div>
            <div><span class="stat-label">${sort.label}</span><div>${sort.field.includes("records") ? AgriLoss.count(crop[sort.field]) : sort.field.includes("kg") ? AgriLoss.kg(crop[sort.field]) : AgriLoss.percent(crop[sort.field])}</div></div>
            <div><span class="stat-label">Stored</span><div>${AgriLoss.percent(crop.stored_positive_share)}</div></div>
            <div><span class="stat-label">Processed / sold</span><div>${AgriLoss.percent(crop.transformed_positive_share)} / ${AgriLoss.percent(crop.sold_positive_share)}</div></div>
          </a>`).join("")}
        </div>
      </section>
    `;
  }

  function cropPage(name, params) {
    const crop = AgriLoss.cropByName(data.by_crop, name);
    if (!crop) return `<section class="section card"><h2>Crop not found</h2><p>Use search to pick a named crop from the published sample.</p></section>`;
    const track = params.track === "processing" ? "value" : params.track === "storage" ? "storage" : "storage";
    const sorts = track === "storage" ? AgriLoss.STORAGE_SORTS : AgriLoss.VALUE_SORTS;
    const sort = sorts.find((item) => item.id === params.sort) || sorts[0];
    const ranked = AgriLoss.rankCrops(data.by_crop, sort.field);
    const rank = ranked.findIndex((row) => row.crop === crop.crop) + 1;
    const seasons = AgriLoss.seasonRowsForCrop(data.by_season_crop, crop.crop);
    const practiceNames = [...new Set((data.by_crop_practice || []).filter((row) => row.crop === crop.crop).map((row) => row.practice))];
    const markets = AgriLoss.marketsForCrop(data.by_crop_market_channel, crop.crop);
    const provinces = data.by_province || [];
    return `
      <section class="hero">
        <div class="crumb"><a href="#/crops">Crops</a> / ${crop.crop}</div>
        <div class="eyebrow">Crop file</div>
        <h1>${crop.crop}</h1>
        <p>${crop.is_priority_crop ? "This crop is among national priority food crops." : "This crop is published in the SAS 2024 sample."} ${AgriLoss.count(crop.records)} survey records. Figures below are unweighted sample descriptions.</p>
      </section>
      <section class="section grid grid-4">
        <div class="card"><div class="stat-label">Stored some harvest</div><div class="stat-value">${AgriLoss.percent(crop.stored_positive_share)}</div><div class="stat-note">${AgriLoss.count(crop.stored_positive_records)} records</div></div>
        <div class="card"><div class="stat-label">Loss in storage</div><div class="stat-value">${AgriLoss.percent(crop.storage_loss_positive_share)}</div><div class="stat-note">${AgriLoss.count(crop.storage_loss_negative_records)} negative values flagged</div></div>
        <div class="card"><div class="stat-label">Processed some harvest</div><div class="stat-value">${AgriLoss.percent(crop.transformed_positive_share)}</div><div class="stat-note">Food ${AgriLoss.percent(crop.transformed_food_positive_share)} · drink ${AgriLoss.percent(crop.transformed_drink_positive_share)}</div></div>
        <div class="card"><div class="stat-label">Sold some harvest</div><div class="stat-value">${AgriLoss.percent(crop.sold_positive_share)}</div><div class="stat-note">Typical harvest ${AgriLoss.kg(crop.median_reported_harvest_kg)}</div></div>
      </section>
      <section class="section grid grid-2">
        <article class="card"><h3>In plain language: storage</h3><p class="reading">${AgriLoss.storageReading(crop)}</p></article>
        <article class="card"><h3>In plain language: processing and sales</h3><p class="reading">${AgriLoss.valueReading(crop)}</p></article>
      </section>
      <section class="section card">
        <h3>How this crop changes by season</h3>
        <p class="stat-note">Season C is a smaller, restricted sample and should not be compared directly with A and B.</p>
        <div class="chart-box"><canvas id="season-crop-chart"></canvas></div>
        <div class="table-wrap" style="margin-top:1rem">
          <table><thead><tr><th>Season</th><th>Records</th><th>Stored</th><th>Processed</th><th>Sold</th></tr></thead>
          <tbody>${seasons.map((row) => `<tr><td>${row.season}</td><td>${AgriLoss.count(row.records)}</td><td>${AgriLoss.percent(row.stored_positive_share)}</td><td>${AgriLoss.percent(row.transformed_positive_share)}</td><td>${AgriLoss.percent(row.sold_positive_share)}</td></tr>`).join("") || `<tr><td colspan="5">No season-by-crop summary for this crop.</td></tr>`}</tbody></table>
        </div>
      </section>
      ${
        markets.length
          ? `<section class="section card"><h3>Where this crop was reported as sold (Season A)</h3>
        <p class="stat-note">These are 2024 survey answers, not today’s market prices.</p>
        <div class="table-wrap"><table><thead><tr><th>Sales place</th><th>Records with a sale</th><th>Typical amount sold</th><th>Typical reported price</th></tr></thead>
        <tbody>${markets.map((row) => `<tr><td>${row.market_channel}</td><td>${AgriLoss.count(row.positive_sales_records)}</td><td>${AgriLoss.kg(row.median_positive_sales_kg)}</td><td>${row.median_positive_price_rwf_per_kg != null ? `${AgriLoss.count(row.median_positive_price_rwf_per_kg)} RWF/kg` : "—"}</td></tr>`).join("")}</tbody></table></div></section>`
          : ""
      }
      ${
        practiceNames.length
          ? `<section class="section card"><h3>Practices reported with this crop (Season A)</h3>
        <p class="stat-note">These are side-by-side sample descriptions, not proof that a practice caused storage or sales.</p>
        <label>Practice <select id="practice-select">${practiceNames.map((name) => `<option>${name}</option>`).join("")}</select></label>
        <div class="table-wrap" style="margin-top:0.8rem" id="practice-table"></div></section>`
          : ""
      }
      <section class="section card" id="plan-box">
        <h3>Add your local situation and download a note</h3>
        <p class="stat-note">${rank ? AgriLoss.reviewSignal(crop, sort.label, rank, ranked.length) : "This crop is in the published sample."}</p>
        <form class="plan-form" id="brief-form">
          <label>Challenge
            <select name="track">
              <option value="storage" ${track === "storage" ? "selected" : ""}>After-harvest storage</option>
              <option value="value" ${track === "value" ? "selected" : ""}>Processing and adding value</option>
            </select>
          </label>
          <label>Province context (separate sample summary)
            <select name="province">
              <option value="">Not specified</option>
              ${provinces.map((row) => `<option value="${row.province}">${row.province}</option>`).join("")}
            </select>
          </label>
          <label>Local issue to investigate
            <select name="condition" id="condition-select"></select>
          </label>
          <label>Your notes (do not write names or phone numbers)
            <textarea name="notes" maxlength="500" rows="3"></textarea>
          </label>
          <button class="btn btn-dark" type="submit">Download follow-up note</button>
        </form>
        <ul class="checks" id="check-list"></ul>
      </section>
    `;
  }

  function comparePage() {
    return `
      <section class="hero">
        <div class="eyebrow">Sample map</div>
        <h1>Compare seasons and provinces.</h1>
        <p>Each chart is its own summary. Changing season does not change the crop list. Province numbers are not combined with crop numbers.</p>
      </section>
      <section class="section grid grid-2">
        <article class="card"><h3>Records by season</h3><div class="chart-box"><canvas id="season-chart"></canvas></div></article>
        <article class="card"><h3>Stored harvest by province</h3><div class="chart-box"><canvas id="province-chart"></canvas></div></article>
      </section>
      <section class="section grid grid-2">
        <article class="card"><h3>Crops most often stored</h3><div class="chart-box"><canvas id="stored-chart"></canvas></div></article>
        <article class="card"><h3>Crops most often processed</h3><div class="chart-box"><canvas id="processed-chart"></canvas></div></article>
      </section>
      <section class="section card">
        <h3>Reported storage place</h3>
        <p class="stat-note">Most records have no facility answer. Unmapped codes stay unmapped.</p>
        <div class="table-wrap"><table><thead><tr><th>Facility answer</th><th>Records</th></tr></thead>
        <tbody>${(data.by_storage_facility || []).map((row) => `<tr><td>${row.facility}</td><td>${AgriLoss.count(row.records)}</td></tr>`).join("")}</tbody></table></div>
      </section>
    `;
  }

  function practicesPage() {
    const names = [...new Set((data.by_crop_practice || []).map((row) => row.practice))];
    const crops = [...new Set((data.by_crop_practice || []).map((row) => row.crop))].sort();
    return `
      <section class="hero">
        <div class="eyebrow">Season A only</div>
        <h1>Practices, inputs, and sales places.</h1>
        <p>These tables sit next to production answers for Season A. They do not prove that a practice caused storage or sales. Season B practice files are not used because their source is not confirmed.</p>
      </section>
      <section class="section card">
        <div class="filters">
          <label>Practice or input <select id="link-practice">${names.map((name) => `<option>${name}</option>`).join("")}</select></label>
          <label>Crop <select id="link-crop">${crops.map((name) => `<option>${name}</option>`).join("")}</select></label>
        </div>
        <div id="link-table"></div>
      </section>
      <section class="section card">
        <h3>Reported sales places (Season A)</h3>
        <p class="stat-note">Prices are historical 2024 reports, not a live market.</p>
        <div class="table-wrap"><table><thead><tr><th>Sales place</th><th>Records</th><th>Share with a sale</th><th>Typical amount sold</th><th>Typical price</th></tr></thead>
        <tbody>${(data.by_market_channel || []).map((row) => `<tr><td>${row.market_channel}</td><td>${AgriLoss.count(row.production_records)}</td><td>${AgriLoss.percent(row.positive_sales_share)}</td><td>${AgriLoss.kg(row.median_positive_sales_kg)}</td><td>${row.median_positive_price_rwf_per_kg != null ? `${AgriLoss.count(row.median_positive_price_rwf_per_kg)} RWF/kg` : "—"}</td></tr>`).join("")}</tbody></table></div>
      </section>
    `;
  }

  function planPage() {
    const crops = AgriLoss.namedCrops(data.by_crop).sort((a, b) => a.crop.localeCompare(b.crop));
    return `
      <section class="hero">
        <div class="eyebrow">Follow-up note</div>
        <h1>Plan the next check, not the building.</h1>
        <p>Choose a crop and a challenge, add your local situation, and download a note you can take to a cooperative meeting or a planner. The note does not approve a project.</p>
      </section>
      <section class="section card">
        <form class="plan-form" id="standalone-plan">
          <label>Crop
            <select name="crop">${crops.map((row) => `<option>${row.crop}</option>`).join("")}</select>
          </label>
          <label>Challenge
            <select name="track">
              <option value="storage">After-harvest storage</option>
              <option value="value">Processing and adding value</option>
            </select>
          </label>
          <p><button class="btn btn-dark" type="submit">Open this crop and write the note</button></p>
        </form>
      </section>
    `;
  }

  function aboutPage() {
    const seasons = data.by_season || [];
    return `
      <section class="hero">
        <div class="eyebrow">Methods in plain language</div>
        <h1>How to read these numbers.</h1>
        <p>Every figure on this website comes from grouped NISR SAS 2024 production records. Empty answers stay empty. No farmer names are shown.</p>
      </section>
      <section class="section grid grid-2">
        <article class="card">
          <h3>What a number means</h3>
          <ul>
            <li><strong>Survey record:</strong> one crop grown on one plot.</li>
            <li><strong>Complete answer:</strong> the question was filled in. Blank is not treated as zero.</li>
            <li><strong>Share stored / processed / sold:</strong> among complete answers, the share that reported an amount greater than zero.</li>
            <li><strong>Typical amount:</strong> the middle value among amounts greater than zero.</li>
            <li><strong>Unweighted:</strong> every record counts the same. Official national figures use survey weights. These pages do not.</li>
          </ul>
        </article>
        <article class="card">
          <h3>What this website will not do</h3>
          <ul>
            <li>Estimate national crop loss or yield.</li>
            <li>Rank or target farmers.</li>
            <li>Prove that a practice caused a result.</li>
            <li>Tell you to build a store, dryer, or factory.</li>
            <li>Show live market prices or profit.</li>
          </ul>
        </article>
      </section>
      <section class="section card">
        <h3>Season snapshot</h3>
        <div class="table-wrap"><table><thead><tr><th>Season</th><th>Records</th><th>Stored</th><th>Processed</th><th>Sold</th></tr></thead>
        <tbody>${seasons.map((row) => `<tr><td>${row.season}${row.season === "C" ? " (restricted)" : ""}</td><td>${AgriLoss.count(row.records)}</td><td>${AgriLoss.percent(row.stored_positive_share)}</td><td>${AgriLoss.percent(row.transformed_positive_share)}</td><td>${AgriLoss.percent(row.sold_positive_share)}</td></tr>`).join("")}</tbody></table></div>
      </section>
      <section class="section card">
        <h3>Sources</h3>
        <p>Survey data: <a href="https://microdata.statistics.gov.rw/index.php/catalog/113" target="_blank" rel="noopener noreferrer">NISR SAS 2024 catalog</a>. Policy context: NST2, Vision 2050, and PSTA 5. Those policy rates are not calculated from this sample.</p>
      </section>
    `;
  }

  function bindCropsForm() {
    const form = $("#crop-filter-form");
    if (!form) return;
    const list = $(".crop-list");
    const paint = () => {
      let rows = AgriLoss.searchCrops(data.by_crop, form.q.value);
      if (form.filter.value === "priority") rows = rows.filter((row) => row.is_priority_crop);
      rows = rows.sort((a, b) => a.crop.localeCompare(b.crop));
      list.innerHTML = rows.map(cropCard).join("") || `<div class="card">No crops match that search.</div>`;
    };
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      location.hash = `#/crops?q=${encodeURIComponent(form.q.value.trim())}&filter=${form.filter.value}`;
    });
    form.filter.addEventListener("change", paint);
    form.q.addEventListener("input", paint);
  }

  function bindSortForm(track) {
    const form = $("#sort-form");
    if (!form) return;
    form.sort.addEventListener("change", () => {
      location.hash = `#/${track}?sort=${form.sort.value}`;
    });
  }

  function conditionOptions(track) {
    return track === "storage"
      ? ["Not specified", "Storage capacity", "Collection or transport", "Facility condition", "Other / unknown"]
      : ["Not specified", "Processing equipment / capacity", "Product quality / yield", "Market access / prices", "Other / unknown"];
  }

  function bindCropPage(crop) {
    const trackSelect = $("select[name='track']");
    const condition = $("#condition-select");
    const list = $("#check-list");
    function refreshChecks() {
      const track = trackSelect.value;
      condition.innerHTML = conditionOptions(track).map((name) => `<option>${name}</option>`).join("");
      const checks = AgriLoss.followUpChecks(crop, track, condition.value);
      list.innerHTML = checks.map((item) => `<li>${item}</li>`).join("");
    }
    if (trackSelect) {
      trackSelect.addEventListener("change", refreshChecks);
      condition.addEventListener("change", refreshChecks);
      refreshChecks();
    }
    const form = $("#brief-form");
    if (form) {
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        const track = form.track.value;
        const sorts = track === "storage" ? AgriLoss.STORAGE_SORTS : AgriLoss.VALUE_SORTS;
        const ranked = AgriLoss.rankCrops(data.by_crop, sorts[0].field);
        const rank = ranked.findIndex((row) => row.crop === crop.crop) + 1;
        const province = (data.by_province || []).find((row) => row.province === form.province.value);
        const markdown = AgriLoss.followUpBrief({
          crop,
          track,
          sortLabel: sorts[0].label,
          rank: rank || 1,
          total: ranked.length,
          releaseNote: releaseNote(),
          province,
          localCondition: form.condition.value,
          localNotes: form.notes.value,
        });
        const blob = new Blob([markdown], { type: "text/markdown" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `agriloss-${track}-${crop.crop.toLowerCase().replace(/\s+/g, "-")}.md`;
        link.click();
        toast("Follow-up note downloaded. It is a checklist, not a project approval.");
      });
    }
    const practiceSelect = $("#practice-select");
    if (practiceSelect) {
      const renderPractice = () => {
        const rows = AgriLoss.practicesForCrop(data.by_crop_practice, crop.crop, practiceSelect.value);
        $("#practice-table").innerHTML = `<table><thead><tr><th>Answer</th><th>Records</th><th>Stored</th><th>Processed</th><th>Sold</th></tr></thead><tbody>${rows.map((row) => `<tr><td>${row.status}</td><td>${AgriLoss.count(row.records)}</td><td>${AgriLoss.percent(row.stored_positive_share)}</td><td>${AgriLoss.percent(row.transformed_positive_share)}</td><td>${AgriLoss.percent(row.sold_positive_share)}</td></tr>`).join("")}</tbody></table>`;
      };
      practiceSelect.addEventListener("change", renderPractice);
      renderPractice();
    }
    const seasons = AgriLoss.seasonRowsForCrop(data.by_season_crop, crop.crop);
    if (seasons.length) {
      barChart("season-crop-chart", seasons.map((row) => `Season ${row.season}`), seasons.map((row) => row.stored_positive_share || 0), "Share stored", true);
    }
  }

  function afterRender(route) {
    bindCropsForm();
    if (route.path.startsWith("#/storage")) bindSortForm("storage");
    if (route.path.startsWith("#/processing")) bindSortForm("processing");
    if (route.parts[0] === "crop") {
      const crop = AgriLoss.cropByName(data.by_crop, decodeURIComponent(route.parts[1] || ""));
      if (crop) bindCropPage(crop);
    }
    if (route.path === "#/compare") {
      barChart("season-chart", (data.by_season || []).map((row) => `Season ${row.season}`), (data.by_season || []).map((row) => row.records), "Records", false);
      const provinces = (data.by_province || []).filter((row) => row.stored_positive_share != null);
      barChart("province-chart", provinces.map((row) => row.province), provinces.map((row) => row.stored_positive_share), "Stored share", true);
      const stored = AgriLoss.rankCrops(data.by_crop, "stored_positive_share").slice(0, 8);
      barChart("stored-chart", stored.map((row) => row.crop), stored.map((row) => row.stored_positive_share), "Stored", true);
      const processed = AgriLoss.rankCrops(data.by_crop, "transformed_positive_share").slice(0, 8);
      barChart("processed-chart", processed.map((row) => row.crop), processed.map((row) => row.transformed_positive_share), "Processed", true);
    }
    if (route.path === "#/practices") {
      const render = () => {
        const practice = $("#link-practice").value;
        const crop = $("#link-crop").value;
        const rows = AgriLoss.practicesForCrop(data.by_crop_practice, crop, practice);
        $("#link-table").innerHTML = rows.length
          ? `<table><thead><tr><th>Answer</th><th>Records</th><th>Stored</th><th>Processed</th><th>Sold</th></tr></thead><tbody>${rows.map((row) => `<tr><td>${row.status}</td><td>${AgriLoss.count(row.records)}</td><td>${AgriLoss.percent(row.stored_positive_share)}</td><td>${AgriLoss.percent(row.transformed_positive_share)}</td><td>${AgriLoss.percent(row.sold_positive_share)}</td></tr>`).join("")}</tbody></table>`
          : `<p>No published Yes/No comparison for that crop and practice.</p>`;
      };
      $("#link-practice").addEventListener("change", render);
      $("#link-crop").addEventListener("change", render);
      render();
    }
    const plan = $("#standalone-plan");
    if (plan) {
      plan.addEventListener("submit", (event) => {
        event.preventDefault();
        location.hash = `#/crop/${AgriLoss.slug(plan.crop.value)}?track=${plan.track.value}`;
      });
    }
  }

  function render() {
    if (!data) return;
    destroyCharts();
    const route = parseRoute();
    $("#main-nav").innerHTML = navHtml(route.path.startsWith("#/crop") ? "#/crops" : route.path);
    const view = $("#view");
    if (route.parts[0] === "crop") view.innerHTML = cropPage(decodeURIComponent(route.parts[1] || ""), route.params);
    else if (route.path.startsWith("#/crops")) view.innerHTML = cropsPage(route.params);
    else if (route.path.startsWith("#/storage")) view.innerHTML = trackPage("storage");
    else if (route.path.startsWith("#/processing")) view.innerHTML = trackPage("value");
    else if (route.path.startsWith("#/compare")) view.innerHTML = comparePage();
    else if (route.path.startsWith("#/practices")) view.innerHTML = practicesPage();
    else if (route.path.startsWith("#/plan")) view.innerHTML = planPage();
    else if (route.path.startsWith("#/about")) view.innerHTML = aboutPage();
    else view.innerHTML = homePage();
    afterRender(route);
    window.scrollTo(0, 0);
  }

  async function boot() {
    try {
      if (window.AGRILOSS_DATA) {
        data = window.AGRILOSS_DATA;
      } else {
        const response = await fetch("public_data/dashboard_aggregates.json");
        if (!response.ok) throw new Error("Could not load survey summaries.");
        data = await response.json();
      }
      try {
        const ctx = await fetch("public_data/national_context.json");
        if (ctx.ok) context = await ctx.json();
      } catch (error) {
        context = null;
      }
      render();
    } catch (error) {
      $("#view").innerHTML = `<section class="section card"><h2>The survey file could not be loaded</h2><p>${error.message}</p><p>Open this site through XAMPP at <code>http://localhost/AgriLoss/</code> so the data file can be read.</p></section>`;
    }
  }

  window.addEventListener("hashchange", render);
  document.addEventListener("DOMContentLoaded", () => {
    const input = $("#global-search");
    input.addEventListener("input", () => headerSearch(input.value));
    input.addEventListener("keydown", (event) => {
      const links = $$("#search-results a");
      const current = $("#search-results a.active");
      const index = links.indexOf(current);
      if (event.key === "ArrowDown" && links.length) {
        event.preventDefault();
        const next = links[Math.min(links.length - 1, index + 1)] || links[0];
        links.forEach((node) => node.classList.remove("active"));
        next.classList.add("active");
      } else if (event.key === "ArrowUp" && links.length) {
        event.preventDefault();
        const prev = links[Math.max(0, index - 1)] || links[0];
        links.forEach((node) => node.classList.remove("active"));
        prev.classList.add("active");
      } else if (event.key === "Enter") {
        event.preventDefault();
        const chosen = $("#search-results a.active") || $("#search-results a");
        if (chosen) location.hash = chosen.getAttribute("href");
        else location.hash = `#/crops?q=${encodeURIComponent(input.value)}`;
        $("#search-results").classList.remove("open");
      }
    });
    document.addEventListener("click", (event) => {
      if (!event.target.closest(".search")) $("#search-results").classList.remove("open");
    });
    $("#menu-toggle").addEventListener("click", () => $("#main-nav").classList.toggle("open"));
    boot();
  });
})();
