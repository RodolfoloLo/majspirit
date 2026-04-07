import { defineStore } from "pinia";

export type NoticeLevel = "success" | "info" | "warning" | "error";

export interface Notice {
  id: string;
  level: NoticeLevel;
  text: string;
}

export const useUiStore = defineStore("ui", {
  state: () => ({
    notices: [] as Notice[],
  }),
  actions: {
    push(text: string, level: NoticeLevel = "info") {
      const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
      this.notices.push({ id, level, text });
      window.setTimeout(() => this.remove(id), 3200);
    },
    remove(id: string) {
      this.notices = this.notices.filter((n) => n.id !== id);
    },
  },
});
