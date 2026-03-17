let role = "student";

const studentBtn = document.getElementById("studentBtn");
const teacherBtn = document.getElementById("teacherBtn");
const loginBtn = document.getElementById("loginBtn");
const loginError = document.getElementById("loginError");
const passwordInput = document.getElementById("password");
const togglePasswordBtn = document.getElementById("togglePasswordBtn");

function syncRoleButtons() {
  const isStudent = role === "student";
  studentBtn.classList.toggle("active", isStudent);
  teacherBtn.classList.toggle("active", !isStudent);
  studentBtn.setAttribute("aria-selected", isStudent ? "true" : "false");
  teacherBtn.setAttribute("aria-selected", isStudent ? "false" : "true");
}

studentBtn.addEventListener("click", () => {
  role = "student";
  syncRoleButtons();
});

teacherBtn.addEventListener("click", () => {
  role = "teacher";
  syncRoleButtons();
});

togglePasswordBtn.addEventListener("click", () => {
  const reveal = passwordInput.type === "password";
  passwordInput.type = reveal ? "text" : "password";
  togglePasswordBtn.textContent = reveal ? "Hide" : "Show";
  togglePasswordBtn.setAttribute("aria-label", reveal ? "Hide password" : "Show password");
});

loginBtn.addEventListener("click", async () => {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  if (!email || !password) {
    showError("Please enter both email and password.");
    return;
  }

  loginBtn.disabled = true;
  loginBtn.classList.add("is-loading");
  loginBtn.textContent = "Signing in...";
  loginError.hidden = true;

  try {
    const result = await ReadWiseAPI.login(email, password, role);
    const user = result && result.user ? result.user : null;
    if (!user) throw new Error("Invalid login response.");

    sessionStorage.setItem("role", user.role);
    if (user.student && user.student.id) {
      sessionStorage.setItem("studentId", user.student.id);
    } else {
      sessionStorage.removeItem("studentId");
    }

    if (user.role === "student") {
      const needsPreAssessment = !(user.student && user.student.preAssessmentCompleted);
      window.location.href = needsPreAssessment
        ? "pages/student-pre-assessment.html"
        : "pages/student-dashboard.html";
    } else {
      window.location.href = "pages/teacher-dashboard.html";
    }
  } catch (error) {
    showError(error.message || "Invalid credentials. Try again.");
  } finally {
    loginBtn.disabled = false;
    loginBtn.classList.remove("is-loading");
    loginBtn.textContent = "Sign In";
  }
});

function showError(message) {
  loginError.textContent = message || "Invalid credentials. Try again.";
  loginError.hidden = false;
}

document.getElementById("email").addEventListener("input", () => {
  loginError.hidden = true;
});

passwordInput.addEventListener("input", () => {
  loginError.hidden = true;
});

syncRoleButtons();
