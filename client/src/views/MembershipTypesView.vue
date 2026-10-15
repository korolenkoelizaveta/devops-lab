<script setup>
import axios from "axios"
import { ref, onBeforeMount, computed } from "vue"
import Cookies from "js-cookie"
import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()

const membershipTypes = ref([])
const loading = ref(false)

const membershipTypeToAdd = ref({ type: "", description: "" })
const membershipTypeToEdit = ref({})

const profile = computed(() => auth.user)

const canManageMembershipTypes = computed(() => {
  const p = profile.value
  if (!p) return false
  return Boolean(p.is_superuser || p.is_admin || p.role === "admin")
})

async function fetchMembershipTypes() {
  loading.value = true

  try {
    const response = await axios.get("/api/membershiptype/")
    membershipTypes.value = response.data
  } finally {
    loading.value = false
  }
}

async function onMembershipTypeAdd() {
  if (!canManageMembershipTypes.value) return

  await axios.post("/api/membershiptype/", {
    ...membershipTypeToAdd.value,
  })
  membershipTypeToAdd.value = { type: "", description: "" }
  await fetchMembershipTypes()
}

async function onRemoveClick(membershiptype) {
  if (!canManageMembershipTypes.value) return

  await axios.delete(`/api/membershiptype/${membershiptype.id}/`)
  await fetchMembershipTypes()
}

function onMembershipTypeEditClick(membershiptype) {
  if (!canManageMembershipTypes.value) return

  membershipTypeToEdit.value = { ...membershiptype }
}

async function onUpdateMembershipType() {
  if (!canManageMembershipTypes.value) return

  await axios.put(`/api/membershiptype/${membershipTypeToEdit.value.id}/`, {
    ...membershipTypeToEdit.value,
  })
  await fetchMembershipTypes()
}

onBeforeMount(async () => {
  axios.defaults.headers.common["X-CSRFToken"] = Cookies.get("csrftoken")

  if (!auth.user) {
    await auth.fetchProfile()
  }

  await fetchMembershipTypes()
})
</script>

<template>
  <div class="modal fade" id="editMembershipTypeModal" tabindex="-1" v-if="canManageMembershipTypes">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">Редактировать тип абонемента</h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="row g-2">
            <div class="col">
              <div class="form-floating">
                <input type="text" class="form-control" v-model="membershipTypeToEdit.type">
                <label>Тип абонемента</label>
              </div>
            </div>
            <div class="col">
              <div class="form-floating">
                <input type="text" class="form-control" v-model="membershipTypeToEdit.description">
                <label>Описание</label>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
          <button data-bs-dismiss="modal" type="button" class="btn btn-primary" @click="onUpdateMembershipType">Сохранить</button>
        </div>
      </div>
    </div>
  </div>

  <div class="container-fluid">
    <div style="padding-bottom: 10px;" v-if="canManageMembershipTypes">
      <div class="row g-2">
        <div class="col">
          <div class="form-floating">
            <input type="text" class="form-control" v-model="membershipTypeToAdd.type" required>
            <label>Тип абонемента</label>
          </div>
        </div>
        <div class="col">
          <div class="form-floating">
            <input type="text" class="form-control" v-model="membershipTypeToAdd.description" required>
            <label>Описание</label>
          </div>
        </div>
        <div class="col-auto d-flex align-items-center">
          <button class="btn btn-primary mt-2 mt-md-0" @click="onMembershipTypeAdd">
            Добавить
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="p-3 text-center">Загрузка…</div>
    <div v-else>
      <div v-for="item in membershipTypes" :key="item.id" class="membershipType-item">
        <div>{{ item.type }}</div>
        <div>{{ item.description }}</div>

        <button v-if="canManageMembershipTypes" class="btn btn-success" @click="onMembershipTypeEditClick(item)" data-bs-toggle="modal" data-bs-target="#editMembershipTypeModal">
          <i class="bi bi-pen-fill"></i>
        </button>
        <button v-if="canManageMembershipTypes" class="btn btn-danger" @click="onRemoveClick(item)">
          <i class="bi bi-x"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.membershipType-item {
  padding: 0.5rem;
  margin: 0.5rem;
  border: 1px solid silver;
  border-radius: 8px;
  display: grid;
  align-items: center;
  grid-template-columns: 1fr 1fr auto auto;
  gap: 16px;
  margin-left: 0;
  margin-right: 0;
}
</style>