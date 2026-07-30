// Configuración global de la API
export const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:4000/api";

// Para usar en componentes que hacen fetch directo
export const getApiUrl = (endpoint) => {
  const base = API_BASE_URL.replace("/api", ""); // Remover /api si existe
  return `${base}${endpoint}`;
};
