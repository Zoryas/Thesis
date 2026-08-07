(function(global) {
  var pathname = String((global.location && global.location.pathname) || "/");
  var segments = pathname.split("/").filter(Boolean);
  var firstSegment = segments.length ? segments[0] : "";
  var isFileSegment = firstSegment.indexOf(".") !== -1;
  var computedBasePath = "";
  if (firstSegment && !isFileSegment && firstSegment.toLowerCase() !== "pages") {
    computedBasePath = "/" + firstSegment;
  }
  if (typeof global.READWISE_BASE_PATH === "undefined") {
    global.READWISE_BASE_PATH = computedBasePath;
  }

  var existing = String(global.READWISE_API_BASE_URL || "").trim();
  if (existing) return;

  var override = "";
  try {
    override = String(global.localStorage.getItem("readwise_api_base_override") || "").trim();
  } catch (error) {
    override = "";
  }
  if (override) {
    global.READWISE_API_BASE_URL = override;
    return;
  }

  var hostname = (global.location && global.location.hostname ? global.location.hostname : "").toLowerCase();
  var isLocalHost = hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1" || hostname.endsWith(".local");
  if (isLocalHost) {
    global.READWISE_API_BASE_URL = "http://localhost:5000";
  } else if (global.location && global.location.origin) {
    global.READWISE_API_BASE_URL = global.location.origin;
  } else {
    global.READWISE_API_BASE_URL = "https://readwise-api-production.up.railway.app";
  }
})(window);


