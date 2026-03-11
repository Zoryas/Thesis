let role = "student";

const studentBtn = document.getElementById("studentBtn");
const teacherBtn = document.getElementById("teacherBtn");
const loginBtn   = document.getElementById("loginBtn");

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
  const email    = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  const students = [
    { email:"juan.delacruz@pnhs.edu", password:"password123", id:"s1" },
    { email:"maria.santos@pnhs.edu",  password:"password123", id:"s2" },
    { email:"carlo.reyes@pnhs.edu",   password:"password123", id:"s3" },
    { email:"student@example.com",    password:"1234",        id:"s1" }
  ];
  const teacher = { email:"ms.villanueva@pnhs.edu", password:"teacher123" };
  const demoT   = { email:"teacher@example.com",    password:"abcd" };

  if (role === "student") {
    const found = students.find(s => s.email === email && s.password === password);
    if (found) {
      sessionStorage.setItem("role","student");
      sessionStorage.setItem("studentId", found.id);
      window.location.href = "pages/student-dashboard.html";
    } else { showError(); }
  } else {
    if ((email===teacher.email && password===teacher.password) ||
        (email===demoT.email   && password===demoT.password)) {
      sessionStorage.setItem("role","teacher");
      window.location.href = "pages/teacher-dashboard.html";
    } else { showError(); }
  }
});

function showError() {
  let e = document.getElementById("loginError");
  if (!e) {
    e = document.createElement("p");
    e.id = "loginError";
    e.style.cssText = "color:#c0392b;margin-top:10px;font-size:13px;text-align:center;font-weight:600;";
    document.querySelector(".card").appendChild(e);
  }
  e.textContent = "❌ Invalid credentials. Try again.";
}
