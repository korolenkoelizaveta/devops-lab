import { defineStore } from "pinia"
import axios from "axios"
import Cookies from "js-cookie"

axios.defaults.withCredentials = true
axios.defaults.headers.common["X-CSRFToken"] = Cookies.get("csrftoken") || ""

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,      
    loading: false,
    error: null,    
  }),

  getters: {
    isAuthenticated: (state) => !!(state.user && state.user.is_authenticated),
    isAdmin(state) {
      const u = state.user
      if (!u) return false
      return !!(u.is_superuser || u.is_admin || u.role === "admin")
    },
  },
  

  actions: {
    async fetchProfile() {
      try {
        const r = await axios.get("/api/userprofile/info/")
        this.user = r.data
        this.error = null
      } catch (e) {
        this.user = null
      }
    },

    async login(username, password) {
      this.loading = true
      this.error = null
      this.otpGood = null

      try {
        const r = await axios.post("/api/userprofile/login/", {
          username,
          password,
        })

        if (!r.data.success) {
          this.error = r.data.error || "Ошибка авторизации"
          this.user = null
          return false
        }

        await this.fetchProfile()

        return true
      } catch (e) {
        this.error = "Ошибка авторизации"
        this.user = null
        this.otpGood = null
        return false
      } finally {
        this.loading = false
      }
    },

    async logout() {
      try {
        await axios.post("/api/userprofile/logout/")
      } catch (e) {
      }
      this.user = null
    },

  },
})
