<script setup lang="ts">
import { computed, ref } from "vue";
import { z } from "zod";
import { useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";
import { useUiStore } from "../stores/ui";

const auth = useAuthStore();
const ui = useUiStore();
const router = useRouter();

const activeTab = ref<"login" | "register">("login");
const email = ref("");
const nickname = ref("");
const password = ref("");
const confirmPassword = ref("");
const error = ref("");

const loginSchema = z.object({
  email: z.string().email("邮箱格式不正确"),
  password: z.string().min(8, "密码至少 8 位"),
});

const registerSchema = z
  .object({
    email: z.string().email("邮箱格式不正确"),
    nickname: z.string().min(1, "昵称不能为空").max(64, "昵称最多 64 字"),
    password: z.string().min(8, "密码至少 8 位"),
    confirmPassword: z.string().min(8, "确认密码至少 8 位"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "两次输入密码不一致",
    path: ["confirmPassword"],
  });

const submitText = computed(() => (activeTab.value === "login" ? "登入牌局" : "创建雀士账号"));

async function submit(): Promise<void> {
  error.value = "";

  try {
    if (activeTab.value === "login") {
      loginSchema.parse({ email: email.value, password: password.value });
      await auth.doLogin({ email: email.value, password: password.value });
      ui.push("欢迎归来，牌桌已就绪", "success");
    } else {
      registerSchema.parse({
        email: email.value,
        nickname: nickname.value,
        password: password.value,
        confirmPassword: confirmPassword.value,
      });
      await auth.doRegister({
        email: email.value,
        nickname: nickname.value,
        password: password.value,
      });
      ui.push("注册成功，欢迎新雀士", "success");
    }

    await router.push({ name: "lobby" });
  } catch (e) {
    error.value = e instanceof Error ? e.message : "提交失败";
    ui.push(error.value, "error");
  }
}
</script>

<template>
  <section class="relative min-h-[calc(100vh-130px)] flex flex-col lg:flex-row items-center justify-center lg:justify-between px-4 lg:px-16 overflow-hidden">
    <!-- Dynamic imposing background elements -->
    <div class="pointer-events-none absolute inset-0 -z-10 mix-blend-overlay">
      <div class="absolute -left-[10%] -top-[10%] h-[60vh] w-[60vh] animate-pulse rounded-full bg-cinnabar-600/20 blur-[120px]"></div>
      <div class="absolute -bottom-[10%] -right-[10%] h-[70vh] w-[70vh] animate-pulse rounded-full bg-brass-500/20 blur-[130px]" style="animation-delay: 2s"></div>
    </div>

    <!-- Imposing Titles (Unboxed) -->
    <aside class="relative z-10 flex flex-col items-center lg:items-start text-center lg:text-left mb-12 lg:mb-0">
      <h1 class="font-brush text-[clamp(4rem,15vw,8rem)] leading-none tracking-[0.15em] text-transparent bg-clip-text bg-gradient-to-br from-brass-400 via-rice-100 to-brass-600 drop-shadow-[0_10px_20px_rgba(0,0,0,0.5)]">
        MajSpirit
      </h1>
      <p class="mt-4 text-xl tracking-[0.5em] text-rice-50/90 drop-shadow-md">雀灵麻将</p>
      <div class="mt-10 h-px w-32 bg-gradient-to-r from-transparent via-brass-500/50 to-transparent lg:mx-0 mx-auto"></div>
      <p class="mt-8 max-w-md text-base leading-8 text-rice-100/80">
        风骨入局，牌势如文。<br />沉浸式中式麻将对战体验，从此刻落座开始。
      </p>
    </aside>

    <!-- Form Section -->
    <form class="relative z-10 w-full max-w-md paper-card lg:mr-10 xl:mr-20" @submit.prevent="submit">
      <div class="grid grid-cols-2 gap-2 rounded-2xl border border-jade-600/20 bg-rice-100/70 p-1 mb-4">
        <button
          type="button"
          class="rounded-xl px-4 py-2 text-sm font-semibold transition"
          :class="activeTab === 'login'
            ? 'bg-gradient-to-br from-jade-500 to-jade-600 text-rice-50 shadow-md'
            : 'text-ink-700 hover:bg-rice-50/80'"
          @click="activeTab = 'login'"
        >
          登录
        </button>
        <button
          type="button"
          class="rounded-xl px-4 py-2 text-sm font-semibold transition"
          :class="activeTab === 'register'
            ? 'bg-gradient-to-br from-jade-500 to-jade-600 text-rice-50 shadow-md'
            : 'text-ink-700 hover:bg-rice-50/80'"
          @click="activeTab = 'register'"
        >
          注册
        </button>
      </div>

      <div class="grid gap-4">
        <label class="grid gap-1 text-sm text-ink-700">
          <span>邮箱</span>
          <input v-model.trim="email" class="ink-input" type="email" autocomplete="email" placeholder="you@example.com" />
        </label>

        <label v-if="activeTab === 'register'" class="grid gap-1 text-sm text-ink-700">
          <span>昵称</span>
          <input v-model.trim="nickname" class="ink-input" type="text" autocomplete="nickname" placeholder="你的雀士名" />
        </label>

        <label class="grid gap-1 text-sm text-ink-700">
          <span>密码</span>
          <input v-model="password" class="ink-input" type="password" autocomplete="current-password" placeholder="至少 8 位" />
        </label>

        <label v-if="activeTab === 'register'" class="grid gap-1 text-sm text-ink-700">
          <span>确认密码</span>
          <input
            v-model="confirmPassword"
            class="ink-input"
            type="password"
            autocomplete="new-password"
            placeholder="再次输入密码"
          />
        </label>

        <p v-if="error" class="m-0 text-sm text-cinnabar-600">{{ error }}</p>

        <button class="ink-btn-primary mt-2" type="submit" :disabled="auth.loading">
          {{ auth.loading ? '提交中...' : submitText }}
        </button>
      </div>
    </form>
  </section>
</template>
