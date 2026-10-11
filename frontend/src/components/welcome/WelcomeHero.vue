<script setup>
import archUrl from "@/assets/images/welcome/arch-frame.svg";
import badgeUrl from "@/assets/images/welcome/hero-badge.svg";
import lanternLeftUrl from "@/assets/images/welcome/lantern-left.svg";
import lanternRightUrl from "@/assets/images/welcome/lantern-right.svg";
</script>

<template>
  <section class="relative mx-auto h-[min(320px,78vw)] w-full max-w-[380px]" aria-label="Million Istig‘for maqsadi">
    <img
      :src="archUrl"
      alt=""
      class="pointer-events-none absolute inset-0 h-full w-full object-contain object-top"
      decoding="async"
    />
    <img
      :src="lanternLeftUrl"
      alt=""
      class="pointer-events-none absolute left-2 top-1.5 w-[clamp(36px,10.5vw,44px)] drop-shadow-md"
    />
    <img
      :src="lanternRightUrl"
      alt=""
      class="pointer-events-none absolute right-2 top-1.5 w-[clamp(36px,10.5vw,44px)] drop-shadow-md"
    />
    <div class="absolute left-1/2 top-[56%] w-[min(270px,72vw)] max-w-[280px] -translate-x-1/2 -translate-y-1/2">
      <img :src="badgeUrl" alt="" class="block w-full" decoding="async" />
      <div
        class="absolute inset-0 flex flex-col items-center justify-center gap-1.5 pt-1 text-center"
        aria-label="1 000 000 istig‘for"
      >
        <span class="font-display text-[clamp(2.625rem,7.5vw,3rem)] font-bold leading-none text-ivory tabular-nums drop-shadow">
          1&nbsp;000&nbsp;000
        </span>
        <span class="font-sans text-[clamp(0.75rem,3.2vw,0.875rem)] font-bold tracking-[0.3em] text-gold-soft">
          ISTIG‘FOR
        </span>
      </div>
    </div>
  </section>
</template>
