/* ═══════════════════════════════════════════
   main.js — Vidyarthi Portal
   ═══════════════════════════════════════════ */

"use strict";

// ── DOM refs ─────────────────────────────────
const uploadZone     = document.getElementById("uploadZone");
const fileInput      = document.getElementById("fileInput");
const uploadFilename = document.getElementById("uploadFilename");
const btnUpload      = document.getElementById("btnUpload");
const progressWrap   = document.getElementById("progressWrap");
const progressBar    = document.getElementById("progressBar");
const progressLabel  = document.getElementById("progressLabel");

const analyticsSection = document.getElementById("analytics-section");
const summaryGrid      = document.getElementById("summaryGrid");
const studentsSection  = document.getElementById("students-section");
const studentsBody     = document.getElementById("studentsBody");
const searchInput      = document.getElementById("searchInput");

const generateSection  = document.getElementById("generate-section");
const btnGenerate      = document.getElementById("btnGenerate");
const btnDownload      = document.getElementById("btnDownload");
const generateStatus   = document.getElementById("generateStatus");
const genCount         = document.getElementById("genCount");

let chartInstances = {};
let allStudents    = [];

// ── Chart.js palette ─────────────────────────
const PALETTE = [
  "#2176ae","#e07b00","#1a7a4a","#9b3fb5",
  "#c0392b","#16a085","#d35400","#2980b9",
];

// ── Drag-and-drop ─────────────────────────────
uploadZone.addEventListener("dragover", e => {
  e.preventDefault();
  uploadZone.classList.add("drag-over");
});
uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("drag-over"));
uploadZone.addEventListener("drop", e => {
  e.preventDefault();
  uploadZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) handleFileSelected(file);
});
uploadZone.addEventListener("click", e => {
  if (e.target !== fileInput) fileInput.click();
});
fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) handleFileSelected(fileInput.files[0]);
});

function handleFileSelected(file) {
  uploadFilename.textContent = `📎 ${file.name}`;
  btnUpload.disabled = false;
  btnUpload._file = file;
}

// ── Upload & analyse ──────────────────────────
btnUpload.addEventListener("click", async () => {
  const file = btnUpload._file;
  if (!file) return;

  // Progress indicator
  progressWrap.hidden = false;
  animateProgress(0, 40, 600);
  progressLabel.textContent = "Uploading…";
  btnUpload.disabled = true;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res  = await fetch("/upload", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok || data.error) {
      showError(data.error || "Upload failed");
      return;
    }

    animateProgress(40, 100, 400);
    progressLabel.textContent = "Analysing…";
    await sleep(500);

    progressWrap.hidden = true;
    progressBar.style.width = "0";

    renderAnalytics(data.analytics);

  } catch (err) {
    showError("Network error: " + err.message);
  } finally {
    btnUpload.disabled = false;
  }
});

// ── Render analytics ──────────────────────────
function renderAnalytics(a) {
  // Summary cards
  const cards = [
    { label: "Total Students", value: a.total,   cls: "sv-navy"   },
    { label: "Male",           value: a.male,    cls: "sv-blue"   },
    { label: "Female",         value: a.female,  cls: "sv-orange" },
    { label: "Subjects",       value: Object.keys(a.subjects).length, cls: "sv-green" },
    { label: "Avg Age",        value: a.age_stats.avg ?? "—",       cls: "sv-navy"   },
    { label: "Min Age",        value: a.age_stats.min ?? "—",       cls: "sv-blue"   },
    { label: "Max Age",        value: a.age_stats.max ?? "—",       cls: "sv-orange" },
    { label: "Castes",         value: Object.keys(a.caste).length,  cls: "sv-green"  },
  ];

  summaryGrid.innerHTML = cards.map(c =>
    `<div class="summary-card">
       <div class="summary-value ${c.cls}">${c.value}</div>
       <div class="summary-label">${c.label}</div>
     </div>`
  ).join("");

  // Charts
  buildDoughnut("chartGender",   { Male: a.male, Female: a.female });
  buildBar("chartCaste",    a.caste);
  buildDoughnut("chartReligion", a.religion);
  buildBar("chartSubjects", a.subjects);

  // Age distribution
  const ageDist = a.age_stats.distribution;
  const ageLabels = Object.keys(ageDist).sort((x,y)=>x-y);
  const ageValues = ageLabels.map(k => ageDist[k]);
  buildBarRaw("chartAge", ageLabels, ageValues, "Students");

  // Students table
  allStudents = a.students;
  genCount.textContent = a.total;
  renderTable(allStudents);

  // Show sections
  analyticsSection.hidden = false;
  studentsSection.hidden  = false;
  generateSection.hidden  = false;
}

// ── Table rendering ───────────────────────────
function renderTable(students) {
  studentsBody.innerHTML = students.map((s, i) => {
    const gClass = s.gender.toUpperCase() === "M" ? "badge-gender-m" : "badge-gender-f";
    const gLabel = s.gender.toUpperCase() === "M" ? "♂ Male" : "♀ Female";
    const cCls   = `caste-${(s.caste || "gen").toLowerCase()}`;
    return `<tr>
      <td>${s.sr_no || i + 1}</td>
      <td title="${s.name}"><strong>${s.name}</strong></td>
      <td title="${s.father}">${s.father}</td>
      <td><span class="${gClass}">${gLabel}</span></td>
      <td>${s.dob}</td>
      <td><span class="badge-caste ${cCls}">${s.caste}</span></td>
      <td>${s.religion}</td>
      <td>${s.subject}</td>
      <td title="${s.email}" style="font-size:.8rem;color:#555">${s.email}</td>
    </tr>`;
  }).join("");
}

// ── Search ────────────────────────────────────
searchInput.addEventListener("input", () => {
  const q = searchInput.value.toLowerCase();
  const filtered = allStudents.filter(s =>
    Object.values(s).some(v => String(v).toLowerCase().includes(q))
  );
  renderTable(filtered);
});

// ── Generate PDF ─────────────────────────────
btnGenerate.addEventListener("click", async () => {
  setStatus("⏳ Generating profiles… this may take a few seconds.", "status-info");
  btnGenerate.disabled = true;

  try {
    const res  = await fetch("/generate", { method: "POST" });
    const data = await res.json();

    if (!res.ok || data.error) {
      setStatus("❌ Error: " + (data.error || "Generation failed"), "status-err");
      return;
    }
    setStatus("✅ All profiles merged successfully!", "status-ok");
    btnDownload.hidden = false;
  } catch (err) {
    setStatus("❌ Network error: " + err.message, "status-err");
  } finally {
    btnGenerate.disabled = false;
  }
});

btnDownload.addEventListener("click", () => {
  window.location.href = "/download";
});

// ── Chart helpers ─────────────────────────────
function destroyChart(id) {
  if (chartInstances[id]) { chartInstances[id].destroy(); delete chartInstances[id]; }
}

function buildDoughnut(id, dataObj) {
  destroyChart(id);
  const labels = Object.keys(dataObj);
  const values = Object.values(dataObj);
  chartInstances[id] = new Chart(document.getElementById(id), {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: PALETTE, borderWidth: 2, borderColor: "#fff" }],
    },
    options: {
      responsive: true,
      plugins: { legend: { position: "bottom", labels: { font: { size: 11 } } } },
      cutout: "55%",
    },
  });
}

function buildBar(id, dataObj) {
  destroyChart(id);
  const labels = Object.keys(dataObj);
  const values = Object.values(dataObj);
  buildBarRaw(id, labels, values, "Count");
}

function buildBarRaw(id, labels, values, label) {
  destroyChart(id);
  chartInstances[id] = new Chart(document.getElementById(id), {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label,
        data: values,
        backgroundColor: labels.map((_, i) => PALETTE[i % PALETTE.length] + "cc"),
        borderColor:     labels.map((_, i) => PALETTE[i % PALETTE.length]),
        borderWidth: 1.5,
        borderRadius: 5,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { stepSize: 1, font: { size: 11 } } },
        x: { ticks: { font: { size: 11 } } },
      },
    },
  });
}

// ── Utility ──────────────────────────────────
function setStatus(msg, cls) {
  generateStatus.textContent = msg;
  generateStatus.className   = "generate-status " + cls;
}

function showError(msg) {
  progressWrap.hidden = true;
  alert("Error: " + msg);
}

function animateProgress(from, to, ms) {
  const step    = (to - from) / (ms / 16);
  let current   = from;
  const timer = setInterval(() => {
    current += step;
    progressBar.style.width = Math.min(current, to) + "%";
    if (current >= to) clearInterval(timer);
  }, 16);
}

const sleep = ms => new Promise(r => setTimeout(r, ms));
