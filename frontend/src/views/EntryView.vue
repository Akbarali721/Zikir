<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { useUserStore } from "@/stores/user";
import { allowDevAuth } from "@/services/clientConfig";
import { getTelegramInitData } from "@/services/telegram";

const router = useRouter();
const userStore = useUserStore();

const phase = ref("loading");
const message = ref("");

async function routeAfterBootstrap() {
  if (userStore.me && userStore.onboardingCompleted) {
    await router.replace({ name: "tasbeh" });
  } else if (userStore.me) {
    await router.replace({ name: "welcome" });
  } else if (userStore.authError) {
    phase.value = "error";
    message.value = userStore.authError;
  } else {
    phase.value = "error";
    message.value = "Ma’lumotlarni yuklab bo‘lmadi.";
  }
}

async function tryBootstrap() {
  phase.value = "loading";
  message.value = "";
  userStore.resetBootstrap();
  await userStore.bootstrap();
  await routeAfterBootstrap();
}

onMounted(() => {
  tryBootstrap();
});

const showTelegramHint = () => !getTelegramInitData() && !allowDevAuth();
</script>

<template>
  <main class="flex min-h-dvh flex-col items-center justify-center px-6 text-center">
    <p v-if="phase === 'loading'" class="font-sans text-sm text-muted">Yuklanmoqda…</p>
    <template v-else>
      <p class="font-sans text-base text-forest" role="alert">{{ message }}</p>
      <p v-if="showTelegramHint()" class="mt-3 max-w-sm font-sans text-sm text-muted">
        Iltimos, ilovani Telegram bot orqali oching. Brauzerda to‘g‘ridan-to‘g‘ri kirish faqat Telegram autentifikatsiyasi
        bilan ishlaydi.
      </p>
      <button
        type="button"
        class="mt-6 min-h-[44px] rounded-full border border-gold bg-emerald px-8 py-3 font-sans font-bold text-ivory"
        @click="tryBootstrap"
      >
        Qayta urinish
      </button>
    </template>
  </main>
</template>
