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

function renderSummary(data) {
  document.getElementById("student-count").textContent = data.studentCount || 0;
  document.getElementById("teacher-count").textContent = data.teacherCount || 0;
  document.getElementById("passage-count").textContent = data.passageCount || 0;
}

function renderActivity(items) {
  const container = document.getElementById("admin-activity");
  if (!items || !items.length) {
    container.innerHTML = "<div class='surface-note'>No recent admin actions yet.</div>";
    return;
  }
  container.innerHTML = items.map(function(item) {
    return (
      '<div class="admin-activity-item">' +
        '<div><strong>' + item.action + '</strong></div>' +
        '<div class="micro-copy">' + item.details + '</div>' +
        '<div class="micro-copy">' + item.createdAt + '</div>' +
      '</div>'
    );
  }).join("");
}

async function loadAdminDashboard() {
  if (!(await enforceAdminSession())) return;

  try {
    const summary = await ReadWiseAPI.request("/api/admin/summary");
    renderSummary(summary);
    renderActivity(summary.recentActions || []);
  } catch (error) {
    console.error("Failed to load admin dashboard:", error);
    document.getElementById("admin-activity").innerHTML = "<div class='surface-note surface-note-error'>Unable to load recent activity.</div>";
  }
}

loadAdminDashboard();
