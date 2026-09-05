function enforceAdminSession() {
  if (sessionStorage.getItem("role") !== "admin") {
    window.location.replace("/admin-login");
    return false;
  }
  return true;
}

function escapeHtml(value) {
  return String(value || "").replace(/[&<>"']/g, function(character) {
    return { "&":"&amp;", "<":"&lt;", ">":"&gt;", "\"":"&quot;", "'":"&#39;" }[character];
  });
}

function setMessage(message, isError) {
  var element = document.getElementById("pre-assessment-message");
  element.textContent = message || "";
  element.hidden = !message;
  element.style.color = isError ? "#c0392b" : "#287a4b";
}

var passages = [];
var selectedPassageIds = { EASY: "", MODERATE: "", HARD: "" };

function renderPassageLibrary() {
  var selected = String(document.getElementById("difficulty-filter").value || "ALL");
  var visible = passages.filter(function(passage) {
    return selected === "ALL" || String(passage.label || "").toUpperCase() === selected;
  });
  visible.sort(function(left, right) {
    var leftUsed = Array.isArray(left.usedWeeks) && left.usedWeeks.length ? 1 : 0;
    var rightUsed = Array.isArray(right.usedWeeks) && right.usedWeeks.length ? 1 : 0;
    if (leftUsed !== rightUsed) return leftUsed - rightUsed;
    return String(left.title || "").localeCompare(String(right.title || ""));
  });
  var grid = document.getElementById("pre-assessment-library");
  if (!visible.length) {
    grid.innerHTML = '<div class="card empty-state"><h3>No passages match this filter</h3><p>Create or publish passages in the Passage Library first.</p></div>';
    return;
  }
  grid.innerHTML = visible.map(function(passage) {
    var level = String(passage.label || "EASY").toUpperCase();
    var isSelected = selectedPassageIds[level] === passage.id;
    var usedWeeks = Array.isArray(passage.usedWeeks) ? passage.usedWeeks : [];
    var weeklyAssigned = usedWeeks.length > 0;
    var preview = String(passage.text || "").slice(0, 220).trim();
    return '<div class="card library-card ' + (isSelected ? "library-card-selected" : "") + '">' +
      '<div class="library-card-copy"><div class="pill-row"><span class="badge ' + badgeClass(level) + '">' + escapeHtml(getClassDisplayName(level)) + '</span><span class="badge badge-primary">' + escapeHtml(passage.genre) + '</span></div>' +
      '<h3 class="library-card-title">' + escapeHtml(passage.title) + '</h3>' +
      '<div class="card-meta-row"><span class="library-card-fact">' + escapeHtml(passage.words || 0) + ' words</span><span class="library-card-fact">~' + escapeHtml(passage.time || 0) + ' min</span></div>' +
      '<p class="library-card-preview">' + escapeHtml(preview) + (preview.length >= 220 ? '...' : '') + '</p>' +
      '<div class="surface-note ' + (weeklyAssigned ? 'surface-note-warn' : '') + '">' + (weeklyAssigned ? 'Assigned in Week ' + escapeHtml(usedWeeks.join(', ')) + ' and cannot be used for pre-assessment.' : 'Available for pre-assessment selection.') + '</div></div>' +
      '<div class="library-card-actions"><button class="btn ' + (isSelected ? 'btn-success' : 'btn-outline') + ' btn-sm" type="button" ' + (weeklyAssigned ? 'disabled' : 'onclick="selectPreAssessmentPassage(\'' + escapeHtml(passage.id) + '\')"') + '>' + (weeklyAssigned ? 'Assigned to Weekly Assessment' : (isSelected ? 'Selected for Pre-Assessment' : 'Select for ' + escapeHtml(getClassDisplayName(level)) + ' Pre-Assessment')) + '</button></div></div>';
  }).join("");
  updateSelectionState();
}

function updateSelectionState() {
  var levels = ["EASY", "MODERATE", "HARD"];
  var selectedCount = levels.filter(function(level) { return Boolean(selectedPassageIds[level]); }).length;
  var saveButton = document.getElementById("save-config-btn");
  var summary = document.getElementById("selection-summary");
  saveButton.disabled = selectedCount !== levels.length;
  summary.textContent = selectedCount === levels.length
    ? "Easy, Moderate, and Difficult passages are selected. Save to apply this pre-assessment."
    : selectedCount + " of 3 levels selected. Choose one passage for each level before saving.";
}

function selectPreAssessmentPassage(passageId) {
  var passage = passages.find(function(item) { return item.id === passageId; });
  if (!passage) return;
  var level = String(passage.label || "EASY").toUpperCase();
  selectedPassageIds[level] = selectedPassageIds[level] === passage.id ? "" : passage.id;
  renderPassageLibrary();
}

async function loadConfig() {
  if (!enforceAdminSession()) return;
  try {
    var results = await Promise.all([ReadWiseAPI.getAdminPassages(), ReadWiseAPI.getPreAssessmentConfig()]);
    passages = Array.isArray(results[0]) ? results[0] : [];
    var config = results[1] && results[1].config;
    if (Array.isArray(config)) {
      config.forEach(function(step) {
        var level = String(step.level || "").toUpperCase();
        if (Object.prototype.hasOwnProperty.call(selectedPassageIds, level)) selectedPassageIds[level] = step.id || "";
      });
    }
    renderPassageLibrary();
    updateSelectionState();
  } catch (error) {
    setMessage(error.message || "Unable to load the pre-assessment configuration.", true);
  }
}

async function saveConfig() {
  try {
    var passageIds = [selectedPassageIds.EASY, selectedPassageIds.MODERATE, selectedPassageIds.HARD];
    if (passageIds.some(function(id) { return !id; })) throw new Error("Choose one passage for each level.");
    await ReadWiseAPI.savePreAssessmentPassages(passageIds);
    setMessage("Pre-assessment saved successfully.", false);
  } catch (error) {
    setMessage(error.message || "Unable to save the pre-assessment.", true);
  }
}

async function logout() {
  try { await ReadWiseAPI.logout(); } catch (error) { console.warn(error); }
  sessionStorage.clear();
  window.location.href = "/admin-login";
}

document.getElementById("difficulty-filter").addEventListener("change", renderPassageLibrary);
document.getElementById("save-config-btn").addEventListener("click", saveConfig);
loadConfig();
