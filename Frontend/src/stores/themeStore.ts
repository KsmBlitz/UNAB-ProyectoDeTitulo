import { reactive } from 'vue';

interface ThemeState {
  isDark: boolean;
}


const getInitialTheme = () => {
  const stored = localStorage.getItem('theme');
  if (stored === 'dark') return true;
  if (stored === 'light') return false;
  // Si no hay preferencia, usar claro por defecto
  return false;
};

const state = reactive<ThemeState>({
  isDark: getInitialTheme()
});

export const themeStore = {
  get isDark() {
    return state.isDark;
  },

  toggleTheme() {
    state.isDark = !state.isDark;
    localStorage.setItem('theme', state.isDark ? 'dark' : 'light');
    this.applyTheme();
  },

  applyTheme() {
    // Limpiar solo clases de gradiente y forzar 'dark' minúscula
    document.body.classList.remove(
      'bg-gradient-to-br', 'from-white', 'via-blue-100', 'to-blue-200',
      'from-slate-900', 'via-slate-800', 'to-slate-900', 'dark', 'Dark', 'bg-slate-900', 'bg-white'
    );
    document.documentElement.classList.remove('dark', 'Dark');
    if (state.isDark) {
      document.documentElement.classList.add('dark');
      document.body.classList.add('bg-gradient-to-br', 'from-slate-900', 'via-slate-800', 'to-slate-900');
    } else {
      document.body.classList.add('bg-gradient-to-br', 'from-white', 'via-blue-100', 'to-blue-200');
    }
  },

  initTheme() {
    this.applyTheme();
  }
};
