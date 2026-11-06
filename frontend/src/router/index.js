import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.store.js'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: () => import('../views/dashboard/DashboardView.vue'),
    meta: { requiresAuth: true, title: 'Server Overview & Homelab Stack' },
  },
  {
    path: '/docker',
    name: 'docker',
    component: () => import('../views/docker/DockerView.vue'),
    meta: { requiresAuth: true, title: 'Docker Containers & Live Logs' },
  },
  {
    path: '/transfers',
    name: 'transfers',
    component: () => import('../views/transfers/TransfersView.vue'),
    meta: { requiresAuth: true, title: 'Live Transfers & I/O Monitor' },
  },
  {
    path: '/services',
    name: 'services',
    component: () => import('../views/services/ServicesView.vue'),
    meta: { requiresAuth: true, title: 'Homelab Services Control Center' },
  },
  {
    path: '/chat',
    name: 'chat',
    component: () => import('../views/chat/ChatView.vue'),
    meta: { requiresAuth: true, title: 'AI Workspace — Server Assistant' },
  },
  {
    path: '/tools',
    name: 'tools',
    component: () => import('../views/tools/ToolsView.vue'),
    meta: { requiresAuth: true, title: 'MCP Server — Tools Catalog & Playground' },
  },
  {
    path: '/tokens',
    name: 'tokens',
    component: () => import('../views/tokens/TokensView.vue'),
    meta: { requiresAuth: true, title: 'MCP Server — Personal Access Tokens (PAT)' },
  },
  {
    path: '/clients',
    name: 'clients',
    component: () => import('../views/clients/ClientsView.vue'),
    meta: { requiresAuth: true, title: 'MCP Server — OAuth 2.0 Clients & Sessions' },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/auth/LoginView.vue'),
    meta: { requiresAuth: false, isAuth: true, title: 'Sign In — klpod221 Kontrol Panel' },
  },
  {
    path: '/consent',
    name: 'consent',
    component: () => import('../views/auth/ConsentView.vue'),
    meta: { requiresAuth: true, isAuth: true, title: 'Authorize Application — klpod221 Kontrol Panel' },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('../views/profile/ProfileView.vue'),
    meta: { requiresAuth: true, title: 'Account Profile & Security' },
  },
  {
    path: '/users',
    name: 'users',
    component: () => import('../views/users/UsersView.vue'),
    meta: { requiresAuth: true, title: 'User Management' },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  if (!authStore.isLoaded) {
    await authStore.checkAuth()
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({
      name: 'login',
      query: { return_to: to.fullPath },
    })
    return
  }

  if (to.name === 'login' && authStore.isAuthenticated && !to.query.return_to) {
    next({ name: 'dashboard' })
    return
  }

  next()
})
