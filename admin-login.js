const adminLoginBtn = document.getElementById("adminLoginBtn");
const adminLoginError = document.getElementById("adminLoginError");
const adminEmailInput = document.getElementById("admin-email");
const adminPasswordInput = document.getElementById("admin-password");
const adminTogglePasswordBtn = document.getElementById("adminTogglePasswordBtn");

adminTogglePasswordBtn.addEventListener("click", () => {
  const reveal = adminPasswordInput.type === "password";
  adminPasswordInput.type = reveal ? "text" : "password";
  adminTogglePasswordBtn.textContent = reveal ? "Hide" : "Show";
  adminTogglePasswordBtn.setAttribute("aria-label", reveal ? "Hide password" : "Show password");
});

adminLoginBtn.addEventListener("click", async () => {
  const email = adminEmailInput.value.trim();
  const password = adminPasswordInput.value;

  if (!email || !password) {
    showError("Please enter both email and password.");
    return;
  }

  adminLoginBtn.disabled = true;
  adminLoginBtn.classList.add("is-loading");
  adminLoginBtn.textContent = "Signing in...";
  adminLoginError.hidden = true;

  try {
    const result = await ReadWiseAPI.login(email, password, "admin");
    const user = result && result.user ? result.user : null;
    if (!user) throw new Error("Invalid login response.");

    sessionStorage.setItem("role", user.role);
    sessionStorage.removeItem("studentId");

    window.location.href = "/admin-dashboard";
  } catch (error) {
    showError(error.message || "Invalid credentials. Try again.");
  } finally {
    adminLoginBtn.disabled = false;
    adminLoginBtn.classList.remove("is-loading");
    adminLoginBtn.textContent = "Sign In";
  }
});

function showError(message) {
  adminLoginError.textContent = message || "Invalid credentials. Try again.";
  adminLoginError.hidden = false;
}

adminEmailInput.addEventListener("input", () => {
  adminLoginError.hidden = true;
});

adminPasswordInput.addEventListener("input", () => {
  adminLoginError.hidden = true;
});
