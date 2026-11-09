window.__errs = window.__errs || [];
window.addEventListener("error", function (e) { window.__errs.push(String(e.message) + " @ " + String(e.filename).split("/").pop() + ":" + e.lineno); });
window.addEventListener("unhandledrejection", function (e) { window.__errs.push("rej: " + String(e.reason && e.reason.stack || e.reason).slice(0, 400)); });
(function () {
  var orig = console.error;
  console.error = function () {
    (window.__errs = window.__errs || []).push("console.error: " + Array.from(arguments).map(function (a) { return String(a && a.stack ? a.stack : a); }).join(" ").slice(0, 500));
    orig.apply(console, arguments);
  };
})();
