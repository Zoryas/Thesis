let role = "student";

const studentBtn = document.getElementById("studentBtn");
const teacherBtn = document.getElementById("teacherBtn");
const loginBtn = document.getElementById("loginBtn");

studentBtn.addEventListener("click", () => {
  role = "student";
  studentBtn.classList.add("active");
  teacherBtn.classList.remove("active");
});

teacherBtn.addEventListener("click", () => {
  role = "teacher";
  teacherBtn.classList.add("active");
  studentBtn.classList.remove("active");
});

loginBtn.addEventListener("click", async () => {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  if (!email || !password) {
    showError("Please enter both email and password.");
    return;
  }

  loginBtn.disabled = true;
  loginBtn.style.opacity = "0.7";
  loginBtn.textContent = "Signing in...";

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
      window.location.href = "pages/student-dashboard.html";
    } else {
      window.location.href = "pages/teacher-dashboard.html";
    }
  } catch (error) {
    showError(error.message || "Invalid credentials. Try again.");
  } finally {
    loginBtn.disabled = false;
    loginBtn.style.opacity = "1";
    loginBtn.textContent = "Login";
  }
});

function showError(message) {
  let error = document.getElementById("loginError");
  if (!error) {
    error = document.createElement("p");
    error.id = "loginError";
    error.className = "login-error";
    document.querySelector(".card").appendChild(error);
  }
  error.textContent = message || "Invalid credentials. Try again.";
}
