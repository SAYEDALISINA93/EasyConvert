const FORMATS = [
  { id: "md", label: "Markdown", ext: "md" },
  { id: "pdf", label: "PDF", ext: "pdf" },
  { id: "docx", label: "Word", ext: "docx" },
  { id: "html", label: "HTML", ext: "html" },
  { id: "epub", label: "EPUB", ext: "epub" },
];

const EXT_TO_FORMAT = {
  md: "md", markdown: "md",
  pdf: "pdf",
  docx: "docx", doc: "docx",
  html: "html", htm: "html",
  epub: "epub",
};

const dropZone = document.getElementById("drop-zone");
const dropInner = document.getElementById("drop-inner");
const fileInput = document.getElementById("file-input");
const fileChip = document.getElementById("file-chip");
const chipExt = document.getElementById("chip-ext");
const chipName = document.getElementById("chip-name");
const chipClear = document.getElementById("chip-clear");
const formatGrid = document.getElementById("format-grid");
const convertBtn = document.getElementById("convert-btn");
const convertLabel = document.getElementById("convert-btn-label");
const statusLine = document.getElementById("status-line");
const ledgerRows = document.getElementById("ledger-rows");

let selectedFile = null;
let selectedFormat = null;

function renderFormatGrid() {
  formatGrid.innerHTML = "";
  const srcFmt = selectedFile ? EXT_TO_FORMAT[selectedFile.name.split(".").pop().toLowerCase()] : null;

  FORMATS.forEach((f) => {
    const btn = document.createElement("button");
    btn.className = "format-option";
    btn.textContent = f.label;
    btn.type = "button";

    const disabled = srcFmt === f.id;
    if (disabled) btn.classList.add("disabled");
    if (selectedFormat === f.id && !disabled) btn.classList.add("selected");

    btn.addEventListener("click", () => {
      if (disabled) return;
      selectedFormat = f.id;
      renderFormatGrid();
      updateConvertButton();
    });

    formatGrid.appendChild(btn);
  });
}

function updateConvertButton() {
  if (!selectedFile) {
    convertBtn.disabled = true;
    convertLabel.textContent = "SELECT A FILE TO BEGIN";
    return;
  }
  if (!selectedFormat) {
    convertBtn.disabled = true;
    convertLabel.textContent = "CHOOSE AN OUTPUT FORMAT";
    return;
  }
  convertBtn.disabled = false;
  const targetLabel = FORMATS.find((f) => f.id === selectedFormat).label;
  convertLabel.textContent = `CONVERT TO ${targetLabel.toUpperCase()}`;
}

function setFile(file) {
  const ext = file.name.split(".").pop().toLowerCase();
  if (!EXT_TO_FORMAT[ext]) {
    setStatus(`Unsupported file type: .${ext}`, "err");
    return;
  }
  selectedFile = file;
  selectedFormat = null;
  chipExt.textContent = ext.toUpperCase();
  chipName.textContent = file.name;
  fileChip.hidden = false;
  dropInner.hidden = true;
  setStatus("");
  renderFormatGrid();
  updateConvertButton();
}

function clearFile() {
  selectedFile = null;
  selectedFormat = null;
  fileInput.value = "";
  fileChip.hidden = true;
  dropInner.hidden = false;
  renderFormatGrid();
  updateConvertButton();
}

function setStatus(msg, kind) {
  statusLine.textContent = msg;
  statusLine.className = "status-line" + (kind ? " " + kind : "");
}

function addLedgerRow(srcName, targetLabel, url, downloadName) {
  const empty = ledgerRows.querySelector(".ledger-empty");
  if (empty) empty.remove();

  const row = document.createElement("div");
  row.className = "ledger-row";
  row.innerHTML = `
    <span>${srcName}</span>
    <span class="ledger-arrow">→</span>
    <span>${targetLabel}</span>
    <a class="ledger-download" href="${url}" download="${downloadName}">download</a>
  `;
  ledgerRows.prepend(row);
}

// --- drag & drop wiring ---

["dragenter", "dragover"].forEach((evt) =>
  dropInner.addEventListener(evt, (e) => {
    e.preventDefault();
    dropInner.classList.add("drag-over");
  })
);
["dragleave", "drop"].forEach((evt) =>
  dropInner.addEventListener(evt, (e) => {
    e.preventDefault();
    dropInner.classList.remove("drag-over");
  })
);
dropInner.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
});
dropInner.addEventListener("click", (e) => {
  if (e.target.tagName !== "LABEL") fileInput.click();
});
fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) setFile(fileInput.files[0]);
});
chipClear.addEventListener("click", clearFile);

// --- convert action ---

convertBtn.addEventListener("click", async () => {
  if (!selectedFile || !selectedFormat) return;
  convertBtn.disabled = true;
  const originalLabel = convertLabel.textContent;
  convertLabel.textContent = "CONVERTING…";
  setStatus("Running pandoc / extractor…");

  try {
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("target", selectedFormat);

    const res = await fetch("/api/convert", { method: "POST", body: formData });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `Server error (${res.status})`);
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const stem = selectedFile.name.replace(/\.[^.]+$/, "");
    const targetFmt = FORMATS.find((f) => f.id === selectedFormat);
    const downloadName = `${stem}.${targetFmt.ext}`;

    setStatus(`Done. ${downloadName} is ready.`, "ok");
    addLedgerRow(selectedFile.name, targetFmt.label, url, downloadName);

    // auto-trigger download
    const a = document.createElement("a");
    a.href = url;
    a.download = downloadName;
    a.click();
  } catch (err) {
    console.error(err);
    setStatus(String(err.message || err).slice(0, 300), "err");
  } finally {
    convertBtn.disabled = false;
    updateConvertButton();
  }
});

renderFormatGrid();
updateConvertButton();
