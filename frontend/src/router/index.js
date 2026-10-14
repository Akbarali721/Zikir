import { createRouter, createWebHistory } from "vue-router";

import { useUserStore } from "@/stores/user";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "entry",
      component: () => import("@/views/EntryView.vue"),
      meta: { skipGuard: true },
    },
    {
      path: "/welcome",
      name: "welcome",
      component: () => import("@/views/WelcomeView.vue"),
    },
    {
      path: "/profile",
      redirect: { name: "tasbeh" },
    },
    {
      path: "/tasbeh",
      name: "tasbeh",
      component: () => import("@/views/TasbehView.vue"),
    },
    {
      path: "/admin",
      name: "admin",
      component: () => import("@/views/AdminView.vue"),
      meta: { requiresAdmin: true },
    },
    {
      path: "/admin/forbidden",
      name: "admin-forbidden",
      component: () => import("@/views/AdminForbiddenView.vue"),
      meta: { adminForbiddenPage: true },
    },
  ],
});

router.beforeEach(async (to) => {
  if (to.meta.skipGuard) {
    return true;
  }

  const userStore = useUserStore();

  if (!userStore.bootstrapped) {
    await userStore.bootstrap();
  }

  if (to.meta.adminForbiddenPage) {
    return true;
  }

  if (to.meta.requiresAdmin) {
    if (!userStore.me) {
      return { name: "entry" };
    }
    if (!userStore.isAdmin) {
      return { name: "admin-forbidden" };
    }
    return true;
  }

  if (userStore.me) {
    if (to.name === "welcome") {
      return { name: "tasbeh" };
    }
    return true;
  }

  if (to.name === "tasbeh" || to.name === "welcome") {
    return { name: "entry" };
  }

  return true;
});

export default router;
