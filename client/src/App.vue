<script setup>
import { computed, onBeforeMount } from "vue"
import { useRoute, useRouter, RouterView, RouterLink } from "vue-router"
import { useAuthStore } from "@/stores/auth"

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const showLayout = computed(() => route.name !== "LoginView")

const userLabel = computed(() => {
  const u = auth.user
  if (!u || !auth.isAuthenticated) return ""

  let roleText = ""
  if (u.is_admin || u.is_superuser) roleText = "админ"
  else if (u.role === "trainer") roleText = "тренер"
  else if (u.role === "client") roleText = "клиент"

  return roleText ? `${u.username} (${roleText})` : u.username
})

async function onLogout() {
  await auth.logout()
  router.push({ name: "LoginView" })
}

onBeforeMount(async () => {
  if (auth.user === null) {
    await auth.fetchProfile()
  }
})
</script>

<template>
  <RouterView v-if="!showLayout" />

  <div v-else>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container-fluid">
        <RouterLink class="navbar-brand" to="/users">
          Gym
        </RouterLink>

        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#mainNavbar"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="mainNavbar">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <RouterLink
                to="/users"
                class="nav-link"
                :class="{ active: route.name === 'UsersView' }"
              >
                Пользователи
              </RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink
                to="/memberships"
                class="nav-link"
                :class="{ active: route.name === 'MembershipsView' }"
              >
                Абонементы
              </RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink
                to="/membershiptypes"
                class="nav-link"
                :class="{ active: route.name === 'MembershipTypesView' }"
              >
                Типы абонементов
              </RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink
                to="/workoutsessions"
                class="nav-link"
                :class="{ active: route.name === 'WorkoutSessionsView' }"
              >
                Тренировки
              </RouterLink>
            </li>
          </ul>
          <div class="d-flex align-items-center">
          <RouterLink
            v-if="!auth.isAuthenticated"
            :to="{ name: 'LoginView' }"
            class="btn btn-outline-light btn-sm"
            title="Войти"
            aria-label="Войти"
          >
            <i class="bi bi-person-circle fs-5"></i>
          </RouterLink>

            <span
              v-if="auth.isAuthenticated && userLabel"
              class="text-light me-3"
            >
              {{ userLabel }}
            </span>
            <button
              v-if="auth.isAuthenticated"
              class="btn btn-outline-light btn-sm"
              @click="onLogout"
            >
              Выйти
            </button>
          </div>
        </div>
      </div>
    </nav>

    <main class="container-fluid py-3">
      <RouterView />
    </main>
  </div>
</template>