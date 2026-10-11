<script setup>
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

import { useUserStore } from "@/stores/user";
import { getTelegramUserUnsafe } from "@/services/telegram";

const router = useRouter();
const userStore = useUserStore();

const displayName = ref(userStore.me?.display_name || getTelegramUserUnsafe()?.first_name || "");
const age = ref(userStore.me?.age ?? "");
const submitting = ref(false);
const fieldError = ref("");

const ageNum = computed(() => Number(age.value));

function validate() {
  const name = displayName.value.trim();
  if (name.length < 2) {
    fieldError.value = "Ism kamida 2 ta belgidan iborat bo‘lishi kerak.";
    return false;
  }
  if (!Number.isFinite(ageNum.value) || ageNum.value < 10 || ageNum.value > 100) {
    fieldError.value = "Yosh 10 dan 100 gacha bo‘lishi kerak.";
    return false;
  }
  fieldError.value = "";
  return true;
}

async function onSubmit() {
  if (submitting.value) return;
  if (!validate()) return;
  submitting.value = true;
  try {
    await userStore.submitOnboarding(displayName.value.trim(), ageNum.value);
    await router.push({ name: "tasbeh" });
  } catch (err) {
    fieldError.value = err.message || "Saqlashda xatolik yuz berdi.";
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <main class="mx-auto min-h-dvh max-w-md px-5 pb-[max(1.5rem,env(safe-area-inset-bottom))] pt-[max(1.25rem,env(safe-area-inset-top))]">
    <h1 class="font-display text-3xl font-bold text-forest">Profil</h1>
    <p class="mt-2 font-sans text-base text-muted">Ismingiz va yoshingiz — bir martalik sozlash.</p>

    <form class="mt-8 space-y-5" novalidate @submit.prevent="onSubmit">
      <label class="block">
        <span class="font-sans text-sm font-medium text-forest">Ismingiz</span>
        <input
          v-model="displayName"
          type="text"
          autocomplete="name"
          maxlength="50"
          class="mt-1.5 min-h-[44px] w-full rounded-xl border border-gold/30 bg-ivory px-4 py-3 font-sans text-base text-forest outline-none focus:border-emerald"
        />
      </label>

      <label class="block">
        <span class="font-sans text-sm font-medium text-forest">Yoshingiz</span>
        <input
          v-model.number="age"
          type="number"
          inputmode="numeric"
          min="10"
          max="100"
          class="mt-1.5 min-h-[44px] w-full rounded-xl border border-gold/30 bg-ivory px-4 py-3 font-sans text-base text-forest outline-none focus:border-emerald"
        />
      </label>

      <p v-if="fieldError" class="font-sans text-sm text-red-800" role="alert">{{ fieldError }}</p>

      <button
        type="submit"
        :disabled="submitting"
        class="min-h-[44px] w-full rounded-full border border-gold bg-emerald px-6 py-4 font-sans text-lg font-bold text-ivory disabled:opacity-60"
      >
        {{ submitting ? "Saqlanmoqda…" : "Davom etish" }}
      </button>
    </form>
  </main>
</template>
