import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import router from "./router";
import { ensureClientConfig } from "./services/clientConfig";
import { initTelegramWebApp } from "./services/telegram";

import "./assets/main.css";

async function bootstrap() {
  initTelegramWebApp();
  await ensureClientConfig();

  const app = createApp(App);
  app.use(createPinia());
  app.use(router);
  app.mount("#app");
}

bootstrap();
