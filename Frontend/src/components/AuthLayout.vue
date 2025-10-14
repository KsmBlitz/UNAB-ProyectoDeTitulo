<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
}>();
</script>

<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="logo">
        <i class="pi pi-shield" style="font-size: 3rem; color: #3498db;"></i>
        <h2>{{ title }}</h2>
        <p v-if="subtitle">{{ subtitle }}</p>
      </div>
      <slot />
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f4f6f9;
  padding: 1rem;
}

.auth-card {
  background-color: #fff;
  padding: 2.5rem 3rem;
  border-radius: 12px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 480px;
  text-align: center;
}

.logo { margin-bottom: 2rem; }
.logo h2 { margin: 0.5rem 0; color: #2c3e50; }
.logo p { color: #6c757d; margin: 0; }
</style>
