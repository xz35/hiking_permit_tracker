(async function () {
  const root = document.getElementById("calendar-root");
  const filterSelect = document.getElementById("permit-filter");
  const lastRefresh = document.getElementById("last-refresh");
  const primaryCount = document.getElementById("primary-count");
  const sourceLink = document.getElementById("source-link");

  const state = {
    snapshot: null,
    status: null,
    filter: "all",
  };

  filterSelect.addEventListener("change", () => {
    state.filter = filterSelect.value;
    renderCalendar();
  });

  try {
    const [snapshot, status] = await Promise.all([
      fetchJson(window.WHITNEY_CONFIG.dataUrl),
      fetchJson(window.WHITNEY_CONFIG.statusUrl),
    ]);
    state.snapshot = snapshot;
    state.status = status;
    renderHeader();
    renderCalendar();
  } catch (error) {
    const card = document.createElement("div");
    card.className = "error-card";
    card.textContent = `Unable to load permit data: ${error.message}`;
    root.replaceChildren(card);
  }

  function renderHeader() {
    lastRefresh.textContent = formatTimestamp(state.status.last_successful_poll_at);
    primaryCount.textContent = String(state.snapshot.summary.primary_match_count);

    const anchor = document.createElement("a");
    anchor.href = state.snapshot.public_permit_url;
    anchor.textContent = "Recreation.gov";
    anchor.target = "_blank";
    anchor.rel = "noreferrer";
    sourceLink.replaceChildren(anchor);
  }

  function renderCalendar() {
    if (!state.snapshot) {
      return;
    }

    const recordsByDate = groupRecordsByDate(state.snapshot.records, state.filter);
    const months = state.snapshot.source.months.map(parseMonth);
    const monthCards = months.map((month) => createMonthCard(month, recordsByDate));
    root.replaceChildren(...monthCards);
  }

  function createMonthCard(month, recordsByDate) {
    const card = document.createElement("article");
    card.className = "month-card";

    const title = document.createElement("h2");
    title.className = "month-title";
    title.textContent = month.label;

    const weekdayRow = document.createElement("div");
    weekdayRow.className = "weekday-row";
    ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].forEach((weekday) => {
      const span = document.createElement("span");
      span.textContent = weekday;
      weekdayRow.appendChild(span);
    });

    const grid = document.createElement("div");
    grid.className = "month-grid";

    for (let index = 0; index < month.firstWeekday; index += 1) {
      const pad = document.createElement("div");
      pad.className = "day-pad";
      grid.appendChild(pad);
    }

    for (let day = 1; day <= month.daysInMonth; day += 1) {
      const cellDate = `${month.year}-${String(month.month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
      const cell = document.createElement("article");
      const records = recordsByDate.get(cellDate) || [];
      const hasMatch = records.some((record) => record.is_primary_match);
      cell.className = `day-cell${hasMatch ? " match" : ""}`;

      const dayNumber = document.createElement("div");
      dayNumber.className = "day-number";
      dayNumber.textContent = String(day);
      cell.appendChild(dayNumber);

      const meta = document.createElement("div");
      meta.className = "day-meta";

      if (records.length === 0) {
        meta.appendChild(createPill("", "empty"));
      } else {
        records
          .sort(sortRecords)
          .forEach((record) => meta.appendChild(createRecordPill(record)));
      }

      const footnote = document.createElement("div");
      footnote.className = "day-footnote";
      footnote.textContent = hasMatch ? "Preferred overnight date" : weekdayLabel(cellDate);
      meta.appendChild(footnote);

      cell.appendChild(meta);
      grid.appendChild(cell);
    }

    card.append(title, weekdayRow, grid);
    return card;
  }

  function createRecordPill(record) {
    const capacityText = `${record.available_capacity}/${record.total_capacity}`;
    const label = `${labelForPermit(record.permit_type)} ${capacityText}`;
    let className = record.permit_type;
    if (record.is_primary_match) {
      className += " match";
    }
    return createPill(label, className);
  }

  function createPill(text, className) {
    const pill = document.createElement("div");
    pill.className = `permit-pill ${className}`;
    pill.textContent = text;
    return pill;
  }

  function groupRecordsByDate(records, filter) {
    const grouped = new Map();
    records.forEach((record) => {
      if (filter !== "all" && record.permit_type !== filter) {
        return;
      }
      if (record.available_capacity === 0) {
        return;
      }
      const current = grouped.get(record.entry_date) || [];
      current.push(record);
      grouped.set(record.entry_date, current);
    });
    return grouped;
  }

  function sortRecords(left, right) {
    if (left.is_primary_match !== right.is_primary_match) {
      return left.is_primary_match ? -1 : 1;
    }
    if (left.available_capacity !== right.available_capacity) {
      return right.available_capacity - left.available_capacity;
    }
    return left.permit_type.localeCompare(right.permit_type);
  }

  function labelForPermit(permitType) {
    return permitType === "overnight" ? "Overnight" : "Day-use";
  }

  function weekdayLabel(dateText) {
    return new Intl.DateTimeFormat("en-US", { weekday: "long" }).format(new Date(`${dateText}T12:00:00`));
  }

  function parseMonth(monthText) {
    const [yearText, monthTextPart] = monthText.split("-");
    const year = Number(yearText);
    const month = Number(monthTextPart);
    const first = new Date(year, month - 1, 1);
    const last = new Date(year, month, 0);
    return {
      year,
      month,
      label: new Intl.DateTimeFormat("en-US", { month: "long", year: "numeric" }).format(first),
      firstWeekday: first.getDay(),
      daysInMonth: last.getDate(),
    };
  }

  function formatTimestamp(timestamp) {
    return new Intl.DateTimeFormat("en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(timestamp));
  }

  async function fetchJson(url) {
    const response = await fetch(url, { headers: { Accept: "application/json" } });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  }
})();
