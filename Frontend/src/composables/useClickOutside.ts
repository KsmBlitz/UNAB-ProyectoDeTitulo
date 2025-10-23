import { onMounted, onUnmounted, type Ref } from 'vue';

/**
 * Composable para manejar clics fuera de un elemento
 * Útil para cerrar modales, dropdowns, etc.
 */
export function useClickOutside(elementRef: Ref<HTMLElement | null>, callback: () => void) {
  const handleClickOutside = (event: MouseEvent) => {
    if (elementRef.value && !elementRef.value.contains(event.target as Node)) {
      callback();
    }
  };

  onMounted(() => {
    document.addEventListener('click', handleClickOutside);
  });

  onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside);
  });

  return { handleClickOutside };
}
