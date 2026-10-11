<script setup>
import { useRouter } from "vue-router";
import WelcomeHero from "@/components/welcome/WelcomeHero.vue";

const router = useRouter();

function goToProfile() {
  router.push({ name: "profile" });
}
</script>

<template>
  <main class="mx-auto min-h-dvh max-w-md px-5 pb-[max(1.5rem,env(safe-area-inset-bottom))] pt-[max(1.25rem,env(safe-area-inset-top))]">
    <p class="text-center font-display text-[clamp(1.25rem,4.2vw,1.375rem)] font-semibold tracking-wide text-emerald-mid">
      Million Istig‘for
    </p>

    <WelcomeHero class="mt-3" />

    <div class="mt-6 text-center">
      <h1 class="font-display text-[clamp(1.875rem,7.8vw,2.125rem)] font-bold leading-tight text-forest">
        1&nbsp;000&nbsp;000 istig‘for.
      </h1>
      <p class="mx-auto mt-3 max-w-xs font-display text-[clamp(1.3125rem,5.2vw,1.5rem)] font-semibold leading-snug text-forest">
        Bir kishi uchun juda katta.<br />
        Birgalikda esa uddalash mumkin.
      </p>
      <p class="mx-auto mt-6 max-w-sm font-sans text-base leading-relaxed text-muted">
        Har kuni Instagram, YouTube va boshqa kontentlarga sezmay qancha vaqtimiz ketadi. Shu vaqtning atigi bir necha
        daqiqasini foydali amalga ajratsak-chi?
      </p>
      <div class="mx-auto mt-6 max-w-sm rounded-2xl border border-gold/40 bg-ivory p-4 text-left shadow-md shadow-forest/5">
        <p class="font-sans text-[15px] font-medium leading-relaxed text-forest">
          Siz aytgan har bir istig‘for umumiy
          <strong class="font-bold text-emerald">1&nbsp;000&nbsp;000</strong>
          maqsadiga qo‘shiladi.
        </p>
      </div>
      <p class="mx-auto mt-6 max-w-xs font-sans text-sm leading-relaxed text-muted">
        <span class="block">Bir necha daqiqa.</span>
        <span class="block">Bir kichik hissa.</span>
        <span class="mt-2 block font-display text-[clamp(1.3125rem,5vw,1.5rem)] font-semibold text-forest">
          Bitta katta umumiy maqsad.
        </span>
      </p>
    </div>

    <button
      type="button"
      class="mt-8 min-h-[44px] w-full rounded-full border border-gold bg-gradient-to-b from-emerald-mid via-emerald to-forest px-6 py-4 font-sans text-lg font-bold text-ivory shadow-lg shadow-forest/25 transition-transform active:scale-[0.99] motion-reduce:transition-none"
      @click="goToProfile"
    >
      Men ham qo‘shilaman
    </button>
  </main>
</template>
