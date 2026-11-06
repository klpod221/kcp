<template>
  <div class="space-y-6 max-w-4xl">
    <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 p-5">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-md bg-zinc-800 border border-zinc-700 text-zinc-100 flex items-center justify-center font-mono font-bold text-sm uppercase">
          {{ (authStore.username || 'K')[0] }}
        </div>
        <div>
          <h2 class="text-sm font-semibold text-zinc-100 flex items-center gap-2">
            <span>{{ authStore.username }}</span>
            <Badge :variant="authStore.isAdmin ? 'success' : 'neutral'" size="sm">
              {{ authStore.isAdmin ? 'Administrator' : 'Standard User' }}
            </Badge>
          </h2>
          <div class="text-[11px] text-zinc-500 font-mono mt-0.5">
            User ID: #{{ authStore.user?.id || '—' }} · Created: {{ authStore.user?.created_at ? formatDate(authStore.user.created_at) : '—' }}
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 p-5 space-y-4">
        <div class="border-b border-zinc-800/80 pb-3">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-200">
            Account Details
          </h3>
          <p class="text-[11px] text-zinc-400 mt-0.5">Update your contact email address</p>
        </div>

        <form @submit.prevent="handleUpdateEmail" class="space-y-3.5">
          <Input
            v-model="profileForm.email"
            type="email"
            label="Email Address"
            placeholder="admin@example.com"
          />

          <div class="pt-2 flex justify-end">
            <Button
              type="submit"
              variant="primary"
              size="sm"
              :loading="savingEmail"
            >
              Save Email
            </Button>
          </div>
        </form>
      </div>

      <div class="rounded-lg bg-zinc-900/40 border border-zinc-800/80 p-5 space-y-4">
        <div class="border-b border-zinc-800/80 pb-3">
          <h3 class="text-xs font-semibold uppercase tracking-wider text-zinc-200">
            Change Password
          </h3>
          <p class="text-[11px] text-zinc-400 mt-0.5">Ensure your account uses a secure password</p>
        </div>

        <form @submit.prevent="handleChangePassword" class="space-y-3.5">
          <Input
            v-model="passwordForm.current_password"
            type="password"
            label="Current Password"
            placeholder="••••••••••••"
            required
          />

          <Input
            v-model="passwordForm.new_password"
            type="password"
            label="New Password"
            placeholder="Minimum 6 characters"
            required
          />

          <Input
            v-model="passwordForm.confirm_password"
            type="password"
            label="Confirm New Password"
            placeholder="Re-enter new password"
            required
          />

          <div class="pt-2 flex justify-end">
            <Button
              type="submit"
              variant="primary"
              size="sm"
              :loading="savingPassword"
            >
              Update Password
            </Button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth.store.js'
import { adminService } from '../../services/admin.service.js'
import { useToastStore } from '../../stores/toast.store.js'
import { formatDate } from '../../utils/format.js'
import Button from '../../components/ui/Button.vue'
import Input from '../../components/ui/Input.vue'
import Badge from '../../components/ui/Badge.vue'

const authStore = useAuthStore()
const toast = useToastStore()

const profileForm = ref({
  email: '',
})

const passwordForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

const savingEmail = ref(false)
const savingPassword = ref(false)

onMounted(() => {
  if (authStore.user) {
    profileForm.value.email = authStore.user.email || ''
  }
})

async function handleUpdateEmail() {
  savingEmail.value = true
  try {
    const res = await adminService.updateProfile({ email: profileForm.value.email })
    authStore.user = { ...authStore.user, ...res.user }
    toast.success('Profile email updated successfully')
  } catch (err) {
    toast.error(err.message || 'Failed to update email')
  } finally {
    savingEmail.value = false
  }
}

async function handleChangePassword() {
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    toast.error('New passwords do not match')
    return
  }
  if (passwordForm.value.new_password.length < 6) {
    toast.error('New password must be at least 6 characters')
    return
  }

  savingPassword.value = true
  try {
    await adminService.updateProfile({
      current_password: passwordForm.value.current_password,
      new_password: passwordForm.value.new_password,
    })
    toast.success('Password changed successfully')
    passwordForm.value = {
      current_password: '',
      new_password: '',
      confirm_password: '',
    }
  } catch (err) {
    toast.error(err.message || 'Failed to change password')
  } finally {
    savingPassword.value = false
  }
}
</script>

