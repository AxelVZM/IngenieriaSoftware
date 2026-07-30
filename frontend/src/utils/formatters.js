// src/utils/formatters.js
// Formateadores de presentación compartidos.

/**
 * Formatea una fecha SIN hora (columnas DATE de PostgreSQL, que la API
 * serializa como "AAAA-MM-DD") al formato local dd/mm/aaaa.
 *
 * No usar `new Date("2026-03-01").toLocaleDateString()` para estos valores: el
 * estándar obliga a interpretar la forma corta como UTC, así que al imprimirla
 * en una zona negativa (Perú es UTC-5) se muestra el DÍA ANTERIOR. Además,
 * `toLocaleDateString()` sin locale adopta el del navegador y puede rendir
 * "3/1/2026" (formato de EE. UU.) en una interfaz en español.
 *
 * Por eso se formatea la cadena directamente, sin construir un Date.
 *
 * @param {string|null|undefined} value fecha ISO ("2026-03-01" o con hora)
 * @param {string} fallback texto a mostrar si no hay fecha
 * @returns {string} "01/03/2026"
 */
export function formatDateOnly(value, fallback = '-') {
  if (!value) return fallback;

  // Acepta "2026-03-01" y también "2026-03-01T00:00:00" quedándose con la fecha.
  const [fecha] = String(value).split('T');
  const [anio, mes, dia] = fecha.split('-');

  if (!anio || !mes || !dia) return fallback;

  return `${dia}/${mes}/${anio}`;
}

/**
 * Formatea un monto en soles con dos decimales.
 *
 * @param {number|string|null|undefined} value
 * @returns {string} "S/. 150.00"
 */
export function formatCurrency(value) {
  return `S/. ${parseFloat(value || 0).toFixed(2)}`;
}
