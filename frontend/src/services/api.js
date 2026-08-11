const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:4000/api";
const TIEMPO_MAXIMO_MS = 60000;

// Códigos que significan "la sesión ya no sirve" -> cerrar sesión local
const SESSION_ERROR_CODES = [
  "TOKEN_EXPIRED",
  "TOKEN_INVALID",
  "TOKEN_MISSING",
  "USER_NOT_FOUND",
];

/**
 * Error enriquecido: además del mensaje trae el código del backend
 * y el status HTTP, para que los componentes puedan reaccionar.
 */
export class ApiError extends Error {
  constructor(message, { code = "UNKNOWN_ERROR", status = 0, fields = [] } = {}) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.fields = fields;
  }
}

function clearSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

// Pydantic emite sus mensajes propios en inglés; se traducen los que pueden
// aparecer en los formularios. Los de nuestros validadores ya vienen en español.
// La traducción puede ser una función cuando necesita un dato del mensaje
// original, como la cantidad mínima de caracteres.
const MENSAJES_PYDANTIC = [
  [/^Field required$/i, 'Campo obligatorio'],
  [/^Input should be a valid number/i, 'Debe ser un número válido'],
  [/^Input should be a valid integer/i, 'Debe ser un número entero válido'],
  [/^Input should be a valid date/i, 'Debe ser una fecha válida (AAAA-MM-DD)'],
  [/^Input should be a valid string/i, 'Debe ser un texto válido'],
  [/^Input should be a valid boolean/i, 'Debe ser verdadero o falso'],
  [/^Input should be a valid list/i, 'Debe ser una lista'],
  [/^String should have at least (\d+) characters?$/i,
    (m) => `Debe tener al menos ${m[1]} caracteres`],
  [/^String should have at most (\d+) characters?$/i,
    (m) => `Debe tener como máximo ${m[1]} caracteres`],
  [/^List should have at least (\d+) items?/i,
    (m) => `Debe tener al menos ${m[1]} elemento(s)`],
];

// Nombres de campo legibles; si un campo no está aquí se muestra tal cual.
const ETIQUETAS_CAMPO = {
  name: 'Nombre',
  description: 'Descripción',
  base_price: 'Precio base',
  start_date: 'Fecha de inicio',
  end_date: 'Fecha de fin',
  duration_months: 'Duración en meses',
  status: 'Estado',
  group_label: 'Grupo',
  capacity: 'Capacidad',
  teacher_id: 'Docente',
  price_override: 'Precio de la oferta',
  course_id: 'Curso',
  cycle_id: 'Ciclo',
  // Horarios: se editan desde la ficha de la oferta, así que sus errores
  // aparecen en los mismos formularios.
  course_offering_id: 'Oferta',
  day_of_week: 'Día de la semana',
  start_time: 'Hora de inicio',
  end_time: 'Hora de fin',
  classroom: 'Aula',
  // Campos de los demás módulos. Sin ellos el usuario vería el nombre de la
  // variable, porque el backend identifica los campos así en TODOS los 422.
  dni: 'DNI',
  email: 'Correo electrónico',
  password: 'Contraseña',
  username: 'Usuario',
  role: 'Rol',
  first_name: 'Nombres',
  last_name: 'Apellidos',
  phone: 'Teléfono',
  parent_name: 'Nombre del apoderado',
  parent_phone: 'Teléfono del apoderado',
  student_id: 'Estudiante',
  schedule_id: 'Horario',
  date: 'Fecha',
  enrollment_id: 'Matrícula',
  installment_id: 'Cuota',
  package_id: 'Paquete',
  total_amount: 'Monto total',
  paid_amount: 'Monto pagado',
  num_installments: 'Número de cuotas',
  first_due_date: 'Primer vencimiento',
  related_id: 'Registro asociado',
  course_ids: 'Cursos',
  course_offering_ids: 'Ofertas',
  items: 'Cursos a matricular',
};

/** Etiqueta legible de un campo; acepta rutas anidadas como "body.base_price". */
function etiquetaDeCampo(campo) {
  const hoja = String(campo ?? '').split('.').filter(Boolean).pop();
  return ETIQUETAS_CAMPO[hoja] ?? hoja ?? '';
}

/** Minúsculas y sin tildes, para comparar textos sin depender del acento. */
function normalizar(texto) {
  return String(texto).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

/**
 * Antepone al mensaje la etiqueta del campo, salvo cuando el propio mensaje ya
 * lo nombra: nuestros validadores escriben frases completas ("El precio base
 * debe ser mayor que 0") y anteponerles la etiqueta las dejaría repetidas.
 *
 * La decisión se toma mirando el texto, NO si el mensaje venía traducido. Con
 * el criterio anterior los validadores de otros módulos —que redactan mensajes
 * sin nombrar el campo, como "Solo puede contener letras…"— se quedaban sin
 * prefijo y no había forma de saber a qué campo se referían.
 */
function conEtiqueta(campo, texto) {
  const etiqueta = etiquetaDeCampo(campo);
  if (!etiqueta) return texto;
  if (normalizar(texto).includes(normalizar(etiqueta))) return texto;
  return `${etiqueta}: ${texto}`;
}

/** Traduce un mensaje de Pydantic; si no lo reconoce lo devuelve tal cual. */
function traducirMensaje(msg) {
  for (const [patron, traduccion] of MENSAJES_PYDANTIC) {
    const coincidencia = patron.exec(msg);
    if (coincidencia) {
      return typeof traduccion === 'function' ? traduccion(coincidencia) : traduccion;
    }
  }
  return msg;
}

/**
 * Convierte el cuerpo de error de la API en un texto legible.
 *
 * En un 422 de validación, FastAPI devuelve `detail` como un ARREGLO de objetos
 * ({loc, msg, type}, ...). Pasar eso a `new Error(...)` producía el mensaje
 * "[object Object]". Aquí se aplanan los mensajes y se les antepone el campo.
 */
function extractErrorMessage(data, response) {
  if (!data) {
    return response?.status >= 500
      ? "El servidor no está disponible. Inténtalo de nuevo en unos minutos."
      : "No se pudo completar la operación.";
  }

  const detail = data?.detail ?? data?.message ?? data?.error;

  if (typeof detail === 'string') return detail;

  if (Array.isArray(detail)) {
    const mensajes = detail
      .map((item) => {
        if (typeof item === 'string') return item;

        const crudo = String(item?.msg ?? '').replace(/^Value error,\s*/i, '');
        if (!crudo) return '';

        const campo = Array.isArray(item?.loc)
          ? item.loc.filter((p) => p !== 'body' && typeof p === 'string').pop()
          : null;

        return conEtiqueta(campo, traducirMensaje(crudo));
      })
      .filter(Boolean);

    if (mensajes.length) return mensajes.join(' · ');
  }

  if (detail && typeof detail === 'object') {
    return detail.msg || detail.message || JSON.stringify(detail);
  }

  return 'No se pudo completar la operación.';
}

/**
 * Arma el texto de un 422 a partir de los errores ya separados en campo y
 * mensaje que envía el manejador global del backend.
 *
 * El backend nombra los campos con su identificador interno (`base_price`,
 * `duration_months`, `day_of_week`). Mostrárselos al usuario es un defecto de
 * usabilidad: aquí se cambian por la etiqueta del formulario y se traducen los
 * mensajes que Pydantic emite en inglés.
 */
function formatearErroresDeValidacion(errores) {
  if (!Array.isArray(errores) || !errores.length) return null;

  const mensajes = errores
    .map((item) => {
      const crudo = String(item?.message ?? '').replace(/^Value error,\s*/i, '');
      if (!crudo) return '';
      return conEtiqueta(item?.field, traducirMensaje(crudo));
    })
    .filter(Boolean);

  return mensajes.length ? mensajes.join(' · ') : null;
}

/**
 * Extrae el mensaje del cuerpo de error, soportando:
 *  - Formato nuevo: { detail: { code, message, fields, errors } }
 *  - Formato antiguo: { detail: "texto" } o { error: "texto" }
 */
function parseErrorBody(body, status, response) {
  const detail = body?.detail;

  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    // Los 422 traen `errors` con el campo aparte: se rearma el texto para no
    // enseñar el nombre de la variable. Si no viene (backend antiguo), se cae
    // al `message` ya formateado.
    const mensaje =
      formatearErroresDeValidacion(detail.errors) ||
      detail.message ||
      "Error en la petición";

    return new ApiError(mensaje, {
      code: detail.code || "HTTP_ERROR",
      status,
      fields: detail.fields || [],
    });
  }

  const message = extractErrorMessage(body, response);
  return new ApiError(message, { code: "HTTP_ERROR", status });
}

// Función helper para hacer peticiones
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

  const timeoutMs = options.timeout || TIEMPO_MAXIMO_MS;
  const controlador = new AbortController();
  const temporizador = setTimeout(() => controlador.abort(), timeoutMs);
  config.signal = controlador.signal;

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  } catch (err) {
    clearTimeout(temporizador);
    if (err.name === "AbortError") {
      throw new ApiError("El servidor tardó demasiado en responder. Vuelve a intentarlo.", {
        code: "TIMEOUT_ERROR",
      });
    }
    console.error("Network Error:", err);
    throw new ApiError("No se pudo conectar con el servidor. Revisa tu conexión.", {
      code: "NETWORK_ERROR",
    });
  }
  clearTimeout(temporizador);

  // 204 No Content u otras respuestas sin cuerpo
  if (response.status === 204) return null;

  let body = null;
  const raw = await response.text();
  if (raw) {
    try {
      body = JSON.parse(raw);
    } catch {
      body = null;
    }
  }

  if (!response.ok) {
    if (body === null) {
      throw new ApiError(
        `Error del servidor (${response.status}). Intenta más tarde.`,
        { code: "SERVER_ERROR", status: response.status }
      );
    }

    const error = parseErrorBody(body, response.status, response);

    // Sesión inválida o expirada: limpiar y mandar al login
    if (response.status === 401 && (SESSION_ERROR_CODES.includes(error.code) || error.code === "HTTP_ERROR")) {
      clearSession();
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login?expirada=1";
      }
    }

    console.error("API Error:", error.code, error.message);
    throw error;
  }

  // Red de seguridad para endpoints con formato antiguo que retornan 200 con { error: "..." }
  if (body && typeof body === "object" && typeof body.error === "string") {
    const legacy = new ApiError(body.error, {
      code: "LEGACY_ERROR",
      status: response.status,
    });
    console.error("API Error (formato antiguo):", body.error);
    throw legacy;
  }

  return body;
}

// API de autenticación
export const authAPI = {
  login: (dni, password) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ dni, password }),
    }),
  register: (data) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getMe: () => request("/auth/me"),
};

// API de estudiantes
export const studentsAPI = {
  register: (data) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getAll: () => request("/students"),
  getOne: (id) => request(`/students/${id}`),
  update: (id, data) =>
    request(`/students/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id) =>
    request(`/students/${id}`, {
      method: "DELETE",
    }),
};

// API de ciclos
export const cyclesAPI = {
  getAll: () => request("/cycles"),
  getActive: () => request("/cycles/active"),
  getOne: (id) => request(`/cycles/${id}`),
  create: (data) =>
    request("/cycles", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id, data) =>
    request(`/cycles/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id) =>
    request(`/cycles/${id}`, {
      method: "DELETE",
    }),
};

// API de cursos
export const coursesAPI = {
  getAll: () => request("/courses"),
  getOne: (id) => request(`/courses/${id}`),
  create: (data) =>
    request("/courses", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id, data) =>
    request(`/courses/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id) =>
    request(`/courses/${id}`, {
      method: "DELETE",
    }),
  getOfferings: () => request("/courses/offerings"),
  createOffering: (data) =>
    request("/courses/offerings", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateOffering: (id, data) =>
    request(`/courses/offerings/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteOffering: (id) =>
    request(`/courses/offerings/${id}`, {
      method: "DELETE",
    }),
};

// API de paquetes
export const packagesAPI = {
  getAll: () => request("/packages"),
  getOne: (id) => request(`/packages/${id}`),
  create: (data) =>
    request("/packages", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id, data) =>
    request(`/packages/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id) =>
    request(`/packages/${id}`, {
      method: "DELETE",
    }),
  addCourse: (packageId, courseId) =>
    request(`/packages/${packageId}/courses`, {
      method: "POST",
      body: JSON.stringify({ course_id: courseId }),
    }),
  removeCourse: (packageId, courseId) =>
    request(`/packages/${packageId}/courses/${courseId}`, {
      method: "DELETE",
    }),
  getOfferings: () => request("/packages/offerings"),
  createOffering: (data) =>
    request("/packages/offerings", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateOffering: (id, data) =>
    request(`/packages/offerings/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteOffering: (id) =>
    request(`/packages/offerings/${id}`, {
      method: "DELETE",
    }),
  // Mapping: package_offering -> course_offerings
  addOfferingCourse: (packageOfferingId, courseOfferingId) =>
    request(`/packages/offerings/${packageOfferingId}/courses`, {
      method: "POST",
      body: JSON.stringify({ course_offering_id: courseOfferingId }),
    }),
  removeOfferingCourse: (packageOfferingId, courseOfferingId) =>
    request(
      `/packages/offerings/${packageOfferingId}/courses/${courseOfferingId}`,
      {
        method: "DELETE",
      }
    ),
  getOfferingCourses: (packageOfferingId) =>
    request(`/packages/offerings/${packageOfferingId}/courses`),
};

// API de docentes
export const teachersAPI = {
  getAll: () => request("/teachers"),
  getOne: (id) => request(`/teachers/${id}`),
  create: (data) =>
    request("/teachers", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id, data) =>
    request(`/teachers/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id) =>
    request(`/teachers/${id}`, {
      method: "DELETE",
    }),
  resetPassword: (id) =>
    request(`/teachers/${id}/reset-password`, {
      method: "POST",
    }),
  getStudents: (id) => request(`/teachers/${id}/students`),
  getStudentsByCourse: (teacherId, courseOfferingId) =>
    request(`/teachers/${teacherId}/students/course/${courseOfferingId}`),
  markAttendance: (teacherId, data) =>
    request(`/teachers/${teacherId}/attendance`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getAttendance: (teacherId, scheduleId, date) =>
    request(`/teachers/${teacherId}/attendance/${scheduleId}/${date}`),
};

// API de matrículas
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

// API de pagos
export const paymentsAPI = {
  getAll: (status = null) => {
    const url = status ? `/payments?status=${status}` : "/payments";
    return request(url);
  },
  uploadVoucher: (installmentId, file) => {
    const formData = new FormData();
    formData.append("voucher", file);
    formData.append("installment_id", installmentId);
    return request("/payments/upload", {
      method: "POST",
      body: formData,
    });
  },
  approveInstallment: (installmentId) =>
    request("/payments/approve", {
      method: "POST",
      body: JSON.stringify({ installment_id: installmentId }),
    }),
  rejectInstallment: (installmentId, reason = null) =>
    request("/payments/reject", {
      method: "POST",
      body: JSON.stringify({ installment_id: installmentId, reason }),
    }),
};

// API de horarios
export const schedulesAPI = {
  getAll: () => request("/schedules"),
  getByOffering: (courseOfferingId) =>
    request(`/schedules/offering/${courseOfferingId}`),
  getByCourseOffering: (courseOfferingId) =>
    request(`/schedules/offering/${courseOfferingId}`),
  getByPackageOffering: (packageOfferingId) =>
    request(`/schedules/package-offering/${packageOfferingId}`),
  create: (data) =>
    request("/schedules", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id, data) =>
    request(`/schedules/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  delete: (id) =>
    request(`/schedules/${id}`, {
      method: "DELETE",
    }),
};

// API de admin
export const adminAPI = {
  getDashboard: () => request("/admin/dashboard"),
  getAnalytics: (cycleId = null, studentId = null) => {
    const params = new URLSearchParams();
    if (cycleId) params.append("cycle_id", cycleId);
    if (studentId) params.append("student_id", studentId);
    const url = `/admin/analytics${
      params.toString() ? "?" + params.toString() : ""
    }`;
    return request(url);
  },
  getNotifications: (studentId = null, type = null, limit = 50) => {
    const params = new URLSearchParams();
    if (studentId) params.append("student_id", studentId);
    if (type) params.append("type", type);
    params.append("limit", limit);
    return request(`/admin/notifications?${params.toString()}`);
  },
  getAttendanceNotifications: (cycleId, date, group) => {
    const params = new URLSearchParams({
      cycle_id: cycleId,
      date: date,
      group: group,
    });
    return request(`/admin/attendance-notifications?${params.toString()}`);
  },
  sendAttendanceNotifications: (cycleId, date, groupLabel) =>
    request("/admin/send-attendance-notifications", {
      method: "POST",
      body: JSON.stringify({
        cycle_id: cycleId,
        date: date,
        group_label: groupLabel,
      }),
    }),
};

// API de notificaciones
export const notificationsAPI = {
  initWhatsApp: () =>
    request("/notifications/whatsapp/init", { method: "POST", timeout: 60000 }),
  verifyWhatsApp: () =>
    request("/notifications/whatsapp/verify", { method: "POST", timeout: 30000 }),
  testWhatsApp: (phone = "969728039") =>
    request(`/notifications/whatsapp/test?phone=${phone}`, { method: "POST", timeout: 45000 }),
  closeWhatsApp: () =>
    request("/notifications/whatsapp/close", { method: "POST" }),

  getPaymentsRejected: () => request("/notifications/payments/rejected"),
  getPaymentsAccepted: () => request("/notifications/payments/accepted"),
  sendPaymentNotifications: (type, payments) =>
    request("/notifications/payments/send", {
      method: "POST",
      body: JSON.stringify({ type, payments }),
      timeout: 120000,
    }),
};

export default {
  authAPI,
  studentsAPI,
  cyclesAPI,
  coursesAPI,
  packagesAPI,
  teachersAPI,
  enrollmentsAPI,
  paymentsAPI,
  schedulesAPI,
  adminAPI,
  notificationsAPI,
};