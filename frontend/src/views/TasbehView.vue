<script setup>
import { computed, onMounted } from "vue";
import { useRoute } from "vue-router";

import { useTasbehEngine } from "@/composables/useTasbehEngine";
import { api } from "@/services/api";
import { useUserStore } from "@/stores/user";
import { useVisitStore } from "@/stores/visit";
import { formatActiveTimeUz, formatGoalRemainingUz, formatNumber } from "@/utils/format";

const userStore = useUserStore();
const visitStore = useVisitStore();
const route = useRoute();

const engine = useTasbehEngine();

const displayName = computed(() => {
  const me = engine.mePayload.value || userStore.me;
  return me?.display_name || me?.user?.first_name || "do‘st";
});

const global = computed(() => engine.globalProgress.value);

const returnGrowth = computed(() => {
  const me = engine.mePayload.value;
  const g = me?.retention?.global_growth_since_last_visit;
  return g != null && g > 0 ? g : null;
});

async function initTasbeh() {
  const [me, progress] = await Promise.all([api.getMe(), api.getProgress()]);
  userStore.me = me;
  visitStore.loadStored(me?.user?.telegram_id);
  visitStore.startHeartbeat(() => route.name);
  await engine.bootstrap(me, progress);
}

onMounted(() => {
  initTasbeh().catch((err) => {
    engine.error.value = err.message || "Yuklash xatosi";
    engine.loading.value = false;
  });
});

</script>

<template>
  <main
    class="mx-auto flex min-h-dvh max-w-md flex-col overflow-x-hidden px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-[max(0.75rem,env(safe-area-inset-top))]"
  >
    <header class="rounded-2xl border border-gold/25 bg-ivory p-4 shadow-sm">
      <p class="font-display text-xl font-semibold text-forest">Xush kelibsiz, {{ displayName }}.</p>
      <p v-if="returnGrowth" class="mt-1 font-sans text-sm text-muted">
        Siz yo‘q paytingizda yana {{ formatNumber(returnGrowth) }} ta istig‘for qo‘shildi.
      </p>
      <div v-if="global" class="mt-3 space-y-2 font-sans text-sm">
        <div class="flex justify-between gap-2 text-forest">
          <span class="text-muted">Jami aytilgan zikr</span>
          <strong class="tabular-nums">{{ formatNumber(global.dhikr) }}</strong>
        </div>
        <div class="flex justify-between gap-2 text-forest">
          <span class="text-muted">Maqsadgacha qolgan zikr</span>
          <strong class="tabular-nums">{{ formatNumber(global.remaining_dhikr) }}</strong>
        </div>
        <div class="flex justify-between gap-2 text-forest">
          <span class="text-muted">Jamoaning yig‘ilgan faol vaqti</span>
          <strong>{{ formatActiveTimeUz(global.active_seconds) }}</strong>
        </div>
        <div class="flex justify-between gap-2 text-forest">
          <span class="text-muted">Million sekunddan qolgan vaqt</span>
          <strong>{{ formatGoalRemainingUz(global.remaining_seconds).replace("Maqsadgacha: ", "") }}</strong>
        </div>
        <div class="mt-1 h-2 overflow-hidden rounded-full bg-cream">
          <div
            class="h-full rounded-full bg-emerald transition-all duration-200 motion-reduce:transition-none"
            :style="{ width: Math.min(100, global.dhikr_percent || 0) + '%' }"
          />
        </div>
      </div>
    </header>

    <div
      v-if="engine.showIdleBanner.value"
      class="mt-3 rounded-xl border border-gold/30 bg-gold-soft/30 p-3 font-sans text-sm text-forest"
    >
      Tanaffus. Davom etish uchun yana bir marta zikr qiling.
      <button type="button" class="ml-2 font-bold text-emerald underline" @click="engine.onUserInteraction()">
        Davom etish
      </button>
    </div>

    <p v-if="engine.error.value" class="mt-3 rounded-lg bg-red-50 px-3 py-2 font-sans text-sm text-red-900" role="alert">
      {{ engine.error.value }}
    </p>

    <section class="mt-4 flex flex-1 flex-col items-center">
      <div class="mb-3 flex gap-2">
        <button
          type="button"
          class="min-h-[44px] rounded-full px-4 font-sans text-sm font-semibold transition-colors"
          :class="engine.mode.value === 'tap' ? 'bg-emerald text-ivory' : 'bg-ivory text-forest border border-gold/30'"
          @click="engine.setMode('tap')"
        >
          Bosish
        </button>
        <button
          type="button"
          class="min-h-[44px] rounded-full px-4 font-sans text-sm font-semibold transition-colors"
          :class="engine.mode.value === 'swipe' ? 'bg-emerald text-ivory' : 'bg-ivory text-forest border border-gold/30'"
          @click="engine.setMode('swipe')"
        >
          Surish
        </button>
      </div>

      <div
        class="relative flex w-full max-w-[min(100%,320px)] flex-col items-center touch-pan-y"
        @touchstart.passive="engine.onTouchStart"
        @touchend="engine.onTouchEnd"
      >
        <button
          type="button"
          class="relative flex min-h-[min(72vw,280px)] w-full flex-col items-center justify-center overflow-hidden rounded-full border-2 border-gold/50 bg-gradient-to-b from-ivory to-cream shadow-lg shadow-forest/10 transition-transform active:scale-[0.98] motion-reduce:transition-none"
          :aria-label="engine.mode.value === 'tap' ? 'Zikr sanash' : 'Pastdan tepaga suring'"
          @click="engine.onTap"
        >
          <div class="dhikr-fx-layer" aria-hidden="true">
            <span
              v-for="item in engine.fxItems.value"
              :key="item.id"
              :class="item.type === 'ring' ? 'dhikr-fx-ring' : 'dhikr-fx-plus1'"
              :style="{ left: item.x + '%', top: item.y + '%' }"
            >
              {{ item.type === "plus1" ? "+1" : "" }}
            </span>
          </div>
          <span class="relative z-10 font-sans text-xs font-semibold uppercase tracking-wide text-muted">Joriy sessiya</span>
          <span
            class="relative z-10 font-display text-[clamp(2.5rem,12vw,3.5rem)] font-bold tabular-nums text-emerald"
            :class="{ 'dhikr-count-bump': engine.countBump.value }"
          >
            {{ engine.sessionCountFormatted.value }}
          </span>
          <span class="relative z-10 mt-2 font-display text-lg text-forest/80">Astaghfirulloh</span>
          <span class="relative z-10 mt-3 font-sans text-sm text-muted">
            {{ engine.mode.value === "swipe" ? "Pastdan tepaga suring" : "Bosish orqali zikr qiling" }}
          </span>
        </button>
      </div>
    </section>

    <section class="mt-4 grid grid-cols-2 gap-2 font-sans text-sm">
      <div class="rounded-xl border border-gold/20 bg-ivory p-3">
        <p class="text-xs text-muted">Bugungi hissam</p>
        <p class="font-bold text-forest">{{ engine.todayDhikrFormatted.value }} zikr</p>
        <p class="text-xs text-muted">{{ engine.todayTimeFormatted.value }}</p>
      </div>
      <div class="rounded-xl border border-gold/20 bg-ivory p-3">
        <p class="text-xs text-muted">Jami shaxsiy</p>
        <p class="font-bold text-forest">{{ engine.personalDhikrFormatted.value }}</p>
        <p class="text-xs text-muted">{{ engine.personalTimeFormatted.value }}</p>
      </div>
    </section>

    <p v-if="engine.loading.value" class="mt-4 text-center font-sans text-sm text-muted">Tayyorlanmoqda…</p>
  </main>
</template>
