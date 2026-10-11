import { computed, onMounted, onUnmounted, ref, shallowRef } from "vue";
import { api, buildAuthHeaders } from "@/services/api";
import { useVisitStore } from "@/stores/visit";
import { formatActiveTimeUz, formatGoalRemainingUz, formatNumber } from "@/utils/format";

const SYNC_DHikR_THRESHOLD = 15;
const SYNC_INTERVAL_MS = 7000;
const IDLE_TIMEOUT_MS = 45000;
const PENDING_STORAGE = "tasbeh_pending_batch_v2";

function newBatchId() {
  return crypto.randomUUID();
}

export function useTasbehEngine() {
  const visitStore = useVisitStore();

  const loading = ref(true);
  const error = ref("");
  const mode = ref("tap");
  const sessionId = ref(null);

  const pendingDhikr = ref(0);
  const pendingActiveSeconds = ref(0);
  const currentBatchId = ref(null);

  const displaySessionDhikr = ref(0);
  const displaySessionActiveSeconds = ref(0);
  const displayPersonalDhikr = ref(0);
  const displayPersonalSeconds = ref(0);

  const todayBaseDhikr = ref(0);
  const todayBaseSeconds = ref(0);
  const initialSessionDhikr = ref(0);
  const initialSessionActiveSeconds = ref(0);
  const sessionCountsForToday = ref(true);

  const globalProgress = shallowRef(null);
  const mePayload = shallowRef(null);

  const isEngaged = ref(false);
  const isIdlePaused = ref(true);
  const requireInteractionAfterVisible = ref(false);
  const showIdleBanner = ref(false);

  let syncInFlight = false;
  let syncQueued = false;
  let lastSyncAt = Date.now();
  let idleTimer = null;
  let activeSecondTimer = null;
  let syncCheckTimer = null;
  let progressPollTimer = null;
  let progressPollInFlight = false;

  let swipeTracking = false;
  let swipeStartY = 0;
  let swipeStartX = 0;
  let lastTouchAt = 0;

  const countBump = ref(false);
  const fxItems = ref([]);

  const sessionCountFormatted = computed(() => formatNumber(displaySessionDhikr.value));
  const todayDhikrFormatted = computed(() => formatNumber(computeDisplayTodayDhikr()));
  const todayTimeFormatted = computed(() => formatActiveTimeUz(computeDisplayTodaySeconds()));
  const personalDhikrFormatted = computed(() => formatNumber(displayPersonalDhikr.value));
  const personalTimeFormatted = computed(() => formatActiveTimeUz(displayPersonalSeconds.value));

  function computeDisplayTodayDhikr() {
    if (!sessionCountsForToday.value) return todayBaseDhikr.value;
    return (
      todayBaseDhikr.value +
      (displaySessionDhikr.value - initialSessionDhikr.value) +
      pendingDhikr.value
    );
  }

  function computeDisplayTodaySeconds() {
    if (!sessionCountsForToday.value) return todayBaseSeconds.value;
    return (
      todayBaseSeconds.value +
      (displaySessionActiveSeconds.value - initialSessionActiveSeconds.value) +
      pendingActiveSeconds.value
    );
  }

  function pendingStorageKey() {
    const tid = mePayload.value?.user?.telegram_id;
    return tid ? `${PENDING_STORAGE}_${tid}` : null;
  }

  function savePendingLocal() {
    const key = pendingStorageKey();
    if (!key || !currentBatchId.value) return;
    if (pendingDhikr.value === 0 && pendingActiveSeconds.value === 0) {
      sessionStorage.removeItem(key);
      return;
    }
    sessionStorage.setItem(
      key,
      JSON.stringify({
        batchId: currentBatchId.value,
        sessionId: sessionId.value,
        dhikr: pendingDhikr.value,
        seconds: pendingActiveSeconds.value,
      }),
    );
  }

  function restorePendingLocal() {
    const key = pendingStorageKey();
    if (!key) return;
    try {
      const raw = sessionStorage.getItem(key);
      if (!raw) return;
      const data = JSON.parse(raw);
      if (data.sessionId === sessionId.value) {
        currentBatchId.value = data.batchId;
        pendingDhikr.value += data.dhikr || 0;
        pendingActiveSeconds.value += data.seconds || 0;
      }
    } catch {
      /* ignore */
    }
  }

  function canCountActiveTime() {
    return (
      !document.hidden &&
      isEngaged.value &&
      !isIdlePaused.value &&
      !requireInteractionAfterVisible.value &&
      sessionId.value !== null
    );
  }

  function resetIdleTimer() {
    if (idleTimer) clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
      isIdlePaused.value = true;
      isEngaged.value = false;
      showIdleBanner.value = displaySessionDhikr.value > 0;
    }, IDLE_TIMEOUT_MS);
  }

  function onUserInteraction() {
    if (document.hidden) return;
    requireInteractionAfterVisible.value = false;
    isIdlePaused.value = false;
    isEngaged.value = true;
    showIdleBanner.value = false;
    resetIdleTimer();
  }

  function ensureBatchId() {
    if (!currentBatchId.value) {
      currentBatchId.value = newBatchId();
    }
  }

  function triggerDhikrFx(fxPoint) {
    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (!reduced) {
      countBump.value = false;
      requestAnimationFrame(() => {
        countBump.value = true;
        window.setTimeout(() => {
          countBump.value = false;
        }, 150);
      });
    }

    const x = fxPoint?.center ? 50 : (fxPoint?.x ?? 50);
    const y = fxPoint?.center ? 42 : (fxPoint?.y ?? 42);
    const id = Date.now() + Math.random();
    const ring = { id: `${id}-ring`, type: "ring", x, y };
    const plus = { id: `${id}-plus`, type: "plus1", x, y: y - 8 };

    fxItems.value = [...fxItems.value, ring, plus];

    const removeMs = reduced ? 0 : 460;
    window.setTimeout(() => {
      fxItems.value = fxItems.value.filter((item) => item.id !== ring.id && item.id !== plus.id);
    }, removeMs);
  }

  function registerDhikr(fxPoint) {
    if (!sessionId.value) return;
    onUserInteraction();
    ensureBatchId();
    pendingDhikr.value += 1;
    displaySessionDhikr.value += 1;
    displayPersonalDhikr.value += 1;
    savePendingLocal();
    maybeScheduleSync(true);
    triggerDhikrFx(fxPoint);
    if (navigator.vibrate) navigator.vibrate(20);
  }

  async function flushSync(useKeepalive = false) {
    if (!sessionId.value) return;
    if (pendingDhikr.value === 0 && pendingActiveSeconds.value === 0) return;

    if (syncInFlight) {
      syncQueued = true;
      return;
    }

    syncInFlight = true;
    ensureBatchId();
    const sendDhikr = pendingDhikr.value;
    const sendSeconds = pendingActiveSeconds.value;
    const batchId = currentBatchId.value;
    const sid = sessionId.value;

    pendingDhikr.value = 0;
    pendingActiveSeconds.value = 0;
    savePendingLocal();

    const body = {
      session_id: sid,
      dhikr_delta: sendDhikr,
      active_seconds_delta: sendSeconds,
      batch_id: batchId,
    };

    try {
      let data;
      if (useKeepalive) {
        const res = await fetch("/api/tasbeh/sync", {
          method: "POST",
          headers: buildAuthHeaders(true, visitStore.visitId),
          body: JSON.stringify(body),
          keepalive: true,
        });
        if (!res.ok) throw new Error("Sync failed");
        data = await res.json();
      } else {
        data = await api.postTasbehSync(body, visitStore.visitId);
      }

      lastSyncAt = Date.now();
      displaySessionDhikr.value = data.session_dhikr_count;
      displaySessionActiveSeconds.value = data.session_active_seconds;
      displayPersonalDhikr.value = data.personal_dhikr_count;
      displayPersonalSeconds.value = data.personal_active_seconds;
      initialSessionDhikr.value = data.session_dhikr_count;
      initialSessionActiveSeconds.value = data.session_active_seconds;
      if (sessionCountsForToday.value) {
        todayBaseDhikr.value += sendDhikr;
        todayBaseSeconds.value += sendSeconds;
      }
      currentBatchId.value = newBatchId();
      savePendingLocal();
      error.value = "";
      pollProgress(false).catch(() => {});
    } catch (err) {
      pendingDhikr.value += sendDhikr;
      pendingActiveSeconds.value += sendSeconds;
      currentBatchId.value = batchId;
      savePendingLocal();
      error.value = err.message || "Sinxronlash xatosi";
      if (err.status === 409) {
        await recoverSessionConflict(err);
      }
    } finally {
      syncInFlight = false;
      if (syncQueued) {
        syncQueued = false;
        flushSync(false);
      }
    }
  }

  async function recoverSessionConflict(err) {
    try {
      const me = await api.getMe();
      mePayload.value = me;
      if (me.session?.is_active) {
        sessionId.value = me.session.id;
        mode.value = me.session.mode;
        displaySessionDhikr.value = me.session.dhikr_count;
        displaySessionActiveSeconds.value = me.session.active_seconds;
        initialSessionDhikr.value = me.session.dhikr_count;
        initialSessionActiveSeconds.value = me.session.active_seconds;
      }
    } catch {
      /* ignore */
    }
    error.value =
      "Sessiya boshqa oynada ochilgan bo‘lishi mumkin. Ma’lumotlar tiklanmoqda…";
  }

  function maybeScheduleSync(fromAction) {
    const elapsed = Date.now() - lastSyncAt;
    if (
      pendingDhikr.value >= SYNC_DHikR_THRESHOLD ||
      elapsed >= SYNC_INTERVAL_MS ||
      (fromAction && pendingDhikr.value > 0 && elapsed >= 2000)
    ) {
      flushSync(false);
    }
  }

  async function startSession(selectedMode) {
    const data = await api.postSessionStart({ mode: selectedMode });
    sessionId.value = data.session_id;
    mode.value = data.mode;
    displaySessionDhikr.value = 0;
    displaySessionActiveSeconds.value = 0;
    initialSessionDhikr.value = 0;
    initialSessionActiveSeconds.value = 0;
    sessionCountsForToday.value = true;
    isIdlePaused.value = true;
    isEngaged.value = false;
    requireInteractionAfterVisible.value = false;
    showIdleBanner.value = false;
    currentBatchId.value = newBatchId();
  }

  async function ensureSession(selectedMode) {
    if (sessionId.value) {
      if (mode.value !== selectedMode) {
        await flushSync(false);
        await api.postSessionStop();
        await startSession(selectedMode);
      }
      return;
    }
    await startSession(selectedMode);
  }

  async function setMode(selectedMode) {
    mode.value = selectedMode;
    try {
      await ensureSession(selectedMode);
    } catch (err) {
      error.value = err.message || String(err);
    }
  }

  function onTap(e) {
    if (mode.value !== "tap") return;
    if (Date.now() - lastTouchAt < 400) {
      e.preventDefault();
      return;
    }
    e.preventDefault();
    const el = e.currentTarget;
    const rect = el.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    registerDhikr({ x, y });
  }

  function onTouchStart(e) {
    if (mode.value !== "swipe") return;
    const t = e.changedTouches[0];
    swipeTracking = true;
    swipeStartY = t.clientY;
    swipeStartX = t.clientX;
    lastTouchAt = Date.now();
  }

  function onTouchEnd(e) {
    if (mode.value !== "swipe" || !swipeTracking) return;
    swipeTracking = false;
    const t = e.changedTouches[0];
    const dy = swipeStartY - t.clientY;
    const dx = Math.abs(t.clientX - swipeStartX);
    lastTouchAt = Date.now();
    if (dy > 50 && dy > dx * 1.2) {
      e.preventDefault();
      registerDhikr({ center: true });
    }
  }

  async function pollProgress(force) {
    if (progressPollInFlight && !force) return;
    progressPollInFlight = true;
    try {
      const progress = await api.getProgress();
      globalProgress.value = progress.global;
    } catch {
      /* progress xatosi syncni qayta yubormaydi */
    } finally {
      progressPollInFlight = false;
    }
  }

  async function bootstrap(me, progress) {
    mePayload.value = me;
    displayPersonalDhikr.value = me.personal_dhikr_count;
    displayPersonalSeconds.value = me.personal_active_seconds;
    todayBaseDhikr.value = me.today.dhikr;
    todayBaseSeconds.value = me.today.active_seconds;
    globalProgress.value = progress.global;

    if (me.session?.is_active) {
      sessionId.value = me.session.id;
      mode.value = me.session.mode;
      displaySessionDhikr.value = me.session.dhikr_count;
      displaySessionActiveSeconds.value = me.session.active_seconds;
      initialSessionDhikr.value = me.session.dhikr_count;
      initialSessionActiveSeconds.value = me.session.active_seconds;
      sessionCountsForToday.value = me.session.counts_for_today !== false;
    } else {
      await startSession("tap");
    }
    restorePendingLocal();
    if (pendingDhikr.value > 0 || pendingActiveSeconds.value > 0) {
      flushSync(false);
    }
    loading.value = false;
  }

  function onVisibilityChange() {
    if (document.hidden) {
      isEngaged.value = false;
      isIdlePaused.value = true;
      flushSync(true);
      api.postVisitSnapshot().catch(() => {});
    } else {
      requireInteractionAfterVisible.value = true;
      isIdlePaused.value = true;
      isEngaged.value = false;
    }
  }

  function startTimers() {
    activeSecondTimer = setInterval(() => {
      if (canCountActiveTime()) {
        pendingActiveSeconds.value += 1;
        displayPersonalSeconds.value += 1;
        displaySessionActiveSeconds.value += 1;
        savePendingLocal();
      }
    }, 1000);

    syncCheckTimer = setInterval(() => maybeScheduleSync(false), 1000);

    progressPollTimer = setInterval(() => {
      if (!document.hidden) pollProgress(false);
    }, 15000);
  }

  function stopTimers() {
    if (idleTimer) clearTimeout(idleTimer);
    if (activeSecondTimer) clearInterval(activeSecondTimer);
    if (syncCheckTimer) clearInterval(syncCheckTimer);
    if (progressPollTimer) clearInterval(progressPollTimer);
  }

  onMounted(() => {
    document.addEventListener("visibilitychange", onVisibilityChange);
    window.addEventListener("pagehide", () => {
      flushSync(true);
      api.postVisitSnapshot().catch(() => {});
    });
    startTimers();
  });

  onUnmounted(() => {
    document.removeEventListener("visibilitychange", onVisibilityChange);
    stopTimers();
    flushSync(true);
  });

  return {
    loading,
    error,
    mode,
    mePayload,
    globalProgress,
    sessionCountFormatted,
    todayDhikrFormatted,
    todayTimeFormatted,
    personalDhikrFormatted,
    personalTimeFormatted,
    showIdleBanner,
    countBump,
    fxItems,
    formatNumber,
    formatActiveTimeUz,
    formatGoalRemainingUz,
    setMode,
    onTap,
    onTouchStart,
    onTouchEnd,
    onUserInteraction,
    bootstrap,
    pollProgress,
    computeDisplayTodayDhikr,
  };
}
