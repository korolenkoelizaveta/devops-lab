<script setup>
import axios from "axios"
import { ref, onBeforeMount, computed } from "vue"
import Cookies from "js-cookie"
import _ from "lodash"
import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()

const memberships = ref([])
const clients = ref([])
const membershipTypes = ref([])
const loading = ref(false)
const stats = ref(null)

const profile = computed(() => auth.user)

const canManageMemberships = computed(() => {
  const p = profile.value
  if (!p) return false
  return Boolean(p.is_superuser ||  p.is_admin || p.role === "admin")
})

const isTrainerProfile = computed(() => profile.value?.role === "trainer")
const isClientProfile = computed(() => profile.value?.role === "client")

const membershipToAdd = ref({ client: null, membership_type: null, is_active: true })
const membershipToEdit = ref({})

const clientsById = computed(() => _.keyBy(clients.value, x => x.id))
const membershipTypeById = computed(() => _.keyBy(membershipTypes.value, x => x.id))

const clientNameFilter = ref("")
const membershipTypeFilter = ref("")  
const isActiveFilter = ref("")       

const membershipTypeOptions = computed(() => membershipTypes.value)

const filteredMemberships = computed(() => {
  let res = memberships.value.slice()

  if (clientNameFilter.value.trim()) {
    const needle = clientNameFilter.value.toLowerCase()
    res = res.filter(m => {
      const client = clientsById.value[m.client]
      return client && (client.name || "").toLowerCase().includes(needle)
    })
  }

  if (membershipTypeFilter.value) {
    res = res.filter(m => String(m.membership_type) === String(membershipTypeFilter.value))
  }

  if (isActiveFilter.value === "true") {
    res = res.filter(m => m.is_active === true)
  } else if (isActiveFilter.value === "false") {
    res = res.filter(m => m.is_active === false)
  }

  return res
})

async function fetchMemberships() {
  loading.value = true

  const [listRes, statsRes] = await Promise.all([
    axios.get("/api/membership/"),
    axios.get("/api/membership/stats/"),
  ])

  memberships.value = listRes.data
  stats.value = statsRes.data

  loading.value = false
}

async function fetchClients() {
  const r = await axios.get("/api/users/?role=client")
  clients.value = r.data
}

async function fetchMembershipTypes() {
  const r = await axios.get("/api/membershiptype/")
  membershipTypes.value = r.data
}

async function onMembershipAdd() {
  if (!canManageMemberships.value) return

  await axios.post("/api/membership/", { ...membershipToAdd.value })
  membershipToAdd.value = { client: null, membership_type: null, is_active: true }
  await fetchMemberships()
}

async function onRemoveClick(membership) {
  if (!canManageMemberships.value) return

  await axios.delete(`/api/membership/${membership.id}/`)
  await fetchMemberships()
}

function onMembershipEditClick(membership) {
  if (!canManageMemberships.value) return
  membershipToEdit.value = { ...membership }
}

async function onUpdateMembership() {
  if (!canManageMemberships.value) return

  await axios.patch(`/api/membership/${membershipToEdit.value.id}/`, {
    client: membershipToEdit.value.client,
    membership_type: membershipToEdit.value.membership_type,
    is_active: membershipToEdit.value.is_active,
  })
  await fetchMemberships()
}

onBeforeMount(async () => {
  axios.defaults.headers.common["X-CSRFToken"] = Cookies.get("csrftoken")

  if (!auth.user) {
    await auth.fetchProfile()
  }

  await Promise.all([fetchMemberships(), fetchClients(), fetchMembershipTypes()])
})
</script>

<template>
  <div
    class="modal fade"
    id="editMembershipModal"
    tabindex="-1"
    v-if="canManageMemberships"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">Редактировать абонемент</h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>

        <div class="modal-body">
          <div class="row g-2">
            <div class="col">
              <div class="form-floating">
                <select class="form-select" v-model="membershipToEdit.client">
                  <option
                    :value="client.id"
                    v-for="client in clients"
                    :key="`edit-c-${client.id}`"
                  >
                    {{ client.name }}
                  </option>
                </select>
                <label>Клиент</label>
              </div>
            </div>

            <div class="col">
              <div class="form-floating">
                <select
                  class="form-select"
                  v-model="membershipToEdit.membership_type"
                >
                  <option
                    :value="type.id"
                    v-for="type in membershipTypes"
                    :key="`edit-t-${type.id}`"
                  >
                    {{ type.type }}
                  </option>
                </select>
                <label>Тип абонемента</label>
              </div>
            </div>

            <div class="col-auto d-flex align-items-center">
              <div class="form-check form-switch">
                <input
                  class="form-check-input"
                  type="checkbox"
                  v-model="membershipToEdit.is_active"
                >
                <label class="form-check-label ms-2">Активен</label>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button
            type="button"
            class="btn btn-secondary"
            data-bs-dismiss="modal"
          >
            Закрыть
          </button>
          <button
            data-bs-dismiss="modal"
            type="button"
            class="btn btn-primary"
            @click="onUpdateMembership"
          >
            Сохранить
          </button>
        </div>
      </div>
    </div>
  </div>

  <div class="container-fluid" v-if="canManageMemberships">
    <div >
      <div class="row g-2">
        <div class="col">
          <div class="form-floating">
            <select
              class="form-select"
              v-model="membershipToAdd.client"
              required
            >
              <option
                :value="client.id"
                v-for="client in clients"
                :key="`add-c-${client.id}`"
              >
                {{ client.name }}
              </option>
            </select>
            <label>Клиент</label>
          </div>
        </div>

        <div class="col-auto">
          <div class="form-floating">
            <select
              class="form-select"
              v-model="membershipToAdd.membership_type"
              required
            >
              <option
                :value="type.id"
                v-for="type in membershipTypes"
                :key="`add-t-${type.id}`"
              >
                {{ type.type }}
              </option>
            </select>
            <label>Тип абонемента</label>
          </div>
        </div>

        <div class="col">
          <div class="form-check form-switch h-100 d-flex align-items-center">
            <input
              class="form-check-input"
              type="checkbox"
              v-model="membershipToAdd.is_active"
            >
            <label class="form-check-label ms-2">Активен</label>
          </div>
        </div>

        <div class="col-auto">
          <button class="btn btn-primary" @click="onMembershipAdd">
            Добавить
          </button>
        </div>
      </div>
    </div>
  </div>

  <div
    class="container-fluid mt-2"
    v-if="canManageMemberships && stats"
  >
    <div class="alert alert-info py-2 mb-2">
      <strong>Статистика абонементов:</strong>
      <span class="ms-2">
        всего: {{ stats.count }},
        активных: {{ stats.active }},
        неактивных: {{ stats.inactive }}
      </span>
    </div>
  </div>

  <div
    class="container-fluid mb-2"
    v-if="!isClientProfile"
  >
    <div class="row g-2">
      <div class="col-auto">
        <input
          type="text"
          class="form-control"
          v-model="clientNameFilter"
          placeholder="Фильтр по ФИО клиента"
        >
      </div>

      <div class="col-auto">
        <select
          class="form-select"
          v-model="membershipTypeFilter"
        >
          <option value="">Все типы</option>
          <option
            v-for="type in membershipTypeOptions"
            :key="type.id"
            :value="type.id"
          >
            {{ type.type }}
          </option>
        </select>
      </div>

      <div class="col-auto">
        <select
          class="form-select"
          v-model="isActiveFilter"
        >
          <option value="">Все абонементы</option>
          <option value="true">Только активные</option>
          <option value="false">Только неактивные</option>
        </select>
      </div>
    </div>
  </div>

  <div v-if="loading" class="p-3 text-center">Загрузка…</div>
  <div v-else>
    <div
      v-for="item in filteredMemberships"
      :key="item.id"
      class="membership-item"
    >
      <div>{{ clientsById[item.client]?.name }}</div>
      <div>{{ membershipTypeById[item.membership_type]?.type }}</div>
      <div>{{ item.is_active ? "Активен" : "Не активен" }}</div>

      <button
        v-if="canManageMemberships"
        class="btn btn-success"
        @click="onMembershipEditClick(item)"
        data-bs-toggle="modal"
        data-bs-target="#editMembershipModal"
      >
        <i class="bi bi-pen-fill"></i>
      </button>
      <button
        v-if="canManageMemberships"
        class="btn btn-danger"
        @click="onRemoveClick(item)"
      >
        <i class="bi bi-x"></i>
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.membership-item {
  padding: 0.5rem;
  margin: 0.5rem;
  border: 1px solid silver;
  border-radius: 8px;
  display: grid;
  align-items: center;
  grid-template-columns: 1fr 1fr auto auto auto;
  gap: 16px;
}
</style>