(function () {
  "use strict";

  var LEAVE_MS = 320;

  function enterApp() {
    var shell = document.getElementById("welcome-shell");
    var cta = document.getElementById("welcome-cta");

    if (typeof window.onWelcomeComplete === "function") {
      var proceed = window.onWelcomeComplete({ next: "profile" });
      if (proceed === false) return;
    }

    if (cta) cta.disabled = true;

    function goProfile() {
      if (typeof window.openProfileAfterWelcome === "function") {
        window.openProfileAfterWelcome();
      }
    }

    if (shell && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      shell.classList.add("welcome-leaving");
      window.setTimeout(goProfile, LEAVE_MS);
    } else {
      goProfile();
    }
  }

  var cta = document.getElementById("welcome-cta");
  if (cta) {
    cta.addEventListener("click", enterApp);
  }
})();
