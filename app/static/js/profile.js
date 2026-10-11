(function () {
  "use strict";

  var prefilled = false;

  function els() {
    return {
      form: document.getElementById("profile-form"),
      name: document.getElementById("profile-name"),
      age: document.getElementById("profile-age"),
      nameError: document.getElementById("profile-name-error"),
      ageError: document.getElementById("profile-age-error"),
      formError: document.getElementById("profile-form-error"),
      submit: document.getElementById("profile-submit"),
    };
  }

  function clearErrors(ui) {
    ui.nameError.hidden = true;
    ui.ageError.hidden = true;
    ui.formError.hidden = true;
    ui.nameError.textContent = "";
    ui.ageError.textContent = "";
    ui.formError.textContent = "";
    ui.name.classList.remove("field-invalid");
    ui.age.classList.remove("field-invalid");
  }

  function validateClient(ui) {
    clearErrors(ui);
    var name = (ui.name.value || "").trim();
    var ageRaw = (ui.age.value || "").trim();
    var valid = true;

    if (!name) {
      ui.nameError.textContent = "Ismingizni kiriting";
      ui.nameError.hidden = false;
      ui.name.classList.add("field-invalid");
      valid = false;
    } else if (name.length < 2) {
      ui.nameError.textContent = "Ism kamida 2 ta harfdan iborat bo‘lsin";
      ui.nameError.hidden = false;
      ui.name.classList.add("field-invalid");
      valid = false;
    }

    if (!ageRaw) {
      ui.ageError.textContent = "Yoshingizni kiriting";
      ui.ageError.hidden = false;
      ui.age.classList.add("field-invalid");
      valid = false;
    } else {
      var age = parseInt(ageRaw, 10);
      if (Number.isNaN(age) || age < 10 || age > 100) {
        ui.ageError.textContent = "Yoshingizni to‘g‘ri kiriting";
        ui.ageError.hidden = false;
        ui.age.classList.add("field-invalid");
        valid = false;
      }
    }

    return valid;
  }

  async function submitProfile(ui) {
    if (!validateClient(ui)) return;

    var name = ui.name.value.trim();
    var age = parseInt(ui.age.value.trim(), 10);

    ui.submit.disabled = true;
    ui.submit.classList.add("is-loading");
    clearErrors(ui);

    try {
      var res = await fetch("/api/profile/onboarding", {
        method: "POST",
        headers: window.appAuthHeaders(true),
        body: JSON.stringify({ display_name: name, age: age }),
      });

      var data = null;
      var text = await res.text();
      if (text) {
        try {
          data = JSON.parse(text);
        } catch (_) {
          data = null;
        }
      }

      if (!res.ok) {
        var detail = (data && data.detail) || "";
        if (typeof detail === "string" && detail.toLowerCase().includes("display_name")) {
          ui.nameError.textContent = "Ism kamida 2 ta harfdan iborat bo‘lsin";
          ui.nameError.hidden = false;
          ui.name.classList.add("field-invalid");
        } else if (typeof detail === "string" && detail.toLowerCase().includes("age")) {
          ui.ageError.textContent = "Yoshingizni to‘g‘ri kiriting";
          ui.ageError.hidden = false;
          ui.age.classList.add("field-invalid");
        } else {
          ui.formError.textContent = "Xatolik yuz berdi. Qayta urinib ko‘ring.";
          ui.formError.hidden = false;
        }
        return;
      }

      if (typeof window.openTasbehAfterProfile === "function") {
        window.openTasbehAfterProfile();
      }
    } catch (_) {
      ui.formError.textContent = "Xatolik yuz berdi. Qayta urinib ko‘ring.";
      ui.formError.hidden = false;
    } finally {
      ui.submit.disabled = false;
      ui.submit.classList.remove("is-loading");
    }
  }

  window.initProfileOnboarding = function (me) {
    var ui = els();
    if (!ui.form) return;

    if (!prefilled) {
      clearErrors(ui);
      var suggested = "";
      if (me && me.display_name) {
        suggested = me.display_name;
      } else if (me && me.user && me.user.first_name) {
        suggested = me.user.first_name;
      } else {
        var tg = window.Telegram && window.Telegram.WebApp;
        if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.first_name) {
          suggested = tg.initDataUnsafe.user.first_name;
        }
      }
      if (suggested && !ui.name.value) {
        ui.name.value = suggested;
      }
      if (me && me.age && !ui.age.value) {
        ui.age.value = String(me.age);
      }
      prefilled = true;
    }
  };

  document.addEventListener("DOMContentLoaded", function () {
    var ui = els();
    if (!ui.form) return;

    ui.form.addEventListener("submit", function (e) {
      e.preventDefault();
      submitProfile(ui);
    });
  });
})();
