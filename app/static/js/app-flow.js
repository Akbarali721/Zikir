(function () {
  "use strict";

  var WARM_THEME = "#F6F0E5";
  var TASBEH_THEME = "#f7f3ea";

  window.appAuthHeaders = function (json) {
    var headers = {};
    if (json) headers["Content-Type"] = "application/json";
    var tg = window.Telegram && window.Telegram.WebApp;
    if (tg && tg.initData) {
      headers["X-Telegram-Init-Data"] = tg.initData;
    } else if (window.APP_CONFIG && window.APP_CONFIG.debug) {
      headers["X-Dev-Mode"] = "1";
    }
    return headers;
  };

  function setThemeColor(color) {
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", color);
  }

  function showTasbeh() {
    var html = document.documentElement;
    html.classList.remove("welcome-pending", "profile-pending");
    setThemeColor(TASBEH_THEME);
    if (typeof window.startTasbehApp === "function") {
      window.startTasbehApp();
    }
  }

  function showWelcome() {
    var html = document.documentElement;
    html.classList.add("welcome-pending");
    html.classList.remove("profile-pending");
    setThemeColor(WARM_THEME);
  }

  window.openProfileAfterWelcome = function () {
    document.documentElement.classList.remove("welcome-pending");
    document.documentElement.classList.add("profile-pending");
    setThemeColor(WARM_THEME);
    var shell = document.getElementById("profile-shell");
    if (shell && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      shell.classList.add("profile-entering");
      window.setTimeout(function () {
        shell.classList.remove("profile-entering");
      }, 400);
    }
    if (typeof window.initProfileOnboarding === "function") {
      window.initProfileOnboarding(window.__pendingMeForProfile || null);
    }
  };

  window.openTasbehAfterProfile = function () {
    var shell = document.getElementById("profile-shell");
    if (shell && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      shell.classList.add("profile-leaving");
      window.setTimeout(showTasbeh, 280);
    } else {
      showTasbeh();
    }
  };

  async function bootstrapAppFlow() {
    var tg = window.Telegram && window.Telegram.WebApp;
    if (tg) {
      tg.ready();
    }

    window.__pendingMeForProfile = null;

    try {
      var res = await fetch("/api/me", { headers: window.appAuthHeaders(false) });
      if (!res.ok) {
        showWelcome();
        return;
      }
      var me = await res.json();

      if (me.onboarding_completed) {
        showTasbeh();
        return;
      }

      window.__pendingMeForProfile = me;
      showWelcome();
    } catch (_) {
      showWelcome();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootstrapAppFlow);
  } else {
    bootstrapAppFlow();
  }
})();
