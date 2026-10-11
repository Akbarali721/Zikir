<script setup>
import { useRouter } from "vue-router";

const router = useRouter();

function goTasbeh() {
  router.push({ name: "tasbeh" });
}
</script>

<template>
  <main class="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center px-6 text-center">
    <h1 class="font-display text-3xl font-bold text-forest">Ruxsat yo‘q</h1>
    <p class="mt-4 font-sans text-base leading-relaxed text-muted">
      Admin panel faqat tasdiqlangan administratorlar uchun. Agar bu xato deb hisoblasangiz, loyiha
      egasiga murojaat qiling.
    </p>
    <button
      type="button"
      class="mt-8 min-h-[44px] rounded-full border border-gold bg-emerald px-8 py-3 font-sans font-bold text-ivory"
      @click="goTasbeh"
    >
      Tasbehga qaytish
    </button>
  </main>
</template>
