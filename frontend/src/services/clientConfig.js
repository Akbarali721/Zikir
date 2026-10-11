/** Backend DEBUG + DEV_TELEGRAM_ID holatini xavfsiz tekshiradi (sirlar chiqmaydi). */

let configPromise = null;
let config = { allow_dev_auth: false };

export async function ensureClientConfig() {
  if (configPromise) return configPromise;
  configPromise = (async () => {
    try {
      const res = await fetch("/api/config/client", { credentials: "same-origin" });
      if (res.ok) {
        config = await res.json();
      }
    } catch {
      config = { allow_dev_auth: false };
    }
    return config;
  })();
  return configPromise;
}

export function getClientConfig() {
  return config;
}

/** initData yo‘q bo‘lganda X-Dev-Mode yuborish kerakmi */
export function allowDevAuth() {
  if (getTelegramInitData()) return false;
  if (config.allow_dev_auth) return true;
  return import.meta.env.DEV && import.meta.env.VITE_DEV_MODE === "1";
}

function getTelegramInitData() {
  const tg = typeof window !== "undefined" ? window.Telegram?.WebApp : null;
  return tg?.initData?.trim() || "";
}
