function escapeHtml(value) {
  return String(value || "").replace(/[&<>\"]+/g, function(character) {
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

async function logout() {
  try {
    if (window.ReadWiseAPI && typeof ReadWiseAPI.logout === "function") {
      await ReadWiseAPI.logout();
    }
  } catch (error) {
    console.warn("Logout request failed:", error);
  }
  sessionStorage.clear();
  window.location.href = "/admin-login";
}

function resetAdminForm() {
  document.getElementById("admin-email").value = "";
  document.getElementById("admin-password").value = "";
  document.getElementById("admin-role").value = "admin";
  document.getElementById("admin-active").checked = true;
  document.getElementById("admin-modal-error").hidden = true;
}

let currentAdminId = null;
let currentAdminUserId = null;

async function loadCurrentAdminUser() {
  try {
    const result = await ReadWiseAPI.me({ forceRefresh: true });
    if (result && result.user && result.user.id) {
      currentAdminUserId = result.user.id;
    }
  } catch (error) {
    console.warn("Unable to load current admin user", error);
  }
}

function openAdminModal(admin) {
  currentAdminId = admin ? admin.id : null;
  document.getElementById("admin-modal-title").textContent = admin ? "Edit Admin" : "Create Admin";
  resetAdminForm();

  if (admin) {
    document.getElementById("admin-email").value = admin.email || "";
    document.getElementById("admin-role").value = admin.role || "admin";
    document.getElementById("admin-active").checked = admin.isActive;
  }

  const formCard = document.getElementById("admin-form-card");
  formCard.classList.remove("hidden");
  if (formCard && typeof formCard.scrollIntoView === 'function') {
    formCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function closeAdminModal() {
  const formCard = document.getElementById("admin-form-card");
  formCard.classList.add("hidden");
  currentAdminId = null;
}

function setAdminError(message) {
  const err = document.getElementById("admin-modal-error");
  err.textContent = message || "Please fix the highlighted fields.";
  err.hidden = false;
}

function renderAdminRow(admin, index) {
  const encoded = encodeURIComponent(JSON.stringify(admin));
  return '<tr>' +
    '<td>' + (index + 1) + '</td>' +
    '<td class="col-email" title="' + escapeHtml(admin.email) + '">' + escapeHtml(admin.email) + '</td>' +
    '<td>' + escapeHtml(admin.role) + '</td>' +
    '<td>' + (admin.isActive ? 'Yes' : 'No') + '</td>' +
    '<td>' + escapeHtml(admin.createdAt ? new Date(admin.createdAt).toLocaleDateString() : '-') + '</td>' +
    '<td class="col-action">' +
      '<button class="btn btn-outline btn-sm" type="button" onclick="openAdminModalFromButton(this)" data-admin="' + encoded + '">Edit</button>' +
      (admin.id === currentAdminUserId ? '<span class="micro-copy">Current account</span>' : '<button class="btn btn-sm btn-secondary" type="button" onclick="deleteAdmin(\'' + escapeHtml(admin.id) + '\')">Delete</button>') +
    '</td>' +
  '</tr>';
}

function openAdminModalFromButton(button) {
  try {
    const payload = button.dataset.admin ? JSON.parse(decodeURIComponent(button.dataset.admin)) : null;
    if (payload) {
      openAdminModal(payload);
    }
  } catch (error) {
    console.error("Failed to parse admin payload", error);
  }
}

async function loadAdmins() {
  if (!(await enforceAdminSession())) return;

  try {
    const response = await ReadWiseAPI.getAdminUsers("admin");
    const users = Array.isArray(response.users) ? response.users : [];
    const tbody = document.getElementById("admins-table");
    if (!users.length) {
      tbody.innerHTML = '<tr><td colspan="6">No admin users found.</td></tr>';
      return;
    }
    tbody.innerHTML = users.map(renderAdminRow).join("");
  } catch (error) {
    console.error(error);
    const tbody = document.getElementById("admins-table");
    tbody.innerHTML = '<tr><td colspan="6">Unable to load admin users.</td></tr>';
  }
}

async function saveAdmin() {
  const email = document.getElementById("admin-email").value.trim();
  const password = document.getElementById("admin-password").value;
  const role = document.getElementById("admin-role").value;
  const isActive = document.getElementById("admin-active").checked;

  if (!email) {
    setAdminError("Admin email is required.");
    return;
  }

  if (!currentAdminId && !password) {
    setAdminError("Password is required for new admins.");
    return;
  }

  const payload = { email, role, isActive };
  if (password) {
    payload.password = password;
  }

  try {
    if (currentAdminId) {
      await ReadWiseAPI.updateAdminUser(currentAdminId, payload);
    } else {
      await ReadWiseAPI.createAdminUser(payload);
    }
    closeAdminModal();
    await loadAdmins();
  } catch (error) {
    setAdminError(error.message || "Unable to save admin user.");
  }
}

async function deleteAdmin(adminId) {
  const confirmed = window.confirm("Delete this admin user? This action cannot be undone.");
  if (!confirmed) return;

  try {
    await ReadWiseAPI.deleteAdminUser(adminId);
    await loadAdmins();
  } catch (error) {
    window.alert(error.message || "Unable to delete admin user.");
  }
}

function initAdminAdminsPage() {
  document.getElementById("admin-save-btn").addEventListener("click", saveAdmin);
  loadCurrentAdminUser().then(loadAdmins);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initAdminAdminsPage);
} else {
  initAdminAdminsPage();
}
