<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import axios from "axios"
import Cookies from "js-cookie"

const auth = useAuthStore()
const router = useRouter()

const username = ref("")
const password = ref("")
const error = ref("")

axios.defaults.headers.common["X-CSRFToken"] = Cookies.get("csrftoken") || ""

async function onSubmit() {
  const result = await auth.login(username.value, password.value)

  if (result === false) {
    error.value = "Неверный логин или пароль"
    return
  }

  router.push("/users")
}
</script>

<template>
  <div
    class="container d-flex justify-content-center align-items-center"
    style="min-height: 100vh"
  >
    <div class="card p-4" style="min-width: 320px; max-width: 400px; width: 100%;">
      <h3 class="mb-3 text-center">Вход</h3>

      <div v-if="auth.loading" class="alert alert-secondary py-2">
        Загрузка...
      </div>
      <div v-if="localError" class="alert alert-danger py-2">
        {{ localError }}
      </div>

      <form @submit.prevent="onSubmit">
        <div class="form-floating mb-3">
          <input
            type="text"
            class="form-control"
            id="login-username"
            v-model="username"
            required
          >
          <label for="login-username">Логин</label>
        </div>

        <div class="form-floating mb-3">
          <input
            type="password"
            class="form-control"
            id="login-password"
            v-model="password"
            required
          >
          <label for="login-password">Пароль</label>
        </div>

        <button type="submit" class="btn btn-primary w-100" :disabled="auth.loading">
          Войти
        </button>
      </form>
    </div>
  </div>
</template>