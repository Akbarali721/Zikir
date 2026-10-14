/** Million istig‘for challenge — server sync global/personal statistikaga qo‘shiladi. */
export const CHALLENGE_MILLION = "million_istighfor";

/** 33 marta aylanadigan tasbeh — global million challenge bilan aralashmaydi. */
export const CHALLENGE_TASBEH_33 = "tasbeh_33";

export const TASBEH_33_PHRASES = ["Subhanalloh", "Alhamdulillah", "Allohu akbar"];

export const TASBEH_33_ROUND_SIZE = 33;

export function phraseForTasbeh33Step(stepOneBased) {
  const idx = (Math.max(1, stepOneBased) - 1) % TASBEH_33_PHRASES.length;
  return TASBEH_33_PHRASES[idx];
}

export const CHALLENGE_STORAGE_KEY = "tasbeh_challenge_v1";
export const TASBEH_33_PROGRESS_KEY = "tasbeh_33_progress_v1";
