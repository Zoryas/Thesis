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

loginBtn.addEventListener("click", () => {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  const studentCreds = { email: "student@example.com", password: "1234" };
  const teacherCreds = { email: "teacher@example.com", password: "abcd" };

  if (role === "student" && email === studentCreds.email && password === studentCreds.password) {
    window.location.href = "studentDashboard.html"; // redirect
  } else if (role === "teacher" && email === teacherCreds.email && password === teacherCreds.password) {
    window.location.href = "teacherDashboard.html"; // redirect
  } else {
    alert("Invalid credentials");
  }
});
