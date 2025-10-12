import { reactive } from 'vue';

interface User {
  email: string;
  role: string;
  full_name?: string; // Hacer opcional por si no está disponible inicialmente
}

// Exportamos un objeto reactivo que contendrá los datos del usuario
export const authStore = reactive<{
  user: User | null;
}>({
  user: null
});
