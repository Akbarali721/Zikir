import { defineStore } from "pinia";
import { ref, computed } from "vue";

import { api } from "@/services/api";

export const useUserStore = defineStore("user", () => {
  const me = ref(null);
  const loading = ref(false);
  const bootstrapped = ref(false);
  const error = ref(null);
  const authError = ref(null);

  const isAdmin = computed(() => Boolean(me.value?.is_admin));

  async function fetchMe() {
    loading.value = true;
    error.value = null;
    try {
      const prevTid = me.value?.user?.telegram_id;
      me.value = await api.getMe();
      const nextTid = me.value?.user?.telegram_id;
      if (prevTid != null && nextTid != null && prevTid !== nextTid) {
        const { useVisitStore } = await import("@/stores/visit");
        useVisitStore().clearForUserSwitch();
        try {
          Object.keys(sessionStorage).forEach((k) => {
            if (k.startsWith("tasbeh_pending_batch_v2")) sessionStorage.removeItem(k);
          });
        } catch {
          /* ignore */
        }
      }
      authError.value = null;
      return me.value;
    } catch (err) {
      error.value = err.message || "Failed to load user";
      if (err.status === 401 || err.status === 403) {
        authError.value =
          "Kirish rad etildi. Telegram orqali oching yoki mahalliy DEV rejimini sozlang.";
      } else {
        authError.value = err.message || "Internet yoki server bilan bog‘lanishda xatolik.";
      }
      me.value = null;
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function bootstrap() {
    if (bootstrapped.value) return me.value;
    try {
      await fetchMe();
    } catch {
      /* routing handles unauthenticated / offline */
    } finally {
      bootstrapped.value = true;
    }
    return me.value;
  }

  function resetBootstrap() {
    bootstrapped.value = false;
  }

  return {
    me,
    loading,
    bootstrapped,
    error,
    authError,
    isAdmin,
    fetchMe,
    bootstrap,
    resetBootstrap,
  };
});
