// ============================================================================
// PARCHE PARA src/services/api.js
// Sustituye ÚNICAMENTE los dos bloques marcados. El resto del archivo
// (cyclesAPI, coursesAPI, packagesAPI, teachersAPI, schedulesAPI, adminAPI,
// notificationsAPI) se mantiene tal cual.
// ============================================================================

// ─── BLOQUE 1: sustituye la función `request` completa ───────────────────────
//
// Correcciones:
//   S-01  `const data = await response.json()` se ejecutaba SIEMPRE. Ante un
//         204 sin cuerpo, un 502 del proxy o una página de error HTML, se
//         lanzaba un SyntaxError y el usuario veía «Unexpected token < in JSON
//         at position 0» en lugar de un mensaje comprensible.
//   S-02  Un 401 por token expirado dejaba al usuario en la pantalla actual
//         acumulando errores crípticos, sin devolverlo al inicio de sesión.
//   S-03  El `detail` de FastAPI puede ser un array de objetos cuando falla la
//         validación de Pydantic. Al asignarlo a `new Error(...)` se
//         renderizaba «[object Object]».
//   S-04  No había tiempo de espera: con el backend caído, la petición quedaba
//         colgada indefinidamente y los botones no se desbloqueaban nunca.

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:4000/api";
const TIEMPO_MAXIMO_MS = 20000;

function extraerMensaje(data, response) {
  if (!data) {
    return response.status >= 500
      ? "El servidor no está disponible. Inténtalo de nuevo en unos minutos."
      : "No se pudo completar la operación.";
  }

  const detalle = data.detail ?? data.error ?? data.message;

  // S-03: Pydantic devuelve [{loc, msg, type}, ...]
  if (Array.isArray(detalle)) {
    return detalle
      .map((d) => (typeof d === "string" ? d : d.msg || JSON.stringify(d)))
      .join(". ");
  }
  if (detalle && typeof detalle === "object") {
    return detalle.msg || JSON.stringify(detalle);
  }
  return detalle || "No se pudo completar la operación.";
}

async function request(endpoint, options = {}) {
  const token = localStorage.getItem("token");

  const config = {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  };

  if (options.body instanceof FormData) {
    delete config.headers["Content-Type"];
  }

  // S-04: tiempo de espera
  const controlador = new AbortController();
  const temporizador = setTimeout(() => controlador.abort(), TIEMPO_MAXIMO_MS);
  config.signal = controlador.signal;

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  } catch (err) {
    clearTimeout(temporizador);
    if (err.name === "AbortError") {
      throw new Error("El servidor tardó demasiado en responder. Vuelve a intentarlo.");
    }
    throw new Error("No hay conexión con el servidor. Revisa tu red e inténtalo de nuevo.");
  }
  clearTimeout(temporizador);

  // S-01: el cuerpo se interpreta con tolerancia
  let data = null;
  if (response.status !== 204) {
    const texto = await response.text();
    if (texto) {
      try {
        data = JSON.parse(texto);
      } catch {
        data = null; // respuesta no-JSON (HTML de error, proxy, etc.)
      }
    }
  }

  // S-02: sesión caducada -> vuelta al inicio de sesión
  if (response.status === 401) {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    if (!window.location.pathname.startsWith("/login")) {
      window.location.replace("/login?expirada=1");
    }
    throw new Error("Tu sesión ha expirado. Inicia sesión nuevamente.");
  }

  if (!response.ok) {
    throw new Error(extraerMensaje(data, response));
  }

  // El backend antiguo devolvía errores con 200 y un campo `error`
  if (data && data.error) {
    throw new Error(data.error);
  }

  return data;
}

// ─── BLOQUE 2: sustituye el objeto `enrollmentsAPI` completo ────────────────
//
// Correcciones:
//   S-05  `updateStatus` no permitía enviar el motivo, obligatorio en el
//         backend corregido al rechazar o cancelar (RF21).
//   S-06  No existía método para DELETE /enrollments/{id}: el endpoint estaba
//         publicado en el backend y ningún componente podía llamarlo.
//   S-07  No existía método para el historial de cambios (RNF15).
//   S-08  `cancel` no admitía motivo.

export const enrollmentsAPI = {
  getAll: (studentId = null) =>
    request(studentId ? `/enrollments?student_id=${studentId}` : "/enrollments"),

  getAllAdmin: () => request("/enrollments/admin"),

  create: (items) =>
    request("/enrollments", {
      method: "POST",
      body: JSON.stringify({ items }),
    }),

  updateStatus: (enrollmentId, status, reason = null) =>
    request("/enrollments/status", {
      method: "PUT",
      body: JSON.stringify({ enrollment_id: enrollmentId, status, reason }),
    }),

  cancel: (enrollmentId, reason = null) =>
    request("/enrollments/cancel", {
      method: "POST",
      body: JSON.stringify({ enrollment_id: enrollmentId, reason }),
    }),

  remove: (enrollmentId) =>
    request(`/enrollments/${enrollmentId}`, { method: "DELETE" }),

  getHistory: (enrollmentId) => request(`/enrollments/${enrollmentId}/history`),

  getByOffering: (type, id, status = "aceptado") => {
    const params = new URLSearchParams({ type, id, status });
    return request(`/enrollments/by-offering?${params.toString()}`);
  },
};