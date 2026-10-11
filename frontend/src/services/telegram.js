/**
 * Telegram WebApp helpers. Auth is validated on the backend from initData only.
 */

export function getTelegramWebApp() {
  if (typeof window === "undefined") return null;
  return window.Telegram?.WebApp ?? null;
}

export function getTelegramInitData() {
  const tg = getTelegramWebApp();
  return tg?.initData?.trim() || "";
}

export function getTelegramUserUnsafe() {
  const tg = getTelegramWebApp();
  return tg?.initDataUnsafe?.user ?? null;
}

export function initTelegramWebApp() {
  const tg = getTelegramWebApp();
  if (!tg) return;
  tg.ready();
  if (typeof tg.expand === "function") {
    tg.expand();
  }
}

/** @deprecated clientConfig.allowDevAuth() ishlating */
export function isLocalDevAuthEnabled() {
  return import.meta.env.DEV && import.meta.env.VITE_DEV_MODE === "1";
}
