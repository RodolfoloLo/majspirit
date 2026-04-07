import { createRouter, createWebHistory } from "vue-router";

import { getStoredToken } from "../lib/token";
import AuthView from "../views/AuthView.vue";
import GameView from "../views/GameView.vue";
import HistoryView from "../views/HistoryView.vue";
import LobbyView from "../views/LobbyView.vue";
import NotFoundView from "../views/NotFoundView.vue";
import RoomView from "../views/RoomView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/lobby" },
    { path: "/auth", name: "auth", component: AuthView, meta: { guestOnly: true } },
    { path: "/lobby", name: "lobby", component: LobbyView, meta: { requiresAuth: true } },
    { path: "/room/:id", name: "room", component: RoomView, meta: { requiresAuth: true } },
    { path: "/history", name: "history", component: HistoryView, meta: { requiresAuth: true } },
    { path: "/game/:id", name: "game", component: GameView, meta: { requiresAuth: true } },
    { path: "/:pathMatch(.*)*", name: "not-found", component: NotFoundView },
  ],
});

router.beforeEach((to) => {
  const token = getStoredToken();
  const loggedIn = Boolean(token);

  if (to.meta.requiresAuth && !loggedIn) {
    return { name: "auth" };
  }

  if (to.meta.guestOnly && loggedIn) {
    return { name: "lobby" };
  }

  return true;
});

export default router;
