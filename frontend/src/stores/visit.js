import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "@/services/api";

const STORAGE_PREFIX = "million_visit_id_v1";

function storageKey(telegramId) {
  if (!telegramId) return STORAGE_PREFIX;
  return `${STORAGE_PREFIX}_${telegramId}`;
}

export const useVisitStore = defineStore("visit", () => {
  const visitId = ref(null);
  let heartbeatTimer = null;
  let boundTelegramId = null;

  function loadStored(telegramId) {
    boundTelegramId = telegramId ?? null;
    try {
      const raw = sessionStorage.getItem(storageKey(boundTelegramId));
      if (raw) visitId.value = raw;
      else visitId.value = null;
    } catch {
      /* ignore */
    }
  }

  function persist(id) {
    visitId.value = id;
    try {
      sessionStorage.setItem(storageKey(boundTelegramId), id);
    } catch {
      /* ignore */
    }
  }

  function clearForUserSwitch() {
    visitId.value = null;
    stopHeartbeat();
  }

  async function heartbeat(route) {
    const res = await api.postVisitHeartbeat({ route }, visitId.value);
    persist(res.visit_id);
    return res;
  }

  function startHeartbeat(getRoute) {
    stopHeartbeat();
    const tick = () => {
      if (document.hidden) return;
      heartbeat(typeof getRoute === "function" ? getRoute() : getRoute).catch(() => {});
    };
    tick();
    heartbeatTimer = setInterval(tick, 25000);
  }

  function stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
    }
  }

  return { visitId, loadStored, heartbeat, startHeartbeat, stopHeartbeat, clearForUserSwitch };
});
