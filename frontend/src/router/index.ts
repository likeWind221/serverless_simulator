import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/dashboard.vue'
import ResultView from '../views/result.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView
    },
    {
      path: '/result',
      name: 'result',
      component: ResultView
    }
  ]
})

export default router
