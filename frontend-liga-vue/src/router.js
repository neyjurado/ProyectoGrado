import { createRouter, createWebHistory } from 'vue-router'
import Inicio from './views/Inicio.vue'
import Login from './views/Login.vue'
import AdminDashboard from './views/AdminDashboard.vue'
import JugadorDashboard from './views/JugadorDashboard.vue'

const routes = [
  { path: '/', component: Inicio },
  { path: '/login', component: Login },
  { path: '/admin', component: AdminDashboard },
  { path: '/jugador', component: JugadorDashboard }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router