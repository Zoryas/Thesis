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

function getTeacherFormState() {
  return {
    email: document.getElementById("teacher-email").value.trim(),
    password: document.getElementById("teacher-password").value,
    fullName: document.getElementById("teacher-name").value.trim(),
    department: document.getElementById("teacher-department").value.trim(),
    isActive: document.getElementById("teacher-active").checked,
  };
}

function resetTeacherForm() {
  document.getElementById("teacher-email").value = "";
  document.getElementById("teacher-password").value = "";
  document.getElementById("teacher-name").value = "";
  document.getElementById("teacher-department").value = "";
  document.getElementById("teacher-active").checked = true;
  document.getElementById("teacher-modal-error").hidden = true;
}

let currentTeacherId = null;

function openTeacherModal(teacher) {
  currentTeacherId = teacher ? teacher.id : null;
  document.getElementById("teacher-modal-title").textContent = teacher ? "Edit Teacher" : "Create Teacher";
  resetTeacherForm();
  if (teacher) {
    document.getElementById("teacher-email").value = teacher.email || "";
    document.getElementById("teacher-name").value = teacher.fullName || "";
    document.getElementById("teacher-department").value = teacher.department || "";
    document.getElementById("teacher-active").checked = teacher.isActive;
  }
  const formCard = document.getElementById("teacher-form-card");
  formCard.classList.remove("hidden");
  if (formCard && typeof formCard.scrollIntoView === 'function') {
    formCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function closeTeacherModal() {
  const formCard = document.getElementById("teacher-form-card");
  formCard.classList.add("hidden");
  currentTeacherId = null;
}

function setTeacherError(message) {
  const err = document.getElementById("teacher-modal-error");
  err.textContent = message || "Please fix the highlighted fields.";
  err.hidden = false;
}

async function saveTeacher() {
  const data = getTeacherFormState();
  if (!data.email) {
    setTeacherError("Teacher email is required.");
    return;
  }
  if (!data.fullName) {
    setTeacherError("Teacher name is required.");
    return;
  }

  const payload = {
    email: data.email,
    fullName: data.fullName,
    department: data.department,
    isActive: data.isActive,
  };
  if (currentTeacherId) {
    if (data.password) {
      payload.password = data.password;
    }
  } else {
    if (!data.password) {
      setTeacherError("Password is required for new teachers.");
      return;
    }
    payload.password = data.password;
  }

  try {
    if (currentTeacherId) {
      await ReadWiseAPI.updateAdminTeacher(currentTeacherId, payload);
    } else {
      await ReadWiseAPI.createAdminTeacher(payload);
    }
    closeTeacherModal();
    await loadTeacherRoster();
  } catch (error) {
    setTeacherError(error.message || "Unable to save teacher.");
  }
}

async function deleteTeacher(teacherId) {
  const confirmed = window.confirm("Delete this teacher account? This action cannot be undone.");
  if (!confirmed) return;
  try {
    await ReadWiseAPI.deleteAdminTeacher(teacherId);
    await loadTeacherRoster();
  } catch (error) {
    window.alert(error.message || "Unable to delete teacher.");
  }
}

function openTeacherModalFromButton(button) {
  try {
    const payload = button.dataset.teacher ? JSON.parse(decodeURIComponent(button.dataset.teacher)) : null;
    if (payload) {
      openTeacherModal(payload);
    }
  } catch (error) {
    console.error("Failed to parse teacher payload", error);
  }
}

function renderTeacherRow(teacher, index) {
  var encoded = encodeURIComponent(JSON.stringify(teacher));
  return '<tr>' +
    '<td>' + (index + 1) + '</td>' +
    '<td>' + escapeHtml(teacher.email) + '</td>' +
    '<td>' + escapeHtml(teacher.fullName) + '</td>' +
    '<td>' + escapeHtml(teacher.department || "-") + '</td>' +
    '<td>' + (teacher.isActive ? 'Active' : 'Inactive') + '</td>' +
    '<td>' +
      '<button class="btn btn-outline btn-sm" type="button" onclick="openTeacherModalFromButton(this)" data-teacher="' + encoded + '">Edit</button> ' +
      '<button class="btn btn-sm btn-secondary" type="button" onclick="deleteTeacher(\'' + escapeHtml(teacher.id) + '\')">Delete</button>' +
    '</td>' +
  '</tr>';
}

async function loadTeacherRoster() {
  if (!(await enforceAdminSession())) return;
  try {
    const response = await ReadWiseAPI.getAdminTeachers();
    const teachers = Array.isArray(response.teachers) ? response.teachers : [];
    const tbody = document.getElementById("teachers-table");
    if (!teachers.length) {
      tbody.innerHTML = '<tr><td colspan="6">No teacher records found.</td></tr>';
      return;
    }
    tbody.innerHTML = teachers.map(renderTeacherRow).join("");
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

document.getElementById("teacher-save-btn").addEventListener("click", saveTeacher);

loadTeacherRoster();
