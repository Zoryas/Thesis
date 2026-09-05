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

function getStudentFormState() {
  return {
    email: document.getElementById("student-email").value.trim(),
    password: document.getElementById("student-password").value,
    fullName: document.getElementById("student-name").value.trim(),
    grade: document.getElementById("student-grade").value.trim(),
    section: document.getElementById("student-section").value.trim(),
    classLevel: document.getElementById("student-class-level").value,
    preScore: document.getElementById("student-pre-score").value.trim(),
    isActive: document.getElementById("student-active").checked,
  };
}

function resetStudentForm() {
  document.getElementById("student-email").value = "";
  document.getElementById("student-password").value = "";
  document.getElementById("student-name").value = "";
  document.getElementById("student-grade").value = "7";
  document.getElementById("student-section").value = "";
  document.getElementById("student-class-level").value = "EASY";
  document.getElementById("student-pre-score").value = "";
  document.getElementById("student-active").checked = true;
  document.getElementById("student-modal-error").hidden = true;
}

let currentStudentId = null;

function openStudentModal(student) {
  currentStudentId = student ? student.id : null;
  document.getElementById("student-modal-title").textContent = student ? "Edit Student" : "Create Student";
  resetStudentForm();
  if (student) {
    document.getElementById("student-email").value = student.email || "";
    document.getElementById("student-name").value = student.fullName || "";
    document.getElementById("student-grade").value = student.grade || "";
    document.getElementById("student-section").value = student.section || "";
    document.getElementById("student-class-level").value = student.classLevel || "EASY";
    document.getElementById("student-pre-score").value = student.preAssessmentCompleted ? String(student.preScore) : "";
    document.getElementById("student-active").checked = student.isActive;
  }
  const formCard = document.getElementById("student-form-card");
  formCard.classList.remove("hidden");
  if (formCard && typeof formCard.scrollIntoView === 'function') {
    formCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function closeStudentModal() {
  const formCard = document.getElementById("student-form-card");
  formCard.classList.add("hidden");
  currentStudentId = null;
}

function setStudentError(message) {
  const err = document.getElementById("student-modal-error");
  err.textContent = message || "Please fix the highlighted fields.";
  err.hidden = false;
}

function showToast(message, type) {
  try {
    const toast = document.getElementById('global-toast');
    if (!toast) return;
    toast.textContent = message || '';
    toast.className = type === 'error' ? 'error' : 'success';
    toast.style.display = 'block';
    window.clearTimeout(showToast._t);
    showToast._t = window.setTimeout(function() {
      try { toast.style.display = 'none'; } catch (e) {}
    }, 3000);
  } catch (e) {
    // ignore
  }
}

function downloadStudentTemplate() {
  const csv = "fullName,email,password,grade,section,classLevel,preScore\nStudent Name,student@example.com,Password123!,7,MAKADIYOS,,\n";
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "student-import-template.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}

async function importStudents(file) {
  if (!file) return;
  try {
    const result = await ReadWiseAPI.bulkCreateAdminStudents(file);
    const message = result.errorCount
      ? result.createdCount + " students imported; " + result.errorCount + " rows failed."
      : result.createdCount + " students imported successfully.";
    showToast(message, result.errorCount ? "error" : "success");
    await loadStudentRoster();
  } catch (error) {
    showToast(error.message || "Unable to import students.", "error");
  }
}

async function saveStudent() {
  console.debug("admin-students: saveStudent clicked");
  const saveBtn = document.getElementById("student-save-btn");
  if (saveBtn && saveBtn.disabled) {
    // Prevent double-submit when button already disabled
    return;
  }
  let originalBtnText = null;
  if (saveBtn) {
    originalBtnText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";
  }

  const data = getStudentFormState();
  if (!data.email) {
    setStudentError("Student email is required.");
    if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = originalBtnText || "Save"; }
    return;
  }
  if (!data.fullName) {
    setStudentError("Student name is required.");
    if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = originalBtnText || "Save"; }
    return;
  }
  if (!data.grade) {
    setStudentError("Grade is required.");
    if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = originalBtnText || "Save"; }
    return;
  }

  const payload = {
    email: data.email,
    fullName: data.fullName,
    grade: data.grade,
    section: data.section,
    classLevel: data.classLevel,
    isActive: data.isActive,
  };
  if (data.preScore !== "") {
    payload.preScore = Number(data.preScore);
  }
  if (currentStudentId) {
    if (data.password) {
      payload.password = data.password;
    }
  } else {
    if (!data.password) {
      setStudentError("Password is required for new students.");
      if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = originalBtnText || "Save"; }
      return;
    }
    payload.password = data.password;
  }

  try {
    if (currentStudentId) {
      await ReadWiseAPI.updateAdminStudent(currentStudentId, payload);
    } else {
      await ReadWiseAPI.createAdminStudent(payload);
    }
    closeStudentModal();
    await loadStudentRoster();
    showToast('Student saved successfully.', 'success');
  } catch (error) {
    const msg = error && error.message ? error.message : "Unable to save student.";
    setStudentError(msg);
    showToast(msg, 'error');
    // keep the modal open so the admin can correct input
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      try { saveBtn.textContent = originalBtnText || "Save"; } catch (e) {}
    }
  }
}

async function deleteStudent(studentId) {
  const confirmed = window.confirm("Delete this student account? This action cannot be undone.");
  if (!confirmed) return;
  try {
    await ReadWiseAPI.deleteAdminStudent(studentId);
    await loadStudentRoster();
  } catch (error) {
    window.alert(error.message || "Unable to delete student.");
  }
}

function getSelectedStudentIds() {
  return Array.from(document.querySelectorAll(".student-select:checked")).map(function(input) {
    return input.value;
  });
}

function updateStudentSelectionState() {
  const selected = getSelectedStudentIds();
  const deleteButton = document.getElementById("bulk-delete-students-btn");
  const checkboxes = Array.from(document.querySelectorAll(".student-select"));
  const selectAll = document.getElementById("select-all-students");
  deleteButton.disabled = selected.length === 0;
  selectAll.checked = checkboxes.length > 0 && selected.length === checkboxes.length;
  selectAll.indeterminate = selected.length > 0 && selected.length < checkboxes.length;
}

async function deleteSelectedStudents() {
  const studentIds = getSelectedStudentIds();
  if (!studentIds.length) return;
  if (!window.confirm("Delete " + studentIds.length + " selected student account(s)? This action cannot be undone.")) return;
  try {
    const result = await ReadWiseAPI.bulkDeleteAdminStudents(studentIds);
    showToast((result.deleted || studentIds.length) + " student account(s) deleted.", "success");
    await loadStudentRoster();
  } catch (error) {
    showToast(error.message || "Unable to delete selected students.", "error");
  }
}

function openStudentModalFromButton(button) {
  try {
    const payload = button.dataset.student ? JSON.parse(decodeURIComponent(button.dataset.student)) : null;
    if (payload) {
      openStudentModal(payload);
    }
  } catch (error) {
    console.error("Failed to parse student payload", error);
  }
}

function renderStudentRow(student, index) {
  var encoded = encodeURIComponent(JSON.stringify(student));
  return '<tr>' +
    '<td><input class="student-select" type="checkbox" value="' + escapeHtml(student.id) + '" aria-label="Select ' + escapeHtml(student.fullName) + '"></td>' +
    '<td>' + (index + 1) + '</td>' +
    '<td class="col-email" title="' + escapeHtml(student.email) + '">' + escapeHtml(student.email) + '</td>' +
    '<td class="col-name">' + escapeHtml(student.fullName) + '</td>' +
    '<td class="col-grade">' + escapeHtml(student.grade || "-") + ' / ' + escapeHtml(student.section || "-") + '</td>' +
    '<td class="col-level">' + escapeHtml(student.classLevel || "EASY") + '</td>' +
    '<td class="col-score">' + (student.preAssessmentCompleted ? escapeHtml(student.preScore) : 'Pending') + '</td>' +
    '<td class="col-status">' + (student.isActive ? 'Active' : 'Inactive') + '</td>' +
    '<td class="col-action">' +
      '<button class="btn btn-outline btn-sm edit-btn" type="button" onclick="openStudentModalFromButton(this)" data-student="' + encoded + '">Edit</button> ' +
      '<button class="btn btn-sm btn-secondary delete-btn" type="button" onclick="deleteStudent(\'' + escapeHtml(student.id) + '\')">Delete</button>' +
    '</td>' +
  '</tr>';
}

async function loadStudentRoster() {
  if (!(await enforceAdminSession())) return;
  try {
    const response = await ReadWiseAPI.getAdminStudents();
    const students = Array.isArray(response.students) ? response.students : [];
    const tbody = document.getElementById("students-table");
    if (!students.length) {
      tbody.innerHTML = '<tr><td colspan="9">No student records found.</td></tr>';
      return;
    }
    tbody.innerHTML = students.map(renderStudentRow).join("");
    Array.from(document.querySelectorAll(".student-select")).forEach(function(input) {
      input.addEventListener("change", updateStudentSelectionState);
    });
    updateStudentSelectionState();
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

function initAdminStudentsPage() {
  const saveBtn = document.getElementById("student-save-btn");
  if (saveBtn) {
    saveBtn.addEventListener("click", saveStudent);
  }
  document.getElementById("student-bulk-file").addEventListener("change", function(event) {
    importStudents(event.target.files[0]);
    event.target.value = "";
  });
  document.getElementById("select-all-students").addEventListener("change", function(event) {
    Array.from(document.querySelectorAll(".student-select")).forEach(function(input) {
      input.checked = event.target.checked;
    });
    updateStudentSelectionState();
  });
  document.getElementById("bulk-delete-students-btn").addEventListener("click", deleteSelectedStudents);
  loadStudentRoster();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initAdminStudentsPage);
} else {
  initAdminStudentsPage();
}
