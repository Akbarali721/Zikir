<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";

import { api } from "@/services/api";
import { formatActiveTimeUz, formatNumber } from "@/utils/format";

const overview = ref(null);
const users = ref([]);
const usersTotal = ref(0);
const daily = ref([]);
const funnel = ref(null);
const loading = ref(true);
const error = ref("");
const lastUpdated = ref(null);
const q = ref("");

let refreshTimer = null;

async function loadAll() {
  loading.value = true;
  error.value = "";
  try {
    const [ov, us, ser, fun] = await Promise.all([
      api.adminOverview(),
      api.adminUsers({ page: 1, page_size: 50, q: q.value || undefined }),
      api.adminDaily(30),
      api.adminFunnel(7),
    ]);
    overview.value = ov;
    users.value = us.items;
    usersTotal.value = us.total;
    daily.value = ser;
    funnel.value = fun;
    lastUpdated.value = new Date();
  } catch (err) {
    error.value = err.status === 403 ? "Admin ruxsati yo‘q." : err.message || "Yuklash xatosi";
  } finally {
    loading.value = false;
  }
}

function onVisibility() {
  if (document.hidden) {
    if (refreshTimer) clearInterval(refreshTimer);
    refreshTimer = null;
  } else {
    loadAll();
    refreshTimer = setInterval(loadAll, 30000);
  }
}

const updatedLabel = computed(() =>
  lastUpdated.value ? lastUpdated.value.toLocaleTimeString("uz-UZ") : "—",
);

onMounted(() => {
  loadAll();
  refreshTimer = setInterval(() => {
    if (!document.hidden) loadAll();
  }, 30000);
  document.addEventListener("visibilitychange", onVisibility);
});

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer);
  document.removeEventListener("visibilitychange", onVisibility);
});
</script>

<template>
  <div class="min-h-dvh bg-cream pb-10 pt-[max(1rem,env(safe-area-inset-top))]">
    <div class="mx-auto max-w-6xl px-4">
      <header class="flex flex-wrap items-end justify-between gap-3 border-b border-gold/30 pb-4">
        <div>
          <h1 class="font-display text-3xl font-bold text-forest">Admin panel</h1>
          <p class="font-sans text-sm text-muted">Faqat o‘qish rejimi · oxirgi yangilanish: {{ updatedLabel }}</p>
        </div>
        <button
          type="button"
          class="min-h-[44px] rounded-full border border-gold bg-emerald px-5 font-sans text-sm font-bold text-ivory"
          @click="loadAll"
        >
          Yangilash
        </button>
      </header>

      <p v-if="error" class="mt-4 rounded-lg bg-red-50 px-4 py-3 font-sans text-sm text-red-900">{{ error }}</p>
      <p v-if="loading && !overview" class="mt-8 font-sans text-muted">Yuklanmoqda…</p>

      <section v-if="overview" class="mt-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        <article v-for="card in [
          { label: 'Jami foydalanuvchilar', value: formatNumber(overview.total_users) },
          { label: 'Bugun tashrif (nozik)', value: formatNumber(overview.today_distinct_visitors) },
          { label: 'Bugun yangi', value: formatNumber(overview.today_new_users) },
          { label: 'Onlayn (60s)', value: formatNumber(overview.online_users) },
          { label: 'Zikr qilmoqda', value: formatNumber(overview.dhikring_users) },
          { label: 'Jami zikr', value: formatNumber(overview.total_dhikr) },
          { label: 'Bugungi zikr', value: formatNumber(overview.today_dhikr) },
          { label: 'Bugungi faol vaqt', value: formatActiveTimeUz(overview.today_active_seconds) },
        ]" :key="card.label" class="rounded-xl border border-gold/25 bg-ivory p-4 shadow-sm">
          <p class="font-sans text-xs text-muted">{{ card.label }}</p>
          <p class="mt-1 font-sans text-lg font-bold text-forest">{{ card.value }}</p>
        </article>
      </section>

      <section v-if="funnel" class="mt-8 rounded-xl border border-gold/25 bg-ivory p-4">
        <h2 class="font-display text-xl font-semibold text-forest">7 kunlik voronka</h2>
        <ul class="mt-3 space-y-1 font-sans text-sm text-forest">
          <li>Yakunlangan tashriflar: {{ funnel.completed_visits }}</li>
          <li>Zikr boshlagan: {{ funnel.visits_with_dhikr }}</li>
          <li>Zikrsiz chiqqan: {{ funnel.left_without_dhikr }}</li>
          <li>Yangi foydalanuvchi: {{ funnel.new_users }} · onboarding: {{ funnel.onboarded_new_users }}</li>
        </ul>
      </section>

      <section class="mt-8">
        <div class="flex flex-wrap gap-2">
          <input
            v-model="q"
            type="search"
            placeholder="Ism, username yoki Telegram ID"
            class="min-h-[44px] flex-1 rounded-xl border border-gold/30 bg-ivory px-4 font-sans text-sm"
            @keyup.enter="loadAll"
          />
          <button type="button" class="min-h-[44px] rounded-full border border-gold px-4 font-sans text-sm" @click="loadAll">
            Qidirish
          </button>
        </div>
        <p class="mt-2 font-sans text-xs text-muted">Jami: {{ usersTotal }}</p>
        <div class="mt-3 overflow-x-auto rounded-xl border border-gold/25 bg-ivory">
          <table class="min-w-full text-left font-sans text-sm">
            <thead class="border-b border-gold/20 text-xs text-muted">
              <tr>
                <th class="p-3">Ism</th>
                <th class="p-3">Username</th>
                <th class="p-3">TG ID</th>
                <th class="p-3">Zikr</th>
                <th class="p-3">Faol vaqt</th>
                <th class="p-3">Onboarding</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in users" :key="u.id" class="border-b border-gold/10">
                <td class="p-3">{{ u.display_name || u.first_name || "—" }}</td>
                <td class="p-3">{{ u.username ? "@" + u.username : "—" }}</td>
                <td class="p-3 tabular-nums">{{ u.telegram_id }}</td>
                <td class="p-3">{{ formatNumber(u.personal_dhikr_count) }}</td>
                <td class="p-3">{{ formatActiveTimeUz(u.personal_active_seconds) }}</td>
                <td class="p-3">{{ u.onboarding_completed ? "Tugagan" : "Kutilmoqda" }}</td>
              </tr>
              <tr v-if="!users.length">
                <td colspan="6" class="p-6 text-center text-muted">Ma’lumot yo‘q</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section v-if="daily.length" class="mt-8">
        <h2 class="font-display text-xl font-semibold text-forest">30 kun · kunlik</h2>
        <div class="mt-3 max-h-64 overflow-auto rounded-xl border border-gold/25 bg-ivory">
          <table class="min-w-full font-sans text-sm">
            <thead class="sticky top-0 bg-ivory text-xs text-muted">
              <tr>
                <th class="p-2 text-left">Sana</th>
                <th class="p-2 text-right">Tashrif</th>
                <th class="p-2 text-right">Zikr</th>
                <th class="p-2 text-right">Faol vaqt</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in daily" :key="row.date" class="border-t border-gold/10">
                <td class="p-2">{{ row.date }}</td>
                <td class="p-2 text-right">{{ row.visitors }}</td>
                <td class="p-2 text-right">{{ formatNumber(row.dhikr) }}</td>
                <td class="p-2 text-right">{{ formatActiveTimeUz(row.active_seconds) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>
