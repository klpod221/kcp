<template>
  <div class="space-y-5">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-lg bg-zinc-900/40 border border-zinc-800/80">
      <div>
        <h2 class="text-sm font-semibold text-zinc-100 flex items-center gap-2">
          <Users class="w-4 h-4 text-zinc-400" />
          User Management
        </h2>
        <p class="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
          Manage system users, administrators, and active access status for klpod221 Kontrol Panel.
        </p>
      </div>
      <Button
        variant="primary"
        @click="showCreateModal = true"
        class="shrink-0"
      >
        <template #prefix>
          <Plus class="w-3.5 h-3.5" />
        </template>
        Add User
      </Button>
    </div>

    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 overflow-hidden">
      <div class="px-4 py-3 border-b border-zinc-800/80 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-200">
            Registered Users
          </h3>
          <Badge variant="neutral" size="sm">{{ users.length }} accounts</Badge>
        </div>
        <Button
          variant="secondary"
          size="sm"
          :loading="loading"
          @click="loadUsers"
        >
          <template #prefix>
            <RefreshCw class="w-3.5 h-3.5" />
          </template>
          Refresh
        </Button>
      </div>

      <div v-if="loading && !users.length" class="p-8 text-center text-xs text-zinc-500 flex items-center justify-center gap-2">
        <Loader2 class="w-4 h-4 animate-spin text-zinc-400" />
        <span>Loading user accounts...</span>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-zinc-800/80 bg-zinc-950/50 text-[11px] font-medium uppercase tracking-wider text-zinc-500">
              <th class="py-2.5 px-4">User</th>
              <th class="py-2.5 px-4">Email</th>
              <th class="py-2.5 px-4">Role</th>
              <th class="py-2.5 px-4">Status</th>
              <th class="py-2.5 px-4">Created</th>
              <th class="py-2.5 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-800/60 text-xs">
            <tr
              v-for="u in users"
              :key="u.id"
              class="hover:bg-zinc-900/60 transition-colors"
            >
              <td class="py-3 px-4 font-medium text-zinc-100 whitespace-nowrap">
                <div class="flex items-center gap-2.5">
                  <div class="w-6 h-6 rounded bg-zinc-800 border border-zinc-700 text-zinc-200 flex items-center justify-center font-mono font-semibold text-[11px] uppercase">
                    {{ u.username[0] }}
                  </div>
                  <div>
                    <div class="flex items-center gap-1.5">
                      <span>{{ u.username }}</span>
                      <span v-if="u.id === authStore.user?.id" class="text-[10px] font-mono px-1 py-0.2 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
                        you
                      </span>
                    </div>
                    <div class="text-[10px] text-zinc-500 font-mono">ID: #{{ u.id }}</div>
                  </div>
                </div>
              </td>

              <td class="py-3 px-4 font-mono text-[11px] text-zinc-300 whitespace-nowrap">
                {{ u.email || '—' }}
              </td>

              <td class="py-3 px-4 whitespace-nowrap">
                <Badge :variant="u.is_admin ? 'success' : 'neutral'" size="sm">
                  {{ u.is_admin ? 'Administrator' : 'Standard' }}
                </Badge>
              </td>

              <td class="py-3 px-4 whitespace-nowrap">
                <Badge :variant="u.is_active ? 'success' : 'danger'" size="sm">
                  {{ u.is_active ? 'Active' : 'Disabled' }}
                </Badge>
              </td>

              <td class="py-3 px-4 font-mono text-[11px] text-zinc-400 whitespace-nowrap tabular-nums">
                {{ u.created_at ? formatDate(u.created_at) : '—' }}
              </td>

              <td class="py-3 px-4 text-right whitespace-nowrap">
                <div class="inline-flex items-center gap-1.5">
                  <Button
                    variant="secondary"
                    size="sm"
                    @click="openEditModal(u)"
                  >
                    Edit
                  </Button>
                  <Button
                    v-if="u.id !== authStore.user?.id"
                    variant="danger"
                    size="sm"
                    @click="handleDeleteUser(u)"
                  >
                    <Trash2 class="w-3.5 h-3.5" />
                  </Button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <Modal
      v-model="showCreateModal"
      title="Create New User Account"
      maxWidth="md"
    >
      <form @submit.prevent="handleCreateUser" class="space-y-3.5">
        <Input
          v-model="createForm.username"
          label="Username"
          placeholder="username"
          required
        />

        <Input
          v-model="createForm.email"
          type="email"
          label="Email (optional)"
          placeholder="user@example.com"
        />

        <Input
          v-model="createForm.password"
          type="password"
          label="Password"
          placeholder="Minimum 6 characters"
          required
        />

        <div class="flex items-center gap-2 pt-1">
          <input
            id="create_is_admin"
            v-model="createForm.is_admin"
            type="checkbox"
            class="rounded bg-zinc-950 border-zinc-800 text-zinc-100 focus:ring-0"
          />
          <label for="create_is_admin" class="text-xs text-zinc-300">Grant Administrator permissions</label>
        </div>

        <div class="pt-3 flex justify-end gap-2 border-t border-zinc-800">
          <Button variant="ghost" size="sm" @click="showCreateModal = false">Cancel</Button>
          <Button type="submit" variant="primary" size="sm" :loading="creating">Create Account</Button>
        </div>
      </form>
    </Modal>

    <Modal
      v-model="showEditModal"
      :title="`Edit User — ${selectedUser?.username || ''}`"
      maxWidth="md"
    >
      <form @submit.prevent="handleUpdateUser" class="space-y-3.5">
        <Input
          v-model="editForm.email"
          type="email"
          label="Email Address"
          placeholder="user@example.com"
        />

        <Input
          v-model="editForm.password"
          type="password"
          label="Reset Password (optional)"
          placeholder="Leave blank to keep existing password"
        />

        <div class="space-y-2 pt-1">
          <div class="flex items-center gap-2">
            <input
              id="edit_is_admin"
              v-model="editForm.is_admin"
              type="checkbox"
              class="rounded bg-zinc-950 border-zinc-800 text-zinc-100 focus:ring-0"
            />
            <label for="edit_is_admin" class="text-xs text-zinc-300">Administrator role</label>
          </div>

          <div class="flex items-center gap-2">
            <input
              id="edit_is_active"
              v-model="editForm.is_active"
              type="checkbox"
              :disabled="selectedUser?.id === authStore.user?.id"
              class="rounded bg-zinc-950 border-zinc-800 text-zinc-100 focus:ring-0"
            />
            <label for="edit_is_active" class="text-xs text-zinc-300">Active account</label>
          </div>
        </div>

        <div class="pt-3 flex justify-end gap-2 border-t border-zinc-800">
          <Button variant="ghost" size="sm" @click="showEditModal = false">Cancel</Button>
          <Button type="submit" variant="primary" size="sm" :loading="updating">Save Changes</Button>
        </div>
      </form>
    </Modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  Users,
  Plus,
  RefreshCw,
  Trash2,
  Loader2,
} from 'lucide-vue-next'
import { adminService } from '../../services/admin.service.js'
import { useAuthStore } from '../../stores/auth.store.js'
import { useToastStore } from '../../stores/toast.store.js'
import { formatDate } from '../../utils/format.js'
import Button from '../../components/ui/Button.vue'
import Badge from '../../components/ui/Badge.vue'
import Input from '../../components/ui/Input.vue'
import Modal from '../../components/ui/Modal.vue'

const authStore = useAuthStore()
const toast = useToastStore()

const users = ref([])
const loading = ref(false)
const showCreateModal = ref(false)
const showEditModal = ref(false)
const creating = ref(false)
const updating = ref(false)
const selectedUser = ref(null)

const createForm = ref({
  username: '',
  password: '',
  email: '',
  is_admin: false,
})

const editForm = ref({
  email: '',
  password: '',
  is_admin: false,
  is_active: true,
})

async function loadUsers() {
  loading.value = true
  try {
    const res = await adminService.getUsers()
    users.value = res.users || []
  } catch (err) {
    toast.error(err.message || 'Failed to load users')
  } finally {
    loading.value = false
  }
}

async function handleCreateUser() {
  creating.value = true
  try {
    await adminService.createUser(createForm.value)
    toast.success('User account created successfully')
    showCreateModal.value = false
    createForm.value = { username: '', password: '', email: '', is_admin: false }
    await loadUsers()
  } catch (err) {
    toast.error(err.message || 'Failed to create user')
  } finally {
    creating.value = false
  }
}

function openEditModal(u) {
  selectedUser.value = u
  editForm.value = {
    email: u.email || '',
    password: '',
    is_admin: u.is_admin,
    is_active: u.is_active,
  }
  showEditModal.value = true
}

async function handleUpdateUser() {
  if (!selectedUser.value) return
  updating.value = true
  try {
    const payload = {
      email: editForm.value.email,
      is_admin: editForm.value.is_admin,
      is_active: editForm.value.is_active,
    }
    if (editForm.value.password) {
      payload.password = editForm.value.password
    }
    await adminService.updateUser(selectedUser.value.id, payload)
    toast.success('User updated successfully')
    showEditModal.value = false
    await loadUsers()
  } catch (err) {
    toast.error(err.message || 'Failed to update user')
  } finally {
    updating.value = false
  }
}

async function handleDeleteUser(u) {
  if (!confirm(`Delete user account "${u.username}"?`)) return
  try {
    await adminService.deleteUser(u.id)
    toast.success(`User "${u.username}" deleted`)
    await loadUsers()
  } catch (err) {
    toast.error(err.message || 'Failed to delete user')
  }
}

onMounted(() => {
  loadUsers()
})
</script>

