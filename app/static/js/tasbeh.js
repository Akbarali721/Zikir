(function () {
  "use strict";

  const SYNC_DHikR_THRESHOLD = 15;
  const SYNC_INTERVAL_MS = 7000;
  const IDLE_TIMEOUT_MS = 45000;

  const els = {
    globalDhikr: document.getElementById("global-dhikr"),
    globalDhikrGoal: document.getElementById("global-dhikr-goal"),
    globalRemainingDhikr: document.getElementById("global-remaining-dhikr"),
    globalBar: document.getElementById("global-dhikr-bar"),
    sessionCount: document.getElementById("session-count"),
    personalDhikr: document.getElementById("personal-dhikr"),
    personalTime: document.getElementById("personal-time"),
    footerGlobalDhikr: document.getElementById("footer-global-dhikr"),
    footerGlobalTime: document.getElementById("footer-global-time"),
    globalRemainingTime: document.getElementById("global-remaining-time"),
    globalPercent: document.getElementById("global-dhikr-percent"),
    returnCard: document.getElementById("return-card"),
    returnGreeting: document.getElementById("return-greeting"),
    returnSubline: document.getElementById("return-subline"),
    returnGlobalGrowth: document.getElementById("return-global-growth"),
    todayDhikr: document.getElementById("today-dhikr"),
    todayTime: document.getElementById("today-time"),
    sessionActiveTime: document.getElementById("session-active-time"),
    personalSharePercent: document.getElementById("personal-share-percent"),
    idleSummary: document.getElementById("idle-summary"),
    idleSummaryDhikr: document.getElementById("idle-summary-dhikr"),
    idleSummaryTime: document.getElementById("idle-summary-time"),
    idleContinueBtn: document.getElementById("idle-continue-btn"),
    tasbehBtn: document.getElementById("tasbeh-btn"),
    tasbehSurface: document.getElementById("tasbeh-surface"),
    modeTap: document.getElementById("mode-tap"),
    modeSwipe: document.getElementById("mode-swipe"),
    statusMsg: document.getElementById("status-msg"),
    tasbehHint: document.getElementById("tasbeh-hint"),
  };

  let lastDisplayedGlobalDhikr = null;
  let lastGlobalDhikrTotal = 0;

  let sessionId = null;
  let mode = "tap";

  let pendingDhikr = 0;
  let pendingActiveSeconds = 0;

  let displaySessionDhikr = 0;
  let displaySessionActiveSeconds = 0;
  let displayPersonalDhikr = 0;
  let displayPersonalSeconds = 0;

  let todayBaseDhikr = 0;
  let todayBaseSeconds = 0;
  let initialSessionDhikr = 0;
  let initialSessionActiveSeconds = 0;
  let sessionCountsForToday = true;

  let visitSnapshotSending = false;

  let syncInFlight = false;
  let syncQueued = false;
  let lastSyncAt = Date.now();

  let isEngaged = false;
  let isIdlePaused = true;
  let requireInteractionAfterVisible = false;

  let idleTimer = null;
  let activeSecondTimer = null;
  let syncCheckTimer = null;

  let swipeTracking = false;
  let swipeStartY = 0;
  let swipeStartX = 0;

  function formatNumber(n) {
    return new Intl.NumberFormat("uz-UZ").format(n);
  }

  function formatActiveTimeUz(seconds) {
    if (seconds < 0) seconds = 0;
    if (seconds < 60) return `${seconds} soniya`;
    const minutes = Math.floor(seconds / 60);
    const sec = seconds % 60;
    if (minutes < 60) {
      return sec ? `${minutes} daqiqa ${sec} soniya` : `${minutes} daqiqa`;
    }
    const hours = Math.floor(minutes / 60);
    const min = minutes % 60;
    const parts = [];
    if (hours) parts.push(`${hours} soat`);
    if (min) parts.push(`${min} daqiqa`);
    return parts.join(" ") || "0 soniya";
  }

  function formatGoalRemainingUz(seconds) {
    if (seconds < 0) seconds = 0;
    if (seconds === 0) return "Maqsadgacha: 0";
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours >= 1 && minutes === 0) {
      return "Maqsadgacha: " + formatNumber(hours) + " soat";
    }
    if (hours >= 1) {
      return "Maqsadgacha: " + formatNumber(hours) + " soat " + minutes + " daqiqa";
    }
    if (minutes >= 1) {
      return "Maqsadgacha: " + minutes + " daqiqa";
    }
    return "Maqsadgacha: " + seconds + " soniya";
  }

  function authHeaders(json) {
    const headers = {};
    if (json) headers["Content-Type"] = "application/json";
    const tg = window.Telegram && window.Telegram.WebApp;
    if (tg && tg.initData) {
      headers["X-Telegram-Init-Data"] = tg.initData;
    } else if (window.APP_CONFIG && window.APP_CONFIG.debug) {
      headers["X-Dev-Mode"] = "1";
    }
    return headers;
  }

  function showError(msg) {
    els.statusMsg.hidden = false;
    els.statusMsg.textContent = msg;
  }

  function clearError() {
    els.statusMsg.hidden = true;
    els.statusMsg.textContent = "";
  }

  async function apiFetch(path, options) {
    const res = await fetch(path, {
      ...options,
      headers: { ...authHeaders(options && options.body), ...(options && options.headers) },
    });
    let data = null;
    const text = await res.text();
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (_) {
        data = { detail: text };
      }
    }
    if (!res.ok) {
      const detail = (data && data.detail) || res.statusText || "Xatolik";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return data;
  }

  function formatSharePercent(personal, globalTotal) {
    if (!globalTotal || globalTotal <= 0 || personal <= 0) return null;
    const pct = (personal / globalTotal) * 100;
    if (pct > 0 && pct < 0.01) return "<0.01%";
    return pct.toFixed(2) + "%";
  }

  function computeDisplayTodayDhikr() {
    if (!sessionCountsForToday) return todayBaseDhikr;
    return (
      todayBaseDhikr +
      (displaySessionDhikr - initialSessionDhikr) +
      pendingDhikr
    );
  }

  function computeDisplayTodaySeconds() {
    if (!sessionCountsForToday) return todayBaseSeconds;
    return (
      todayBaseSeconds +
      (displaySessionActiveSeconds - initialSessionActiveSeconds) +
      pendingActiveSeconds
    );
  }

  function updateReturnCard(me) {
    if (!els.returnCard || !me || !me.onboarding_completed) return;

    const displayToday = computeDisplayTodayDhikr();
    const name = me.display_name || (me.user && me.user.first_name) || null;
    const isReturning = me.retention && me.retention.is_returning;

    if (!isReturning && displayToday === 0 && !name) {
      els.returnCard.hidden = true;
      return;
    }

    els.returnCard.hidden = false;

    if (name) {
      els.returnGreeting.textContent = "Xush kelibsiz, " + name + ".";
    } else {
      els.returnGreeting.textContent = "Xush kelibsiz.";
    }

    if (displayToday > 0) {
      els.returnSubline.textContent =
        "Bugun siz allaqachon " +
        formatNumber(displayToday) +
        " ta istig‘for bilan hissa qo‘shdingiz.";
    } else {
      els.returnSubline.textContent =
        "Bugun Million Istig‘for uchun bir necha daqiqa ajratamizmi?";
    }

    const growth =
      me.retention && me.retention.global_growth_since_last_visit != null
        ? me.retention.global_growth_since_last_visit
        : null;

    if (growth != null && growth >= 50) {
      els.returnGlobalGrowth.hidden = false;
      els.returnGlobalGrowth.textContent =
        "Siz yo‘q paytingizda yana " +
        formatNumber(growth) +
        " ta istig‘for qo‘shildi.";
    } else if (growth != null && growth > 0) {
      els.returnGlobalGrowth.hidden = false;
      els.returnGlobalGrowth.textContent =
        "Jamoamiz siz yo‘q paytingizda ham davom etdi.";
    } else {
      els.returnGlobalGrowth.hidden = true;
      els.returnGlobalGrowth.textContent = "";
    }
  }

  function sendVisitSnapshot() {
    if (visitSnapshotSending) return;
    visitSnapshotSending = true;
    fetch("/api/visit/snapshot", {
      method: "POST",
      headers: authHeaders(false),
      keepalive: true,
    }).finally(function () {
      visitSnapshotSending = false;
    });
  }

  function showIdleSummary() {
    if (!els.idleSummary || displaySessionDhikr <= 0) return;
    els.idleSummaryDhikr.textContent =
      "Bu safar " + formatNumber(displaySessionDhikr) + " ta istig‘for aytdingiz.";
    els.idleSummaryTime.textContent =
      formatActiveTimeUz(displaySessionActiveSeconds) +
      " foydali vaqt ajratdingiz.";
    els.idleSummary.hidden = false;
  }

  function hideIdleSummary() {
    if (els.idleSummary) els.idleSummary.hidden = true;
  }

  function updatePersonalShareLine() {
    if (!els.personalSharePercent) return;
    const share = formatSharePercent(displayPersonalDhikr, lastGlobalDhikrTotal);
    if (share) {
      els.personalSharePercent.hidden = false;
      els.personalSharePercent.textContent =
        "Umumiy natijaning " + share + " sizning hissangiz";
    } else {
      els.personalSharePercent.hidden = true;
      els.personalSharePercent.textContent = "";
    }
  }

  function updateProgressUI(global) {
    if (!global) return;
    const formattedDhikr = formatNumber(global.dhikr);
    if (lastDisplayedGlobalDhikr !== null && global.dhikr > lastDisplayedGlobalDhikr) {
      els.globalDhikr.classList.remove("count-bump");
      void els.globalDhikr.offsetWidth;
      els.globalDhikr.classList.add("count-bump");
    }
    lastDisplayedGlobalDhikr = global.dhikr;
    lastGlobalDhikrTotal = global.dhikr;

    els.globalDhikr.textContent = formattedDhikr;
    els.globalDhikrGoal.textContent = formatNumber(global.dhikr_goal);
    els.globalRemainingDhikr.textContent = formatNumber(global.remaining_dhikr);
    els.footerGlobalDhikr.textContent = formatNumber(global.dhikr);
    els.footerGlobalTime.textContent = formatActiveTimeUz(global.active_seconds);
    if (els.globalRemainingTime) {
      els.globalRemainingTime.textContent = formatGoalRemainingUz(global.remaining_seconds);
    }
    const pct = Math.min(100, (global.dhikr / global.dhikr_goal) * 100);
    els.globalBar.style.width = `${pct}%`;
    if (els.globalPercent) {
      const displayPct =
        typeof global.dhikr_percent === "number"
          ? global.dhikr_percent
          : pct;
      els.globalPercent.textContent = displayPct.toFixed(1).replace(/\.0$/, "") + "%";
    }
    updatePersonalShareLine();
  }

  function refreshPersonalUI() {
    els.sessionCount.textContent = formatNumber(displaySessionDhikr);
    els.personalDhikr.textContent = formatNumber(displayPersonalDhikr);
    els.personalTime.textContent = formatActiveTimeUz(displayPersonalSeconds);
    if (els.sessionActiveTime) {
      els.sessionActiveTime.textContent = formatActiveTimeUz(displaySessionActiveSeconds);
    }
    if (els.todayDhikr) {
      els.todayDhikr.textContent = formatNumber(computeDisplayTodayDhikr());
    }
    if (els.todayTime) {
      els.todayTime.textContent = formatActiveTimeUz(computeDisplayTodaySeconds());
    }
    updatePersonalShareLine();
    if (window.__lastMePayload) updateReturnCard(window.__lastMePayload);
  }

  function canCountActiveTime() {
    return (
      !document.hidden &&
      isEngaged &&
      !isIdlePaused &&
      !requireInteractionAfterVisible &&
      sessionId !== null
    );
  }

  function resetIdleTimer() {
    if (idleTimer) clearTimeout(idleTimer);
    idleTimer = setTimeout(function () {
      isIdlePaused = true;
      isEngaged = false;
      showIdleSummary();
    }, IDLE_TIMEOUT_MS);
  }

  function onUserInteraction() {
    if (document.hidden) return;
    requireInteractionAfterVisible = false;
    isIdlePaused = false;
    isEngaged = true;
    hideIdleSummary();
    resetIdleTimer();
  }

  function registerDhikr() {
    if (!sessionId) return;
    onUserInteraction();
    pendingDhikr += 1;
    displaySessionDhikr += 1;
    displayPersonalDhikr += 1;
    refreshPersonalUI();
    pulseButton();
    if (navigator.vibrate) navigator.vibrate(20);
    maybeScheduleSync(true);
  }

  function pulseButton() {
    els.tasbehBtn.classList.add("pulse");
    setTimeout(function () {
      els.tasbehBtn.classList.remove("pulse");
    }, 120);
  }

  function startActiveSecondTimer() {
    if (activeSecondTimer) return;
    activeSecondTimer = setInterval(function () {
      if (canCountActiveTime()) {
        pendingActiveSeconds += 1;
        displayPersonalSeconds += 1;
        displaySessionActiveSeconds += 1;
        refreshPersonalUI();
      }
    }, 1000);
  }

  function startSyncCheckTimer() {
    if (syncCheckTimer) return;
    syncCheckTimer = setInterval(function () {
      maybeScheduleSync(false);
    }, 1000);
  }

  function maybeScheduleSync(fromAction) {
    const elapsed = Date.now() - lastSyncAt;
    if (
      pendingDhikr >= SYNC_DHikR_THRESHOLD ||
      elapsed >= SYNC_INTERVAL_MS ||
      (fromAction && pendingDhikr > 0 && elapsed >= 2000)
    ) {
      flushSync(false);
    }
  }

  async function flushSync(useKeepalive) {
    if (!sessionId) return;
    if (pendingDhikr === 0 && pendingActiveSeconds === 0) return;

    if (syncInFlight) {
      syncQueued = true;
      return;
    }

    syncInFlight = true;
    const sendDhikr = pendingDhikr;
    const sendSeconds = pendingActiveSeconds;
    pendingDhikr = 0;
    pendingActiveSeconds = 0;

    const body = JSON.stringify({
      session_id: sessionId,
      dhikr_delta: sendDhikr,
      active_seconds_delta: sendSeconds,
    });

    try {
      let data;
      if (useKeepalive) {
        const res = await fetch("/api/tasbeh/sync", {
          method: "POST",
          headers: authHeaders(true),
          body,
          keepalive: true,
        });
        if (!res.ok) throw new Error("Background sync failed");
        data = await res.json();
      } else {
        data = await apiFetch("/api/tasbeh/sync", { method: "POST", body });
      }

      lastSyncAt = Date.now();
      displaySessionDhikr = data.session_dhikr_count;
      displaySessionActiveSeconds = data.session_active_seconds;
      displayPersonalDhikr = data.personal_dhikr_count;
      displayPersonalSeconds = data.personal_active_seconds;
      initialSessionDhikr = data.session_dhikr_count;
      initialSessionActiveSeconds = data.session_active_seconds;
      if (sessionCountsForToday) {
        todayBaseDhikr += sendDhikr;
        todayBaseSeconds += sendSeconds;
      }
      refreshPersonalUI();
      clearError();

      const progress = await apiFetch("/api/progress");
      updateProgressUI(progress.global);
    } catch (err) {
      pendingDhikr += sendDhikr;
      pendingActiveSeconds += sendSeconds;
      showError(String(err.message || err));
    } finally {
      syncInFlight = false;
      if (syncQueued) {
        syncQueued = false;
        flushSync(false);
      }
    }
  }

  async function startSession(selectedMode) {
    const data = await apiFetch("/api/session/start", {
      method: "POST",
      body: JSON.stringify({ mode: selectedMode }),
    });
    sessionId = data.session_id;
    mode = data.mode;
    displaySessionDhikr = 0;
    displaySessionActiveSeconds = 0;
    initialSessionDhikr = 0;
    initialSessionActiveSeconds = 0;
    sessionCountsForToday = true;
    isIdlePaused = true;
    isEngaged = false;
    requireInteractionAfterVisible = false;
    hideIdleSummary();
  }

  async function ensureSession(selectedMode) {
    if (sessionId) {
      if (mode !== selectedMode) {
        await flushSync(false);
        await apiFetch("/api/session/stop", { method: "POST" });
        await startSession(selectedMode);
      }
      return;
    }
    await startSession(selectedMode);
  }

  function setModeUI(selectedMode) {
    mode = selectedMode;
    els.modeTap.classList.toggle("active", selectedMode === "tap");
    els.modeSwipe.classList.toggle("active", selectedMode === "swipe");
    els.modeTap.setAttribute("aria-selected", selectedMode === "tap" ? "true" : "false");
    els.modeSwipe.setAttribute("aria-selected", selectedMode === "swipe" ? "true" : "false");
    els.tasbehSurface.classList.toggle("swipe-mode", selectedMode === "swipe");
    if (els.tasbehHint) {
      els.tasbehHint.textContent =
        selectedMode === "swipe" ? "Pastdan tepaga suring" : "Bosish orqali zikr qiling";
    }
  }

  async function init() {
    const tg = window.Telegram && window.Telegram.WebApp;
    if (tg) {
      tg.expand();
    }

    try {
      const [me, progress] = await Promise.all([
        apiFetch("/api/me"),
        apiFetch("/api/progress"),
      ]);

      window.__lastMePayload = me;

      displayPersonalDhikr = me.personal_dhikr_count;
      displayPersonalSeconds = me.personal_active_seconds;
      todayBaseDhikr = me.today.dhikr;
      todayBaseSeconds = me.today.active_seconds;
      updateProgressUI(progress.global);

      if (me.session && me.session.is_active) {
        sessionId = me.session.id;
        mode = me.session.mode;
        displaySessionDhikr = me.session.dhikr_count;
        displaySessionActiveSeconds = me.session.active_seconds;
        initialSessionDhikr = me.session.dhikr_count;
        initialSessionActiveSeconds = me.session.active_seconds;
        sessionCountsForToday = me.session.counts_for_today !== false;
        setModeUI(mode);
      } else {
        await startSession("tap");
        setModeUI("tap");
      }

      updateReturnCard(me);
      refreshPersonalUI();
      clearError();
    } catch (err) {
      showError("Yuklash xatosi: " + (err.message || err));
    }

    startActiveSecondTimer();
    startSyncCheckTimer();
  }

  els.tasbehBtn.addEventListener("click", function (e) {
    if (mode !== "tap") return;
    e.preventDefault();
    registerDhikr();
  });

  els.modeTap.addEventListener("click", async function () {
    setModeUI("tap");
    try {
      await ensureSession("tap");
    } catch (err) {
      showError(err.message || String(err));
    }
  });

  els.modeSwipe.addEventListener("click", async function () {
    setModeUI("swipe");
    try {
      await ensureSession("swipe");
    } catch (err) {
      showError(err.message || String(err));
    }
  });

  els.tasbehSurface.addEventListener(
    "touchstart",
    function (e) {
      if (mode !== "swipe") return;
      const t = e.changedTouches[0];
      swipeTracking = true;
      swipeStartY = t.clientY;
      swipeStartX = t.clientX;
    },
    { passive: true }
  );

  els.tasbehSurface.addEventListener(
    "touchend",
    function (e) {
      if (mode !== "swipe" || !swipeTracking) return;
      swipeTracking = false;
      const t = e.changedTouches[0];
      const dy = swipeStartY - t.clientY;
      const dx = Math.abs(t.clientX - swipeStartX);
      if (dy > 50 && dy > dx * 1.2) {
        e.preventDefault();
        registerDhikr();
      }
    },
    { passive: false }
  );

  if (els.idleContinueBtn) {
    els.idleContinueBtn.addEventListener("click", function () {
      onUserInteraction();
    });
  }

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
      isEngaged = false;
      isIdlePaused = true;
      flushSync(true);
      sendVisitSnapshot();
    } else {
      requireInteractionAfterVisible = true;
      isIdlePaused = true;
      isEngaged = false;
    }
  });

  window.addEventListener("pagehide", function () {
    flushSync(true);
    sendVisitSnapshot();
  });

  window.addEventListener("beforeunload", function () {
    flushSync(true);
    sendVisitSnapshot();
  });

  window.startTasbehApp = function () {
    if (window.__tasbehStarted) return;
    window.__tasbehStarted = true;
    init();
  };
})();
