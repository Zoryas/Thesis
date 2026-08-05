(function(global) {
  // Default to same host as the page (handles localhost:80, localhost:8080, 127.0.0.1, etc.).
  var defaultHost = (global.location && global.location.hostname) ? global.location.hostname : "localhost";
  var RAW_BASE = global.READWISE_API_BASE_URL || ("http://" + defaultHost + ":5000");
  var BASE_URL = String(RAW_BASE).replace(/\/+$/, "");
  var USER_CACHE_KEY = "readwise_user_v1";
  var USER_TOKEN_KEY = "readwise_auth_token_v1";
  var TOTAL_WEEKS = 8;
  var MAX_WEEKLY_PASSAGES_PER_CLASS = 5;

  function normalizeWeek(value) {
    var parsed = Number(value);
    if (!Number.isInteger(parsed) || parsed < 1) return 1;
    if (parsed > TOTAL_WEEKS) return TOTAL_WEEKS;
    return parsed;
  }

  async function getActiveWeek() {
    var data = await request("/api/program/week");
    return normalizeWeek(data && data.activeWeek);
  }

  async function setActiveWeek(week) {
    var normalized = normalizeWeek(week);
    var data = await request("/api/program/week/settings", {
      method: "PUT",
      body: { manualOverrideWeek: normalized }
    });
    return normalizeWeek(data && data.activeWeek);
  }

  function buildUrl(path) {
    if (/^https?:\/\//i.test(path)) return path;
    return BASE_URL + path;
  }

  function emitUserCacheChange(user) {
    if (typeof global.CustomEvent !== "function" || typeof global.dispatchEvent !== "function") return;
    global.dispatchEvent(new CustomEvent("readwise:usercachechange", {
      detail: { user: user || null }
    }));
  }

  function getCachedUser() {
    try {
      var raw = global.localStorage.getItem(USER_CACHE_KEY);
      if (!raw) return null;
      var parsed = JSON.parse(raw);
      return parsed && typeof parsed === "object" ? parsed : null;
    } catch (error) {
      return null;
    }
  }

  function getCachedToken() {
    try {
      return global.localStorage.getItem(USER_TOKEN_KEY) || null;
    } catch (error) {
      return null;
    }
  }

  function cacheUser(user, token) {
    try {
      if (user && typeof user === "object") {
        global.localStorage.setItem(USER_CACHE_KEY, JSON.stringify(user));
      } else {
        global.localStorage.removeItem(USER_CACHE_KEY);
      }
      if (token) {
        global.localStorage.setItem(USER_TOKEN_KEY, token);
      }
    } catch (error) {
      // ignore storage errors
    }
    emitUserCacheChange(user || null);
    return user || null;
  }

  function clearCachedUser() {
    try {
      global.localStorage.removeItem(USER_CACHE_KEY);
      global.localStorage.removeItem(USER_TOKEN_KEY);
    } catch (error) {
      // ignore storage errors
    }
    emitUserCacheChange(null);
  }

  async function request(path, options) {
    var settings = options || {};
    var headers = Object.assign({}, settings.headers || {});
    var body = settings.body;

    var isFormData = typeof FormData !== "undefined" && body instanceof FormData;

    if (body !== undefined && body !== null && typeof body !== "string" && !isFormData) {
      headers["Content-Type"] = headers["Content-Type"] || "application/json";
      body = JSON.stringify(body);
    }

    var token = getCachedToken();
    if (token) {
      headers["Authorization"] = headers["Authorization"] || "Bearer " + token;
      headers["X-Auth-Token"] = headers["X-Auth-Token"] || token;
    }

    var response = await fetch(buildUrl(path), {
      method: settings.method || "GET",
      headers: headers,
      body: body,
      credentials: "include"
    });

    var payload = null;
    try {
      payload = await response.json();
    } catch (error) {
      payload = null;
    }

    if (!response.ok) {
      if (response.status === 401) {
        clearCachedUser();
      }
      var errorMessage = (payload && payload.error) || ("Request failed (" + response.status + ")");
      var error = new Error(errorMessage);
      error.status = response.status;
      error.isAuthError = response.status === 401;
      throw error;
    }

    if (!payload || payload.ok === false) {
      throw new Error((payload && payload.error) || "Unexpected API response.");
    }

    return payload.data;
  }

  async function predict(text) {
    var response = await fetch(buildUrl("/predict"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text }),
      credentials: "include"
    });
    var payload = await response.json().catch(function() { return {}; });
    if (!response.ok || payload.error) {
      throw new Error(payload.error || ("Prediction failed (" + response.status + ")"));
    }
    return payload;
  }

  global.ReadWiseAPI = {
    baseUrl: BASE_URL,
    getActiveWeek: getActiveWeek,
    setActiveWeek: setActiveWeek,
    getCachedUser: getCachedUser,
    request: request,
    predict: predict,
    login: function(email, password, role) {
      return request("/api/auth/login", {
        method: "POST",
        body: { email: email, password: password, role: role }
      }).then(function(data) {
        if (data && data.user) cacheUser(data.user, data.token);
        return data;
      });
    },
    logout: function() {
      return request("/api/auth/logout", { method: "POST" }).then(function(data) {
        clearCachedUser();
        return data;
      }, function(error) {
        clearCachedUser();
        throw error;
      });
    },
    me: function(options) {
      var settings = options || {};
      var cachedUser = settings.forceRefresh ? null : getCachedUser();
      if (cachedUser) {
        request("/api/auth/me").then(function(data) {
          if (data && data.user) cacheUser(data.user, getCachedToken());
        }).catch(function() {
          // keep cached user as temporary fallback if refresh fails
        });
        return Promise.resolve({ user: cachedUser, cached: true });
      }
      return request("/api/auth/me").then(function(data) {
        if (data && data.user) cacheUser(data.user, getCachedToken());
        return data;
      });
    },
    getPassages: function() {
      return request("/api/passages");
    },
    getPassage: function(id) {
      return request("/api/passages/" + encodeURIComponent(id));
    },
    createPassage: function(payload) {
      return request("/api/passages", { method: "POST", body: payload });
    },
    updatePassage: function(id, payload) {
      return request("/api/passages/" + encodeURIComponent(id), { method: "PUT", body: payload });
    },
    deletePassage: function(id) {
      return request("/api/passages/" + encodeURIComponent(id), { method: "DELETE" });
    },
    getAssignments: function(week) {
      var target = normalizeWeek(week);
      return request("/api/assignments?week=" + target);
    },
    assignPassage: function(week, classLevel, passageId) {
      return request("/api/assignments", {
        method: "POST",
        body: { week: normalizeWeek(week), classLevel: classLevel, passageId: passageId }
      });
    },
    removeAssignment: function(week, classLevel, passageId) {
      return request("/api/assignments", {
        method: "DELETE",
        body: { week: normalizeWeek(week), classLevel: classLevel, passageId: passageId }
      });
    },
    getStudentWeeklyPassages: function(week) {
      var target = normalizeWeek(week);
      return request("/api/student/weekly-passages?week=" + target);
    },
    getStudentCompletions: function(week) {
      var target = normalizeWeek(week);
      return request("/api/student/completions?week=" + target);
    },
    submitStudentAttempt: function(payload) {
      return request("/api/student/attempts", { method: "POST", body: payload });
    },
    saveReadingTime: function(payload) {
      return request("/api/student/reading-time", { method: "POST", body: payload });
    },
    getReadingProgress: function(week, passageId) {
      var target = normalizeWeek(week);
      return request(
        "/api/student/reading-progress?week=" + target + "&passageId=" + encodeURIComponent(passageId)
      );
    },
    saveReadingProgress: function(payload) {
      return request("/api/student/reading-progress", { method: "POST", body: payload });
    },
    lockReading: function(payload) {
      return request("/api/student/reading-lock", { method: "POST", body: payload });
    },
    submitStudentPreAssessment: function(payload) {
      return request("/api/student/pre-assessment", { method: "POST", body: payload }).then(function(data) {
        if (data && data.user) cacheUser(data.user);
        return data;
      });
    },
    getStudentProgress: function() {
      return request("/api/student/progress");
    },
    getTeacherDashboard: function() {
      return request("/api/teacher/dashboard");
    },
    getTeacherStudents: function() {
      return request("/api/teacher/students");
    },
    getTeacherReportSummary: function(activeWeek) {
      if (activeWeek === undefined || activeWeek === null || activeWeek === "") {
        return request("/api/teacher/reports/summary");
      }
      var target = normalizeWeek(activeWeek);
      return request("/api/teacher/reports/summary?activeWeek=" + target);
    },
    getProgramWeek: function() {
      return request("/api/program/week");
    },
    getProgramWeekSettings: function() {
      return request("/api/program/week/settings");
    },
    updateProgramWeekSettings: function(payload) {
      return request("/api/program/week/settings", { method: "PUT", body: payload || {} });
    },
    getTeacherStudentDetail: function(studentId) {
      return request("/api/teacher/students/" + encodeURIComponent(studentId));
    },
    getTeacherStudentPendingShortAnswers: function(studentId) {
      return request("/api/teacher/students/" + encodeURIComponent(studentId) + "/pending-short-answers");
    },
    saveTeacherScore: function(payload) {
      return request("/api/teacher/score", { method: "POST", body: payload || {} });
    },
    importPassagesCsv: function(file) {
      var form = new FormData();
      form.append("file", file);
      return request("/api/passages/import-csv", { method: "POST", body: form });
    },
    applyTeacherRecommendation: function(studentId) {
      return request("/api/teacher/students/" + encodeURIComponent(studentId) + "/apply-recommendation", {
        method: "POST"
      });
    },
    overrideStudentLevel: function(studentId, level, reason) {
      return request("/api/teacher/students/" + encodeURIComponent(studentId) + "/override-level", {
        method: "POST",
        body: { level: level, reason: reason }
      });
    },
    updateStudentAvatar: function(payload) {
      return request("/api/student/profile/avatar", { method: "PUT", body: payload }).then(function(data) {
        if (data && data.user) cacheUser(data.user);
        return data;
      });
    }
  };

  function normalizeClassLevel(value) {
    var raw = String(value || "").trim().toUpperCase();
    if (raw === "HARD" || raw === "DIFFICULT") return "HARD";
    if (raw === "MODERATE" || raw === "MEDIUM") return "MODERATE";
    return "EASY";
  }

  function mapPassageLabelToClassLevel(label) {
    return normalizeClassLevel(label);
  }

  function getClassDisplayName(level, format) {
    var normalized = normalizeClassLevel(level);
    var display = normalized === "HARD" ? "DIFFICULT" : normalized;
    if (format === "upper") return display;
    if (format === "lower") return display.toLowerCase();
    return display.charAt(0) + display.slice(1).toLowerCase();
  }

  function formatRecommendationDisplay(value) {
    var text = String(value || "").trim();
    if (!text) return "";
    return text
      .replace(/\bUP\b/g, "Up")
      .replace(/\bDOWN\b/g, "Down")
      .replace(/\bMEDIUM\b/gi, getClassDisplayName("MODERATE"))
      .replace(/\bMODERATE\b/gi, getClassDisplayName("MODERATE"))
      .replace(/\bHARD\b/gi, getClassDisplayName("HARD"))
      .replace(/\bDIFFICULT\b/gi, getClassDisplayName("HARD"))
      .replace(/\bEASY\b/gi, getClassDisplayName("EASY"));
  }

  function badgeClass(l) {
    var norm = normalizeClassLevel(l);
    return norm === "EASY" ? "badge-easy" : norm === "MODERATE" ? "badge-moderate" : "badge-hard";
  }

  function levelColor(l) {
    var norm = normalizeClassLevel(l);
    if (norm === "EASY") return "#34c759";
    if (norm === "MODERATE") return "#ff9f0a";
    return "#ff453a";
  }

  function levelBg(l) {
    var norm = normalizeClassLevel(l);
    if (norm === "EASY") return "rgba(52, 199, 89, 0.14)";
    if (norm === "MODERATE") return "rgba(255, 159, 10, 0.14)";
    return "rgba(255, 69, 58, 0.14)";
  }

  if (typeof global.normalizeClassLevel !== "function") global.normalizeClassLevel = normalizeClassLevel;
  if (typeof global.mapPassageLabelToClassLevel !== "function") global.mapPassageLabelToClassLevel = mapPassageLabelToClassLevel;
  if (typeof global.getClassDisplayName !== "function") global.getClassDisplayName = getClassDisplayName;
  if (typeof global.TOTAL_PROGRAM_WEEKS === "undefined") global.TOTAL_PROGRAM_WEEKS = TOTAL_WEEKS;
  if (typeof global.MAX_WEEKLY_PASSAGES_PER_CLASS === "undefined") global.MAX_WEEKLY_PASSAGES_PER_CLASS = MAX_WEEKLY_PASSAGES_PER_CLASS;
  if (typeof global.formatRecommendationDisplay !== "function") global.formatRecommendationDisplay = formatRecommendationDisplay;
  if (typeof global.badgeClass !== "function") global.badgeClass = badgeClass;
  if (typeof global.levelColor !== "function") global.levelColor = levelColor;
  if (typeof global.levelBg !== "function") global.levelBg = levelBg;
  function showToast(msg, color) {
    try {
      var t = global.document && global.document.getElementById && global.document.getElementById("toast");
      if (!t) return;
      t.textContent = String(msg || "");
      t.style.background = color || "#2c3e6b";
      t.style.display = "block";
      setTimeout(function() { try { t.style.display = "none"; } catch (e) {} }, 2800);
    } catch (e) {
      // ignore
    }
  }
  if (typeof global.showToast !== "function") global.showToast = showToast;

  function initSidebarAndThemeControls() {
    if (!global.document || !global.document.body) return;

    var sidebar = document.querySelector(".sidebar");
    var main = document.querySelector(".main");
    if (!sidebar || !main) return;

    var shellToggle = document.querySelector(".shell-toggle");
    if (!shellToggle) {
      shellToggle = document.createElement("button");
      shellToggle.type = "button";
      shellToggle.className = "shell-toggle";
      shellToggle.setAttribute("aria-label", "Toggle sidebar");
      shellToggle.innerHTML = '<span class="icon" data-icon="menu"></span>';
      document.body.appendChild(shellToggle);
    }

    var overlay = document.querySelector(".sidebar-overlay");
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.className = "sidebar-overlay";
      document.body.appendChild(overlay);
    }

    var themeToggle = document.querySelector(".theme-toggle");
    if (!themeToggle) {
      themeToggle = document.createElement("button");
      themeToggle.type = "button";
      themeToggle.className = "theme-toggle";
      themeToggle.setAttribute("aria-label", "Toggle dark mode");
      themeToggle.innerHTML = '<span class="icon" data-icon="moon"></span>';
      document.body.appendChild(themeToggle);
    }

    var userSidebarCollapsedKey = "readwise_sidebar_collapsed";
    var userThemeKey = "readwise_theme_preference";

    function isSidebarOpen() {
      return document.body.classList.contains("sidebar-open");
    }

    function isSidebarCollapsed() {
      return document.body.classList.contains("sidebar-collapsed");
    }

    function setSidebarOpen(value) {
      if (value) {
        document.body.classList.add("sidebar-open");
      } else {
        document.body.classList.remove("sidebar-open");
      }
    }

    function setSidebarCollapsed(value) {
      if (value) {
        document.body.classList.add("sidebar-collapsed");
      } else {
        document.body.classList.remove("sidebar-collapsed");
      }
      try {
        localStorage.setItem(userSidebarCollapsedKey, value ? "1" : "0");
      } catch (e) {
        // ignore storage failures
      }
    }

    function loadSidebarState() {
      var collapsed = false;
      try {
        collapsed = localStorage.getItem(userSidebarCollapsedKey) === "1";
      } catch (e) {
        collapsed = false;
      }
      if (window.matchMedia && window.matchMedia("(max-width: 900px)").matches) {
        document.body.classList.remove("sidebar-collapsed");
        document.body.classList.remove("sidebar-open");
      } else {
        if (collapsed) {
          document.body.classList.add("sidebar-collapsed");
        } else {
          document.body.classList.remove("sidebar-collapsed");
        }
      }
      syncSidebarBreakpoint();
    }

    function syncSidebarBreakpoint() {
      if (window.matchMedia && window.matchMedia("(max-width: 900px)").matches) {
        document.body.classList.remove("sidebar-collapsed");
      } else {
        document.body.classList.remove("sidebar-open");
      }
    }

    function getThemePreference() {
      try {
        var stored = localStorage.getItem(userThemeKey);
        if (stored === "dark" || stored === "light") return stored;
      } catch (e) {
        // ignore
      }
      if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        return "dark";
      }
      return "light";
    }

    function updateThemeDisplay(preference) {
      document.documentElement.setAttribute("data-theme-preference", preference);
      document.documentElement.style.colorScheme = preference;
      document.documentElement.style.backgroundColor = preference === "dark" ? "#070b11" : "#ffffff";
      var icon = themeToggle.querySelector(".icon");
      if (preference === "dark") {
        themeToggle.setAttribute("aria-label", "Switch to light mode");
        if (icon) icon.setAttribute("data-icon", "sun");
      } else {
        themeToggle.setAttribute("aria-label", "Switch to dark mode");
        if (icon) icon.setAttribute("data-icon", "moon");
      }
    }

    function setThemePreference(value) {
      var normalized = value === "dark" ? "dark" : "light";
      updateThemeDisplay(normalized);
      try {
        localStorage.setItem(userThemeKey, normalized);
      } catch (e) {
        // ignore
      }
    }

    shellToggle.addEventListener("click", function() {
      if (window.matchMedia && window.matchMedia("(max-width: 900px)").matches) {
        setSidebarOpen(!isSidebarOpen());
      } else {
        setSidebarCollapsed(!isSidebarCollapsed());
      }
    });

    overlay.addEventListener("click", function() {
      setSidebarOpen(false);
    });

    themeToggle.addEventListener("click", function() {
      var next = document.documentElement.getAttribute("data-theme-preference") === "dark" ? "light" : "dark";
      setThemePreference(next);
    });

    loadSidebarState();
    window.addEventListener("resize", syncSidebarBreakpoint);
    setThemePreference(getThemePreference());
  }

  if (typeof global.addEventListener === "function") {
    global.addEventListener("DOMContentLoaded", initSidebarAndThemeControls);
  } else if (typeof document !== "undefined") {
    initSidebarAndThemeControls();
  }
})(window);



