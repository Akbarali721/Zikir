import { defineStore } from "pinia";
import { ref } from "vue";

import { api } from "@/services/api";

/** Placeholder store for tasbeh session/sync — full port comes later. */
export const useTasbehStore = defineStore("tasbeh", () => {
  const progress = ref(null);
  const loading = ref(false);

  async function fetchProgress() {
    loading.value = true;
    try {
      progress.value = await api.getProgress();
      return progress.value;
    } finally {
      loading.value = false;
    }
  }

  return {
    progress,
    loading,
    fetchProgress,
  };
});
