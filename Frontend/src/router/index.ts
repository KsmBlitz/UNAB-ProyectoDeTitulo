// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '@/auth/store'; // <-- 1. Importar el store

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/LoginView.vue')
    },
    {
      path: '/forgot-password',
      name: 'ForgotPassword',
      component: () => import('../views/ForgotPasswordView.vue')
    },
    {
      path: '/reset-password',
      name: 'ResetPassword',
      component: () => import('../views/ResetPasswordView.vue')
    },
    {
      path: '/',
      component: () => import('../views/DashboardLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'DashboardHome',
          component: () => import('../views/DashboardHomeView.vue')
        },
        {
          path: 'users',
          name: 'UserManagement',
          component: () => import('../views/UserManagementView.vue'),
          // 2. Añadimos el rol requerido a la metadata de la ruta
          meta: { requiresAuth: true, requiresRole: 'admin' }
        },
        {
          path: 'alerts',
          name: 'AlertsManagement',
          component: () => import('../views/AlertsManagementView.vue'),
          meta: { requiresAuth: true }
        },
        {
          path: 'audit',
          name: 'AuditLog',
          component: () => import('../views/AuditLogView.vue'),
          meta: { requiresAuth: true, requiresRole: 'admin' }
        },
        {
          path: 'analytics',
          name: 'Analytics',
          component: () => import('../views/AnalyticsView.vue'),
          meta: { requiresAuth: true }
        }
      ]
    },
    { path: '/:catchAll(.*)', redirect: '/' }
  ]
})

// 3. Guardia de navegación actualizado con chequeo de rol
router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('userToken');

  if (to.meta.requiresAuth && !isAuthenticated) {
    // Si requiere auth y no está logueado, va al login
    next('/login');
  } else if ((to.name === 'Login' || to.name === 'ForgotPassword' || to.name === 'ResetPassword') && isAuthenticated) {
    // Si está logueado e intenta ir al login, recuperación o reset, va al dashboard
    next('/');
  } else if (to.meta.requiresRole) {
    // Si la ruta requiere un rol, decodificar el token para obtener el rol
    const token = localStorage.getItem('userToken');
    let userRole = authStore.user?.role;
    
    // Si no hay usuario en el store, intentar decodificar el token
    if (!userRole && token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        userRole = payload.role;
        // Restaurar el usuario en el store
        if (!authStore.user) {
          authStore.user = {
            email: payload.sub,
            role: payload.role,
            full_name: payload.full_name
          };
        }
      } catch (e) {
        console.error('Error decodificando token:', e);
      }
    }
    
    if (userRole === to.meta.requiresRole) {
      // ...y el usuario tiene ese rol, le permitimos pasar
      next();
    } else {
      // ...si no tiene el rol, le negamos el acceso y lo enviamos al inicio
      alert('No tienes permisos para acceder a esta página.');
      next('/');
    }
  } else {
    next();
  }
});

export default router
