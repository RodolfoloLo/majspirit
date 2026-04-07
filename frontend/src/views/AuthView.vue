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
  <section class="auth-page">
    <aside class="auth-aside">
      <h1>国风雀局 · 智斗四方</h1>
      <p>欢迎来到 MajSpirit。这里有牌局、对战记录与实时互动，专为你的实习展示打造。</p>
      <ul>
        <li>安全鉴权：Bearer Token</li>
        <li>实时同步：WebSocket 心跳与事件</li>
        <li>生产风格：请求追踪 ID 与错误治理</li>
      </ul>
    </aside>

    <form class="auth-card" @submit.prevent="submit">
      <div class="tab-row">
        <button
          type="button"
          :class="{ active: activeTab === 'login' }"
          @click="activeTab = 'login'"
        >
          登录
        </button>
        <button
          type="button"
          :class="{ active: activeTab === 'register' }"
          @click="activeTab = 'register'"
        >
          注册
        </button>
      </div>

      <label>
        邮箱
        <input v-model.trim="email" type="email" autocomplete="email" placeholder="you@example.com" />
      </label>

      <label v-if="activeTab === 'register'">
        昵称
        <input v-model.trim="nickname" type="text" autocomplete="nickname" placeholder="你的雀士名" />
      </label>

      <label>
        密码
        <input v-model="password" type="password" autocomplete="current-password" placeholder="至少 8 位" />
      </label>

      <label v-if="activeTab === 'register'">
        确认密码
        <input
          v-model="confirmPassword"
          type="password"
          autocomplete="new-password"
          placeholder="再次输入密码"
        />
      </label>

      <p v-if="error" class="inline-error">{{ error }}</p>

      <button class="primary" type="submit" :disabled="auth.loading">
        {{ auth.loading ? '提交中...' : submitText }}
      </button>
    </form>
  </section>
</template>
