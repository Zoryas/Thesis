(function(global) {
  // Default to same host as the page (handles localhost:80, localhost:8080, 127.0.0.1, etc.).
  var defaultHost = (global.location && global.location.hostname) ? global.location.hostname : "localhost";
  var RAW_BASE = global.READWISE_API_BASE_URL || ("http://" + defaultHost + ":5000");
  var BASE_URL = String(RAW_BASE).replace(/\/+$/, "");
  var ACTIVE_WEEK_KEY = "readwise_active_week_v1";
  var USER_CACHE_KEY = "readwise_user_v1";
  var TOKEN_KEY = "readwise_token";
  var TOTAL_WEEKS = 8;

  function normalizeWeek(value) {
    var parsed = Number(value);
    if (!Number.isInteger(parsed) || parsed < 1) return 1;
    if (parsed > TOTAL_WEEKS) return TOTAL_WEEKS;
    return parsed;
  }

  function getActiveWeek() {
    try {
      return normalizeWeek(localStorage.getItem(ACTIVE_WEEK_KEY) || 1);
    } catch (error) {
      return 1;
    }
  }

  function setActiveWeek(week) {
    var normalized = normalizeWeek(week);
    try {
      localStorage.setItem(ACTIVE_WEEK_KEY, String(normalized));
    } catch (error) {
      // ignore storage errors
    }
    return normalized;
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

  function cacheUser(user) {
    try {
      if (user && typeof user === "object") {
        global.localStorage.setItem(USER_CACHE_KEY, JSON.stringify(user));
      } else {
        global.localStorage.removeItem(USER_CACHE_KEY);
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
    } catch (error) {
      // ignore storage errors
    }
    emitUserCacheChange(null);
  }

  function getStoredToken() {
    try {
      var raw = global.localStorage.getItem(TOKEN_KEY);
      if (!raw) return null;
      var token = String(raw).trim();
      return token || null;
    } catch (error) {
      return null;
    }
  }

  function setStoredToken(token) {
    try {
      if (token && typeof token === "string") {
        global.localStorage.setItem(TOKEN_KEY, token);
      } else {
        global.localStorage.removeItem(TOKEN_KEY);
      }
    } catch (error) {
      // ignore storage errors
    }
  }

  function clearStoredToken() {
    try {
      global.localStorage.removeItem(TOKEN_KEY);
    } catch (error) {
      // ignore storage errors
    }
  }

  async function request(path, options) {
    var settings = options || {};
    var headers = Object.assign({}, settings.headers || {});
    var body = settings.body;
    var token = getStoredToken();
    if (token && !headers["X-Auth-Token"]) {
      headers["X-Auth-Token"] = token;
    }

    if (body !== undefined && body !== null && typeof body !== "string") {
      headers["Content-Type"] = headers["Content-Type"] || "application/json";
      body = JSON.stringify(body);
    }

    var response = await fetch(buildUrl(path), {
      method: settings.method || "GET",
      headers: headers,
      body: body,
      credentials: "omit"
    });

    var payload = null;
    try {
      payload = await response.json();
    } catch (error) {
      payload = null;
    }

    if (!response.ok) {
      if (response.status === 401) {
        clearStoredToken();
        clearCachedUser();
      }
      throw new Error((payload && payload.error) || ("Request failed (" + response.status + ")"));
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
      credentials: "omit"
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
        if (data && data.token) setStoredToken(data.token);
        if (data && data.user) cacheUser(data.user);
        return data;
      });
    },
    logout: function() {
      return request("/api/auth/logout", { method: "POST" }).then(function(data) {
        clearStoredToken();
        clearCachedUser();
        return data;
      }, function(error) {
        clearStoredToken();
        clearCachedUser();
        throw error;
      });
    },
    me: function() {
      return request("/api/auth/me").then(function(data) {
        if (data && data.user) cacheUser(data.user);
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
    getStudentProgress: function() {
      return request("/api/student/progress");
    },
    updateStudentAvatar: function(payload) {
      return request("/api/student/profile/avatar", { method: "PUT", body: payload }).then(function(data) {
        if (data && data.user) cacheUser(data.user);
        return data;
      });
    }
  };
})(window);
