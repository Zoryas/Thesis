function escapeHtml(value) {
  return String(value || "").replace(/[&<>"]+/g, function(character) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[character];
  });
}

async function enforceAdminSession() {
  const role = sessionStorage.getItem("role");
  if (role !== "admin") {
    window.location.replace("/admin-login");
    return false;
  }
  return true;
}

function getPassageFormState() {
  return {
    title: document.getElementById("passage-title").value.trim(),
    genre: document.getElementById("passage-genre").value.trim(),
    label: document.getElementById("passage-label").value,
    confidence: document.getElementById("passage-confidence").value.trim(),
    text: document.getElementById("passage-text").value.trim(),
    isDraft: document.getElementById("passage-draft").checked,
  };
}

let currentPassageId = null;
let lastPassagePrediction = null;

function updatePassageAnalysisResult(prediction) {
  const result = document.getElementById("passage-analysis-result");
  if (!prediction || !prediction.label) {
    result.textContent = "Prediction unavailable. Analyze the passage to get a result.";
    return;
  }
  const confidence = typeof prediction.confidence === "number" ? prediction.confidence.toFixed(2) : "N/A";
  result.textContent = "Predicted level: " + prediction.label + " — confidence: " + confidence;
}

function resetPassageForm() {
  document.getElementById("passage-title").value = "";
  document.getElementById("passage-genre").value = "Expository";
  document.getElementById("passage-label").value = "EASY";
  document.getElementById("passage-confidence").value = "";
  document.getElementById("passage-text").value = "";
  document.getElementById("passage-draft").checked = false;
  document.getElementById("passage-modal-error").hidden = true;
  lastPassagePrediction = null;
  updatePassageAnalysisResult(null);
}

function openPassageModal(passage) {
  currentPassageId = passage ? passage.id : null;
  document.getElementById("passage-modal-title").textContent = passage ? "Edit Passage" : "Create Passage";
  resetPassageForm();
  if (passage) {
    document.getElementById("passage-title").value = passage.title || "";
    document.getElementById("passage-genre").value = passage.genre || "Expository";
    document.getElementById("passage-label").value = passage.label || "EASY";
    document.getElementById("passage-confidence").value = passage.confidence !== undefined && passage.confidence !== null ? passage.confidence : "";
    document.getElementById("passage-text").value = passage.text || "";
    document.getElementById("passage-draft").checked = Boolean(passage.isDraft);
  }
  const formCard = document.getElementById("passage-form-card");
  formCard.classList.remove("hidden");
  if (formCard && typeof formCard.scrollIntoView === 'function') {
    formCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function closePassageModal() {
  const formCard = document.getElementById("passage-form-card");
  formCard.classList.add("hidden");
  currentPassageId = null;
}

function setPassageError(message) {
  const err = document.getElementById("passage-modal-error");
  err.textContent = message || "Please fix the highlighted fields.";
  err.hidden = false;
}

async function savePassage() {
  const data = getPassageFormState();
  if (!data.title) {
    setPassageError("Passage title is required.");
    return;
  }
  if (!data.text) {
    setPassageError("Passage text is required.");
    return;
  }
  const payload = {
    title: data.title,
    genre: data.genre || "Expository",
    label: data.label || "EASY",
    text: data.text,
    confidence: data.confidence === "" ? null : Number(data.confidence),
    isDraft: data.isDraft,
  };

  try {
    if (currentPassageId) {
      await ReadWiseAPI.updateAdminPassage(currentPassageId, payload);
    } else {
      await ReadWiseAPI.createAdminPassage(payload);
    }
    closePassageModal();
    await loadPassages();
  } catch (error) {
    setPassageError(error.message || "Unable to save passage.");
  }
}

async function analyzePassageText() {
  const text = document.getElementById("passage-text").value.trim();
  if (!text) {
    setPassageError("Passage text is required before analysis.");
    return;
  }
  try {
    const analyzeBtn = document.getElementById("passage-analyze-btn");
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = "Analyzing...";
    lastPassagePrediction = await ReadWiseAPI.predict(text);
    updatePassageAnalysisResult(lastPassagePrediction);
  } catch (error) {
    setPassageError(error.message || "Passage analysis failed.");
  } finally {
    const analyzeBtn = document.getElementById("passage-analyze-btn");
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "Analyze Passage";
  }
}

async function deletePassage(passageId) {
  const confirmed = window.confirm("Delete this passage? This action cannot be undone.");
  if (!confirmed) return;
  try {
    await ReadWiseAPI.deleteAdminPassage(passageId);
    await loadPassages();
  } catch (error) {
    window.alert(error.message || "Unable to delete passage.");
  }
}

function openPassageModalFromButton(button) {
  try {
    const payload = button.dataset.passage ? JSON.parse(decodeURIComponent(button.dataset.passage)) : null;
    if (payload) {
      openPassageModal(payload);
    }
  } catch (error) {
    console.error("Failed to parse passage payload", error);
  }
}

function renderPassageRow(passage, index) {
  var encoded = encodeURIComponent(JSON.stringify(passage));
  return '<tr>' +
    '<td>' + (index + 1) + '</td>' +
    '<td class="col-title" title="' + escapeHtml(passage.title) + '">' + escapeHtml(passage.title) + '</td>' +
    '<td class="col-genre">' + escapeHtml(passage.genre) + '</td>' +
    '<td class="col-level">' + escapeHtml(passage.label) + '</td>' +
    '<td class="col-words">' + escapeHtml(passage.words || 0) + '</td>' +
    '<td class="col-draft">' + (passage.isDraft ? 'Yes' : 'No') + '</td>' +
    '<td class="col-action">' +
      '<button class="btn btn-outline btn-sm edit-btn" type="button" onclick="openPassageModalFromButton(this)" data-passage="' + encoded + '">Edit</button>' +
      '<button class="btn btn-sm btn-secondary delete-btn" type="button" onclick="deletePassage(\'' + escapeHtml(passage.id) + '\')">Delete</button>' +
    '</td>' +
  '</tr>';
}

async function loadPassages() {
  if (!(await enforceAdminSession())) return;
  try {
    const response = await ReadWiseAPI.getAdminPassages();
    const passages = Array.isArray(response) ? response : [];
    const tbody = document.getElementById("passages-table");
    if (!passages.length) {
      tbody.innerHTML = '<tr><td colspan="7">No passages found.</td></tr>';
      return;
    }
    tbody.innerHTML = passages.map(renderPassageRow).join("");
  } catch (error) {
    console.error(error);
    window.location.replace("/admin-login");
  }
}

async function logout() {
  try {
    await ReadWiseAPI.logout();
  } catch (error) {
    console.warn(error);
  }
  sessionStorage.clear();
  window.location.href = "/admin-login";
}

document.getElementById("passage-save-btn").addEventListener("click", savePassage);
document.getElementById("passage-analyze-btn").addEventListener("click", analyzePassageText);

loadPassages();
